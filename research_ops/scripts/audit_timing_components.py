"""Derived operational attribution; keeps preregistered primary outcomes unchanged.

The historical analysis field prevention_deadline_ms is the IMPOSED eligibility
threshold. Actual consumer admission and independent receiver times are separate.
"""

import argparse
import json
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from research_ops.scripts.analyze_timing_study import read_lines


def audit(runs, out):
    records = []
    for run in runs:
        protocol = json.loads((run / "protocol.json").read_text())
        for row in protocol["cases"]:
            base = run / "raw" / row["id"]
            if not (base / "source-checkpoint.json").exists():
                continue
            source = json.loads((base / "source-checkpoint.json").read_text())["payload"]["world"][
                "tc_runtime"
            ][0]
            for arm in row["arm_order"]:
                d = base / arm
                if not (d / "final.json").exists():
                    continue
                final = json.loads((d / "final.json").read_text())
                events = final["tc_events"]
                receipts = final["tc_receipts"]
                inference = read_lines(d / "inference.jsonl")
                loss = [
                    e
                    for e in events
                    if e["kind"] == "dispatch.issued"
                    and row["template"] in [0, 1, 4, 5]
                    or e["kind"] == "access.ticket_snapshot"
                    and e["payload"].get("granted_at_snapshot")
                ]
                commands = sorted(
                    [
                        e
                        for e in events
                        if e["kind"]
                        in [
                            "command.cancel_notice",
                            "command.cancel_resource",
                            "command.revoke_access",
                        ]
                    ],
                    key=lambda e: e["wall"],
                )
                treatments = read_lines(d / "treatments.jsonl")
                worker = json.loads((d / "report.json").read_text()).get("worker_intervals", [])
                overlaps = [
                    dict(receipt_id=r["id"], receipt_wall=r["wall"], interval=i)
                    for r in receipts
                    for i in inference
                    if i["start_wall"] <= r["wall"] <= i["end_wall"]
                ]
                frontier_overlaps = [
                    dict(event_id=e["id"], kind=e["kind"], wall=e["wall"], ms=e["ms"], interval=i)
                    for e in loss
                    for i in inference
                    if i["start_wall"] <= e["wall"] <= i["end_wall"]
                ]
                ticks = sum(
                    any(i["start_wall"] <= w["start_wall"] <= i["end_wall"] for i in inference)
                    for w in worker
                )
                first = commands[0] if commands else None
                frontier = min(loss, key=lambda e: e["wall"]) if loss else None
                records.append(
                    dict(
                        source_id=row["id"],
                        arm=arm,
                        template=row["template"],
                        source_cut_ms=source["clock_ms"],
                        scheduled_eligibility_ms=source["state"]["deadline"],
                        actual_consumer_loss_event=frontier,
                        independent_receipts=[
                            {k: r[k] for k in ["id", "kind", "wall", "ms"]} for r in receipts
                        ],
                        first_protective_command=first,
                        late_or_absent_protection_at_witness=bool(
                            frontier and (first is None or first["wall"] > frontier["wall"])
                        ),
                        protection_before_nominal_eligibility=bool(
                            first and first["ms"] < source["state"]["deadline"]
                        ),
                        receipt_during_generation=overlaps,
                        frontier_during_generation=frontier_overlaps,
                        worker_ticks_during_generation=ticks,
                        visible_verification_seconds=sum(
                            t["seconds"]
                            for t in treatments
                            if t["action"]["target"].startswith("Verify")
                        ),
                        controller_actions=len(treatments),
                        controller_protective_actions=sum(
                            t["action"]["target"].startswith(("Cancel", "Revoke"))
                            for t in treatments
                        ),
                        controller_verifications=sum(
                            t["action"]["target"].startswith("Verify") for t in treatments
                        ),
                        source_to_first_controller_protection_ms=min(
                            [
                                e["ms"] - source["clock_ms"]
                                for e in commands
                                if e["actor"] == "controller"
                            ],
                            default=None,
                        ),
                        historical_bad_after_repair=(
                            "Evaluate from oracle; cancellation/revocation is "
                            "containment, not erasure"
                        ),
                    )
                )
    result = dict(
        schema_version=2,
        semantics=(
            "Eligibility imposed by schedule; loss event is consumer "
            "admission witness; physical observation is independent receiver "
            "receipt. Public acknowledgment may be delayed/missing and is not"
            " the observer HTTP ACK. No exact minimal prevention frontier "
            "inferred from eligibility alone."
        ),
        records=records,
        receipt_overlaps=sum(len(r["receipt_during_generation"]) for r in records),
        frontier_overlaps=sum(len(r["frontier_during_generation"]) for r in records),
        branches_with_progress_during_generation=sum(
            r["worker_ticks_during_generation"] > 0 for r in records
        ),
    )
    atomic_json(out, result)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    d = audit(a.runs, a.output)
    print(json.dumps({k: v for k, v in d.items() if k != "records"}, indent=2))
