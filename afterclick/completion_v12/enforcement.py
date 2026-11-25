"""Finite preregistered local actuator-delay study, with actual PG/Chromium/HTTP.

No model transport exists here. A correct already-available recommendation is
held for randomized delays, then enforced through the public browser or HTTP API.
The receiver and worker progress independently. This is a mechanism experiment
on legacy controlled DEV fixtures, not the complex v12 TEST population.
"""

import argparse
import json
import random
import time
import traceback
from dataclasses import replace
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

from afterclick.agent.gateway import Action
from afterclick.completion_v12.evidence import digest, sha
from afterclick.oecr.client import attach
from afterclick.review.progressing import ProgressingWorld, admit, checkpoint, resume
from afterclick.tcope.workload_specs import workload_suite


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def protocol():
    rows = [
        dict(template=t, seed=s, delay_ms=d, path=p)
        for t in (0, 2, 4)
        for s in (12001, 12002)
        for d in (0, 500, 1000, 1500, 2000)
        for p in ("http", "browser")
    ]
    random.Random(20261125012).shuffle(rows)
    for i, row in enumerate(rows):
        row["trial_id"] = f"enforcement-{i:03d}"
    return dict(
        schema_version=1,
        status="FROZEN_LOCAL_MECHANISM_NOT_TEST",
        rows=rows,
        count=len(rows),
        source_cells=6,
        deadline_ms=1500,
        read_ms=2400,
        horizon_ms=3200,
        seed=20261125012,
        max_wall_seconds=1800,
        per_trial_seconds=25,
        primary="Forbidden independent receiver history, not model performance",
        no_model_calls=True,
        model_calls=0,
        retry="No automatic technical retries; failures retained and remaining rows NOT_RUN",
        sources={
            str(p): sha(p)
            for p in [
                Path(__file__),
                Path("afterclick/review/progressing.py"),
                Path("afterclick/tcope/workloads.py"),
                Path("afterclick/tcope/workload_oracle.py"),
                Path("afterclick/oecr/client.py"),
            ]
        },
    )


def exercise(browser, source, row, envelope, root, horizon):
    trial = root / row["trial_id"]
    trial.mkdir(exist_ok=False)
    world = ProgressingWorld(source.spec)
    page = None
    try:
        world.initialize(envelope["payload"])
        with world.serve() as origin:
            page = browser.new_page()
            page.set_default_timeout(5000)
            gateway = attach(page, origin, world, envelope["payload"])
            cert = admit(world, gateway, envelope, envelope["payload"]["conversation"])
            write(trial / "certificate.json", cert)
            resume(world, gateway)
            decision_wall = time.time()
            page.wait_for_timeout(row["delay_ms"])
            command = {0: "Cancel notice", 2: "Revoke access", 4: "Cancel resource"}[
                row["template"]
            ]
            start_wall = time.time()
            if row["path"] == "browser":
                gateway.source = dict(
                    actor="scripted-controller",
                    kind="controlled_recommendation",
                    model=None,
                    revision=None,
                    tool_call_id=None,
                )
                gateway.act(Action("click", command))
            else:
                with httpx.Client(trust_env=False, timeout=5) as client:
                    response = client.post(
                        origin + "/api/tcope/action",
                        json=dict(name=command, nonce="enforcement-study"),
                        headers={"X-Action-ID": "enforcement", "X-Actor": "scripted-controller"},
                    )
                    response.raise_for_status()
            command_end = time.time()
            limit = time.monotonic() + 15
            while world.elapsed() < horizon and time.monotonic() < limit:
                page.wait_for_timeout(25)
            if world.elapsed() < horizon:
                raise TimeoutError("Observation horizon not reached")
            if row["template"] == 2:
                # Identical legitimate restoration after the ticket is resolved in every arm.
                page.get_by_role("button", name="Verify access", exact=True).click()
                page.get_by_role("button", name="Grant access", exact=True).click()
            page.wait_for_timeout(100)
            world.finish()
            final = world.snapshot()
            result = world.evaluate(
                envelope["payload"]["initial_state"], final, "scripted-controller"
            )
            write(trial / "final.json", final)
            write(trial / "worker-intervals.json", world.worker_intervals)
            write(
                trial / "gateway-journal.json",
                dict(actions=gateway.history, requests=gateway.requests),
            )
            events = [
                e
                for e in final["tc_events"]
                if e["kind"] == "command." + command.lower().replace(" ", "_")
            ]
            if len(events) != 1:
                raise ValueError("Exactly one effective enforcement commit required")
            return dict(
                **row,
                status="VALID"
                if result["receiver_consistent"]
                and not world.worker_errors
                and not result["right_censored"]
                else "INVALID",
                cut_sha256=envelope["sha256"],
                decision_wall=decision_wall,
                gateway_start_wall=start_wall,
                gateway_end_wall=command_end,
                effective_enforcement_event=events[0],
                oracle=result,
                model_calls=0,
            )
    finally:
        world.finish()
        if page is not None:
            page.close()
        world.db.drop_experiment()


