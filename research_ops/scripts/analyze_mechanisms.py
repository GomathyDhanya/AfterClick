"""Recompute saved local mechanism certificates and tables without database or cloud access."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from afterclick.contracts.schema import TaskContract
from afterclick.evaluation.finance_oracle import verify_finance
from afterclick.evaluation.recovery_reference import verify_recovery


def analyze(run, output):
    output.mkdir(parents=True, exist_ok=False)
    trials = [json.loads(s) for s in (run / "trials.jsonl").read_text().splitlines()]
    counts = Counter((t["mechanism"], t["classification"]) for t in trials)
    recomputed = []
    notification_recomputed = []
    followups = []
    for trial in trials:
        case = json.loads((run / trial["raw_reference"]).read_text())
        if trial["mechanism"] != "mock_payment_fee":
            cert = case["certificate"]
            current = verify_recovery(
                TaskContract.model_validate(case["contract"]),
                case["before"],
                case["after"],
                case["reference"],
                "selected",
                reference_validated=cert["reference_validated"],
                requests_quiescent=cert["requests_quiescent"],
                horizon_complete=cert["horizon_complete"],
            )
            assert current == cert, trial["case_id"]
            notification_recomputed.append(trial["case_id"])
            continue
        contract = TaskContract.model_validate(case["contract"])
        source = verify_recovery(
            contract,
            case["source_before"],
            case["source_after"],
            case["reference"]["source"],
            "selected",
            reference_validated=case["reference_certificate"]["valid"],
            requests_quiescent=True,
            horizon_complete=case["mode"] != "censored",
        )
        assert source == case["source_certificate"], trial["case_id"]
        cert = verify_finance(
            case["sink_before"],
            case["sink_after"],
            case["reference"]["sink"],
            case["source_before"]["effect_events"],
            source,
            reference_validated=case["reference_certificate"]["valid"],
            horizon_complete=case["mode"] != "censored",
            null=case["mode"] == "null",
        )
        assert cert == case["certificate"], trial["case_id"]
        recomputed.append(dict(case_id=trial["case_id"], primary_certificate_matches=True))
        if case["receipt_followup"]:
            later = case["receipt_followup"]
            cert = verify_finance(
                case["sink_before"],
                later["sink"],
                case["reference"]["sink"],
                case["source_before"]["effect_events"],
                source,
                reference_validated=True,
                horizon_complete=True,
            )
            assert cert == later["certificate"], trial["case_id"]
            followups.append(
                dict(
                    case_id=trial["case_id"],
                    primary_class=case["certificate"]["classification"],
                    primary_horizon=case["observation_horizon"],
                    recovery_time=case["recovery_time"],
                    event_time=cert["receipt_event_time"],
                    receipt_arrival=cert["receipt_arrival_time"],
                    followup_time=later["observation_time"],
                    followup_class=cert["classification"],
                    residual_fee=cert["residual_fee_units"],
                    primary_label_unchanged=later["primary_label_unchanged"],
                )
            )
    with (output / "counts.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["mechanism", "classification", "cases"])
        writer.writerows((*k, n) for k, n in sorted(counts.items()))
    with (output / "per_seed.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["mechanism", "seed", "classification", "cases"])
        strata = Counter((t["mechanism"], t["seed"], t["classification"]) for t in trials)
        writer.writerows((*k, n) for k, n in sorted(strata.items()))
    result = dict(
        schema_version=1,
        attempted=len(trials),
        metrics=json.loads((run / "metrics.json").read_text()),
        primary_finance_certificates_recomputed=len(recomputed),
        primary_notification_certificates_recomputed=len(notification_recomputed),
        delayed_followups_recomputed=len(followups),
        recomputation=recomputed,
        delayed_followups=followups,
        primary_input_sha256=hashlib.sha256((run / "trials.jsonl").read_bytes()).hexdigest(),
        analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        uncertainty=(
            "Enumerated planted fixtures and clustered seeds; "
            "no population CI or C1/C2/C3 estimate."
        ),
    )
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    # A small standalone timeline, with coordinates taken from archived receipt evidence.
    t = followups[0]
    events = [
        (t["event_time"], "Capture committed", 75),
        (t["recovery_time"], "Principal refunded", 125),
        (t["primary_horizon"], "Primary: UNKNOWN", 75),
        (t["receipt_arrival"], "Capture receipt arrives", 125),
        (t["followup_time"], "Follow-up: UNRECOVERABLE", 175),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="265" viewBox="0 0 1050 265">',
        '<rect width="1050" height="265" fill="white"/>',
        '<g font-family="sans-serif" font-size="14" fill="#172b4d">',
        '<text x="25" y="30" font-size="19">Scheduled fake-fee fixture: '
        "commit time and receipt arrival differ</text>",
        '<line x1="45" y1="210" x2="980" y2="210" stroke="#52657a"/>',
    ]
    for at, label, y in events:
        x = 45 + at * 1.8
        parts.extend(
            [
                f'<line x1="{x}" x2="{x}" y1="{y + 12}" y2="210" stroke="#8fa6bf"/>',
                f'<circle cx="{x}" cy="210" r="4" fill="#195e93"/>',
                f'<text x="{x}" y="{y}" text-anchor="middle">{label}</text>',
                f'<text x="{x}" y="233" text-anchor="middle">{at}</text>',
            ]
        )
    parts.extend(
        [
            '<text x="25" y="257">Logical time units; seed7 development fixture. '
            "Primary label remains UNKNOWN; no discovered minimal boundary claimed.</text>",
            "</g></svg>",
        ]
    )
    (output / "receipt_timeline.svg").write_text("\n".join(parts))
    print(json.dumps({k: v for k, v in result.items() if k not in {"recomputation", "metrics"}}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Fresh destination")
    args = parser.parse_args()
    analyze(args.run, args.output)


if __name__ == "__main__":
    main()
