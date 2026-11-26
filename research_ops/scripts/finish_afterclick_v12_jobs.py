"""Finite tail of the authorized study; no recurring automation or efficacy stop.

Waits only for the currently running registered job, then admits fixed remaining
external/larger work under the existing independent $18 ledger. Never retries a
closed or transport-uncertain trial. All time horizons are finite.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/research_runs"
PRIMARY = RUNS / "v12-44-frozen-primary-test-v1"
OUTPUT = ROOT / "research_ops/completion_v12/final_package/tail-execution.json"


def read(p):
    return json.loads(p.read_text())


def save(d):
    OUTPUT.write_text(json.dumps(d, indent=2) + "\n")


def execute(run, ledger):
    if (run / "raw/paid-start.json").exists():
        ledger.append(dict(run=run.name, disposition="PRESERVED_ALREADY_STARTED_NOT_RELAUNCHED"))
        save(ledger)
        return
    with (run / "execution.log").open("x") as stream:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "afterclick.completion_v12.benchmark.finance",
                "--run",
                str(run),
                "--execute",
            ],
            cwd=ROOT,
            stdout=stream,
            stderr=subprocess.STDOUT,
            timeout=read(run / "paid-protocol.json")["total_seconds"] + 180,
        )
    ledger.append(
        dict(
            run=run.name,
            returncode=result.returncode,
            paid_started=(run / "raw/paid-start.json").exists(),
            lifecycle=read(run / "lifecycle.json") if (run / "lifecycle.json").exists() else None,
        )
    )
    save(ledger)


def main():
    stop = (
        (PRIMARY / "raw/paid-start.json").stat().st_mtime
        + read(PRIMARY / "paid-protocol.json")["total_seconds"]
        + 180
    )
    while not (PRIMARY / "lifecycle.json").exists():
        if time.time() > stop:
            raise TimeoutError("Finite primary wait expired; do not bypass finance guard")
        time.sleep(5)
    ledger = []
    state = read(ROOT / "research_ops/completion_v12/FINANCE_STATE.json")
    if state.get("unresolved_request") and not state.get("active"):
        with (PRIMARY / "financial-closure.log").open("x") as stream:
            subprocess.run(
                [
                    sys.executable,
                    "research_ops/scripts/reconcile_afterclick_v12_finance.py",
                    "--run",
                    str(PRIMARY),
                ],
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=150,
            )
        state = read(ROOT / "research_ops/completion_v12/FINANCE_STATE.json")
    if state.get("active") or state.get("unresolved_request"):
        save(
            [
                dict(
                    disposition="BLOCKED_BY_EXISTING_FINANCE_GUARD",
                    active=state.get("active"),
                    unresolved=state.get("unresolved_request"),
                )
            ]
        )
        return
    q = (
        read(PRIMARY / "external-reconciliation.json")
        if (PRIMARY / "external-reconciliation.json").exists()
        else None
    )
    if q and q["complete"]:
        ledger.append(dict(scope="official_external", disposition="ORIGINAL_ALL_TERMINAL"))
    elif not list((PRIMARY / "external-episodes").glob("*/result.json")) and (
        not (PRIMARY / "external-usage.json").exists()
        or read(PRIMARY / "external-usage.json")["calls"] == 0
    ):
        execute(RUNS / "v12-56-official-external-test-finite", ledger)
    else:
        ledger.append(
            dict(
                scope="official_external",
                disposition="PARTIAL_ORIGINAL_REQUIRES_EXPLICIT_NON_DUPLICATING_ADMISSION",
                reconciliation=q,
            )
        )
        save(ledger)
    state = read(ROOT / "research_ops/completion_v12/FINANCE_STATE.json")
    if not state.get("active") and not state.get("unresolved_request"):
        execute(RUNS / "v12-50-frozen-larger-test-resume-v1", ledger)
    else:
        ledger.append(dict(scope="larger_resume", disposition="BLOCKED_BY_FINANCE_GUARD"))
        save(ledger)
    save(ledger)


if __name__ == "__main__":
    main()
