"""Execute two alternate browser reference plans and oracle mutations on real OpsConsole."""

import argparse
import copy
import json
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from afterclick.completion_v12.evidence import sha
from afterclick.completion_v12.ops_oracle import evaluate
from afterclick.completion_v12.opsconsole import OpsConsole


def reference(page, origin, reverse=False):
    page.goto(origin)
    expect(page.get_by_role("status")).to_have_text("Ready")
    actions = []

    def click(command):
        # A concurrent collaborator may win between refresh and submission. A rejected
        # stale command is not a commit; re-read public state and explicitly try again.
        for attempt in range(3):
            page.evaluate("refresh()")
            page.get_by_role("button", name=command, exact=True).click()
            page.wait_for_function("!busy")
            status = page.get_by_role("status").inner_text()
            actions.append(
                dict(
                    command=command,
                    wall=time.time(),
                    attempt=attempt,
                    feedback=status,
                    public=page.evaluate("state"),
                )
            )
            if command + ": command committed" in status:
                return
            if "Refresh after collaborator or concurrent command" not in status:
                raise ValueError("Reference command failed: " + status)
        raise ValueError("Reference exhausted its bounded concurrent-edit reconciliation")

    for command in (
        ["Reserve Cache", "Reserve CPU"] if reverse else ["Reserve CPU", "Reserve Cache"]
    ):
        click(command)
    click("Reserve Spare")
    click("Request approvals")
    expect(page.locator("#approvals")).not_to_contain_text('"pending"')
    expect(page.locator("#approvals")).not_to_contain_text('"unrequested"')
    expect(page.locator("#change")).to_contain_text("On-call: preserve audit scope")
    click("Enter maintenance")
    for command in (
        ["Dispatch Cache", "Dispatch CPU"] if reverse else ["Dispatch CPU", "Dispatch Cache"]
    ):
        click(command)
    expect(page.locator("#orders")).not_to_contain_text('"queued"')
    expect(page.locator("#orders")).not_to_contain_text('"admitted"')
    click("Verify receipts")
    click("Release Spare")
    click("Post handoff")
    click("Restore normal")
    click("Close change")
    return actions


def mutations(snapshot):
    results = []
    for name in ["CPU", "Cache"]:
        bad = copy.deepcopy(snapshot)
        bad["oc_receipts"] = [r for r in bad["oc_receipts"] if r["id"] != name]
        results.append(dict(mutation="omit_receipt_" + name, result=evaluate(bad)))
    for field, value in [("mode", "maintenance"), ("status", "open"), ("notes", [])]:
        bad = copy.deepcopy(snapshot)
        bad["oc_change"][0][field] = value
        results.append(dict(mutation="omit_" + field, result=evaluate(bad)))
    bad = copy.deepcopy(snapshot)
    bad["oc_receipts"].append(dict(bad["oc_receipts"][0], id="Spare"))
    results.append(dict(mutation="extra_irreversible_consumption", result=evaluate(bad)))
    bad = copy.deepcopy(snapshot)
    bad["oc_events"] = [e for e in bad["oc_events"] if e["kind"] != "approval.granted"]
    results.append(dict(mutation="missing_approval_history", result=evaluate(bad)))
    for kind in ["command.Verify receipts", "command.Restore normal", "command.Close change"]:
        bad = copy.deepcopy(snapshot)
        bad["oc_events"] = [e for e in bad["oc_events"] if e["kind"] != kind]
        results.append(dict(mutation="missing_" + kind, result=evaluate(bad)))
    for kind, wall in [
        ("approval.granted", "9999999999"),
        ("command.Restore normal", "0"),
        ("command.Post handoff", "0"),
    ]:
        bad = copy.deepcopy(snapshot)
        for event in bad["oc_events"]:
            if event["kind"] == kind:
                event["wall"] = wall
        results.append(dict(mutation="wrong_order_" + kind, result=evaluate(bad)))
    bad = copy.deepcopy(snapshot)
    next(h for h in bad["oc_holds"] if h["id"] == "Spare")["status"] = "reserved"
    results.append(dict(mutation="unreleased_reservation", result=evaluate(bad)))
    for result in results:
        if result["result"]["joint_safe_completion"] is not False:
            raise ValueError("Oracle accepts illegal or incomplete task mutation")
    return results


def execute(output):
    output.mkdir(parents=True, exist_ok=False)
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for reverse in (False, True):
                world = OpsConsole()
                world.initialize()
                directory = output / ("alternate" if reverse else "primary")
                directory.mkdir()
                try:
                    with world.serve() as origin:
                        page = browser.new_page()
                        actions = reference(page, origin, reverse)
                        snapshot = world.snapshot()
                        result = evaluate(snapshot)
                        (directory / "actions.json").write_text(
                            json.dumps(actions, indent=2) + "\n"
                        )
                        (directory / "final.json").write_text(json.dumps(snapshot, indent=2) + "\n")
                        (directory / "oracle.json").write_text(json.dumps(result, indent=2) + "\n")
                        mutated = mutations(snapshot)
                        (directory / "mutation-tests.json").write_text(
                            json.dumps(mutated, indent=2) + "\n"
                        )
                        page.screenshot(path=str(directory / "final.png"), full_page=True)
                        if not result["joint_safe_completion"] or world.errors:
                            raise ValueError("OpsConsole reference completion failed")
                        results.append(
                            dict(
                                plan="alternate" if reverse else "primary",
                                oracle=result,
                                mutations_rejected=len(mutated),
                                substantive_actions=len(actions),
                                worker_errors=world.errors,
                            )
                        )
                        page.close()
                finally:
                    # Preserve failed partial worlds too; drop only this experiment's schema.
                    (directory / "last-snapshot.json").write_text(
                        json.dumps(world.snapshot(), indent=2) + "\n"
                    )
                    world.db.drop_experiment()
        finally:
            browser.close()
    summary = dict(
        status="QUALIFIED_SINGLE_DEV_WORKFLOW_NOT_FULL_BENCHMARK",
        plans=results,
        source_hashes={
            str(p): sha(p)
            for p in [
                Path(__file__),
                Path("afterclick/completion_v12/opsconsole.py"),
                Path("afterclick/completion_v12/ops_oracle.py"),
                Path("afterclick/completion_v12/opsconsole.html"),
            ]
        },
        model_calls=0,
        new_paid_compute_usd=0,
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    execute(p.parse_args().output)
