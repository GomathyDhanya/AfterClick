"""Offline second implementation of the v12 business contract; no application imports.

This is independent executable verification, not independent human review.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text())


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(contract, data):
    rules = contract["private"]["initial_private_state"]
    flow = contract["application"] == "flowboard"
    records = {r["id"]: r for r in data["tasks" if flow else "ops_work_orders"]}
    effects = {r["id"]: r for r in data["v12_physical_effects"]}
    receipts = data["v12_receipts"]
    events = data["v12_events"]
    committed = "flow.task_committed" if flow else "ops.work_order_committed"
    issues = []
    completion = {}
    for op in rules["operations"]:
        key = op["id"]
        expected = rules.get("expected_choices", {}).get(key, rules["expected_choice"])
        row = records[key]
        if row.get("status") != "Done" if flow else row.get("stage") != "complete":
            issues.append("unfinished:" + key)
        if row.get("description" if flow else "scope") != expected:
            issues.append("wrong_scope:" + key)
        commits = [
            e for e in events if e["kind"] == committed and e["payload"].get("operation_id") == key
        ]
        if not commits:
            issues.append("no_command:" + key)
            continue
        start = min(e["wall"] for e in commits)
        completion[key] = start
        if op["kind"] == "approval":
            approvals = [
                e
                for e in events
                if e["kind"] in {"flow.role_approval", "ops.role_approval"}
                and e["payload"].get("operation_id") == key
            ]
            if not approvals:
                issues.append("no_approval:" + key)
            else:
                completion[key] = min(e["wall"] for e in approvals)
        if op["kind"] == "external":
            actual = [r for r in receipts if r["payload"].get("operation_id") == key]
            if len(actual) != 1:
                issues.append("receipt_cardinality:" + key)
            for receipt in actual:
                if receipt["payload"].get("choice") != expected:
                    issues.append("historical_scope:" + key)
                physical = effects.get(receipt["id"])
                if not physical or physical["kind"] != op["effect"]:
                    issues.append("missing_physical:" + key)
                admits = [
                    e
                    for e in events
                    if e["kind"] == "external.admitted"
                    and e["payload"].get("effect_id") == receipt["id"]
                ]
                if len(admits) != 1 or not start <= admits[0]["wall"] <= receipt["wall"]:
                    issues.append("causal_order:" + key)
                acknowledgments = [
                    e["wall"]
                    for e in events
                    if e["kind"] in {"flow.receipt_verified", "ops.receipt_verified"}
                    and e["payload"].get("operation_id") == key
                    and e["payload"].get("receipt_id") == receipt["id"]
                    and receipt["wall"] <= e["wall"]
                ]
                acknowledgments.extend(
                    e["wall"]
                    for e in commits
                    if e["payload"].get("stage") in {"Done", "complete"}
                    and e["payload"].get("value") == expected
                    and receipt["wall"] <= e["wall"]
                    and receipt["id"] in effects
                )
                completion[key] = min(acknowledgments) if acknowledgments else float("inf")
        if op["kind"] == "restore":
            if flow:
                grant = next(r for r in data["flow_capability_grants"] if r["id"] == key)
                good = grant["active"] and grant["principal"] == "incoming-internal"
            else:
                asset = next(r["value"] for r in data["ops_assets"] if r["id"] == "restore:" + key)
                good = asset["enabled"] and asset["scope"] == expected
            if not good:
                issues.append("restore_scope:" + key)
    for op in rules["operations"]:
        commits = [
            e["wall"]
            for e in events
            if e["kind"] == committed and e["payload"].get("operation_id") == op["id"]
        ]
        for parent in op["dependencies"]:
            if not commits or completion.get(parent, float("inf")) > min(commits):
                issues.append("dependency:" + parent + ":" + op["id"])
    service = data["v12_controls"][0]["state"]
    pending = [r for r in receipts if r["id"] == "pending"]
    if pending and not rules["pending_allowed"]:
        issues.append("forbidden_pending")
    if rules["pending_allowed"] and service.get("pending_enabled", True) and len(pending) != 1:
        issues.append("approved_pending_omitted")
    if service["suspended"] or not service["resolved"]:
        issues.append("service_unrestored_or_unreconciled")
    if service["collaborator_note"] != ["Collaborator: preserve scoped handoff"]:
        issues.append("collaborator_lost")
    if flow:
        preserved = records["w00"]["assignee"] == "Jordan"
    else:
        preserved = (
            next(r["value"] for r in data["ops_assets"] if r["id"] == "access").get("audit_note")
            == "Preserve scoped handoff"
        )
    if not preserved:
        issues.append("collaborator_business_change_lost")
    consumed = sum(
        r["payload"].get("units", 1)
        for r in receipts
        if r["payload"].get("kind") == "resource.consumption"
    )
    if data["v12_receiver_account"][0]["units"] != 8 - consumed:
        issues.append("quota_nonconservation")
    return sorted(set(issues))


def main(args):
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    for path in sorted(args.contracts.glob("*.json")):
        if path.name == "manifest.json":
            continue
        contract = load(path)
        ops = contract["private"]["initial_private_state"]["operations"]
        for op in ops:
            assert len(op["dependencies"]) == len(set(op["dependencies"])), path
        for replicate in range(2):
            evidence = args.evidence / contract["task_id"] / f"final-{replicate}.json"
            state = load(evidence)
            issues = check(contract, state)
            tests = []
            for op in ops:
                bad = copy.deepcopy(state)
                row = next(
                    r
                    for r in bad[
                        "tasks" if contract["application"] == "flowboard" else "ops_work_orders"
                    ]
                    if r["id"] == op["id"]
                )
                row["status" if contract["application"] == "flowboard" else "stage"] = "unfinished"
                tests.append(bool(check(contract, bad)))
            for mutation in ["physical", "approval", "restoration", "collaborator", "receipt"]:
                bad = copy.deepcopy(state)
                if mutation == "physical":
                    bad["v12_physical_effects"] = []
                elif mutation == "approval":
                    bad["v12_events"] = [
                        e
                        for e in bad["v12_events"]
                        if e["kind"] not in {"flow.role_approval", "ops.role_approval"}
                    ]
                elif mutation == "restoration":
                    bad["v12_controls"][0]["state"]["suspended"] = True
                elif mutation == "collaborator":
                    bad["v12_controls"][0]["state"]["collaborator_note"] = []
                else:
                    bad["v12_receipts"] = []
                tests.append(bool(check(contract, bad)))
            rows.append(
                dict(
                    task_id=contract["task_id"],
                    replicate=replicate,
                    issues=issues,
                    mutations=len(tests),
                    all_mutations_rejected=all(tests),
                    evidence=str(evidence),
                    sha256=checksum(evidence),
                )
            )
    result = dict(
        contracts=len(rows) // 2,
        positive_witnesses=len(rows),
        positive_accepted=sum(not r["issues"] for r in rows),
        mutations=sum(r["mutations"] for r in rows),
        mutation_sets_rejected=sum(r["all_mutations_rejected"] for r in rows),
        independent_implementation=True,
        independent_human_review=False,
        zero_model_calls=True,
        complete=all(not r["issues"] and r["all_mutations_rejected"] for r in rows),
        verifier_sha256=checksum(__file__),
    )
    (args.output / "rows.json").write_text(json.dumps(rows, indent=2) + "\n")
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
