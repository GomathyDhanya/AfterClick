"""Regenerate diagnostic summaries from saved evidence only; never contacts Modal."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path


def analyze(run):
    run = Path(run)
    metrics = json.loads((run / "metrics.json").read_text())
    events = [json.loads(line) for line in (run / "trials.jsonl").read_text().splitlines()]
    cli = [row for row in events if row.get("event") == "cli"]
    polls = [row for row in cli if row["args"][:2] == ["endpoint", "info"]]
    statuses = Counter()
    for row in polls:
        statuses[json.loads((run / row["raw_reference"]).read_text())["status"]] += 1
    before = json.loads((run / "raw/billing-before.json").read_text())
    after = json.loads((run / "raw/billing-after.json").read_text())
    credit_before = -Decimal(before["adjustments"]["credits"])
    credit_after = -Decimal(after["adjustments"]["credits"])
    failures = [row for row in events if row.get("event") == "run_failed"]
    return {
        "schema_version": 1,
        "run_id": run.name,
        "deployment_commands_attempted": sum(r["args"][:2] == ["endpoint", "create"] for r in cli),
        "readiness_poll_counts": dict(statuses),
        "latest_readiness_poll_seconds": polls[-1]["elapsed_seconds"] if polls else None,
        "failure_elapsed_seconds": failures[-1]["elapsed_seconds"] if failures else None,
        "elapsed_through_cleanup_seconds": metrics["elapsed_paid_seconds"],
        "model_calls_attempted": metrics["model_calls_attempted"],
        "valid_decisions": metrics["valid_decisions"],
        "invalid_decisions": metrics["invalid_decisions"],
        "decision_validity_rate": None
        if not metrics["model_calls_attempted"]
        else metrics["valid_decisions"] / metrics["model_calls_attempted"],
        "recovery_censored": 0,
        "recovery_unknown": 0,
        "recovery_scope": "No recovery attempted; operational timeout is not causal censoring.",
        "endpoint_stopped_verified": metrics["endpoint_stopped_verified"],
        "proxy_deleted": metrics["proxy_deleted"],
        "incremental_account_metered_usd_approx": str(
            Decimal(after["metered_cost"]) - Decimal(before["metered_cost"])
        ),
        "incremental_account_credit_used_usd_approx": str(credit_after - credit_before),
        "cumulative_account_credit_used_usd_approx": str(credit_after),
        "cumulative_account_billed_usd_approx": after["billed_cost"],
        "cost_scope": "Account snapshot deltas, delayed and not an exact per-run invoice.",
        "scientific_claims_supported": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.run), indent=2))


if __name__ == "__main__":
    main()