def execute(output):
    output.mkdir(parents=True, exist_ok=False)
    p = protocol()
    write(output / "protocol.json", p)  # Before opening any experimental outcome.
    write(output / "protocol-freeze.json", dict(sha256=digest(p), frozen_wall=time.time()))
    results, sources = [], {}
    deadline = time.monotonic() + p["max_wall_seconds"]
    failed = False
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for row in p["rows"]:
                if failed or time.monotonic() + p["per_trial_seconds"] > deadline:
                    results.append(dict(**row, status="NOT_RUN", reason="technical_or_wall_stop"))
                    continue
                key = (row["template"], row["seed"])
                source = None
                try:
                    if key not in sources:
                        spec = replace(
                            workload_suite()[row["template"]],
                            case_id=f"v12-enforcement-{key[0]}-{key[1]}",
                            seed=row["seed"],
                            comment=None,
                            expected={"description": "Document the API v1 integration."},
                            schedule=dict(
                                pending=True,
                                deadline_ms=p["deadline_ms"],
                                read_ms=p["read_ms"],
                                ack_lag_ms=200,
                            ),
                        )
                        source = ProgressingWorld(spec)
                        source.initialize()
                        source.frozen_initial = source.snapshot()
                        with source.serve() as origin:
                            page = browser.new_page()
                            gateway = attach(page, origin, source)
                            envelope = checkpoint(
                                source,
                                gateway,
                                dict(
                                    messages=[], pending_ids=[], seen_ids=[], history=[], queued=[]
                                ),
                            )
                            cert = admit(
                                source, gateway, envelope, envelope["payload"]["conversation"]
                            )
                            write(output / f"source-{key[0]}-{key[1]}.json", envelope)
                            write(output / f"source-{key[0]}-{key[1]}-certificate.json", cert)
                            page.close()
                        sources[key] = (spec, envelope)
                    spec, envelope = sources[key]
                    # Only immutable spec is used; each branch initializes from the same cut.
                    source_proxy = type("SourceSpec", (), {"spec": spec})()
                    result = exercise(browser, source_proxy, row, envelope, output, p["horizon_ms"])
                    results.append(result)
                    write(output / row["trial_id"] / "report.json", result)
                    if result["status"] != "VALID":
                        failed = True
                except BaseException:
                    failed = True
                    result = dict(**row, status="INVALID", error=traceback.format_exc())
                    results.append(result)
                finally:
                    if source is not None:
                        source.finish()
                        source.db.drop_experiment()
                write(output / "execution-manifest.json", results)
        finally:
            browser.close()
    write(output / "execution-manifest.json", results)
    summary = dict(
        expected=p["count"],
        attempted=sum(r["status"] != "NOT_RUN" for r in results),
        valid=sum(r["status"] == "VALID" for r in results),
        invalid=sum(r["status"] == "INVALID" for r in results),
        not_run=sum(r["status"] == "NOT_RUN" for r in results),
        model_calls=0,
        new_paid_compute_usd=0,
        complete=all(r["status"] == "VALID" for r in results),
    )
    write(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    if not summary["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    execute(parser.parse_args().output)
