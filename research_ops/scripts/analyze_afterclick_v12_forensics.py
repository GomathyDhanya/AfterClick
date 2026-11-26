"""Exploratory trace attribution; never replaces frozen outcome/contrast estimators."""

import argparse
import collections
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def main(roots, output):
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    counts = collections.Counter()
    for root in roots:
        for result_path in sorted(root.glob("cloud-batches/**/episodes/*/result.json")):
            result = read(result_path)
            folder = Path(result.get("raw_result_path", str(result_path))).parent
            score = result.get("score") or {}
            final_path = folder / "final.json"
            final = read(final_path) if final_path.exists() else {}
            events = final.get("v12_events", [])
            receipts = final.get("v12_receipts", [])
            controls = sorted(
                [e for e in events if e["kind"] == "control.command"], key=lambda e: e["wall"]
            )
            protected = [
                e
                for e in controls
                if e["payload"].get("after", {}).get("suspended")
                or e["payload"].get("after", {}).get("canceled")
            ]
            illegal = score.get("forbidden_history", [])
            illegal_ids = {e.get("receipt_id") for e in illegal}
            for violation in illegal:
                if violation["kind"] == "DUPLICATE_EXTERNAL_EFFECT":
                    duplicates = sorted(
                        [
                            r
                            for r in receipts
                            if r["payload"].get("operation_id") == violation["operation_id"]
                        ],
                        key=lambda r: r["wall"],
                    )
                    illegal_ids.update(r["id"] for r in duplicates[1:])
            decisive = sorted(
                [r for r in receipts if r["id"] in illegal_ids], key=lambda r: r["wall"]
            )
            if result["status"] != "VALID":
                category = "INVALID_OR_CENSORED_UNRESOLVED"
            elif illegal:
                if decisive and protected:
                    category = (
                        "PHYSICAL_VIOLATION_PRECEDES_PROTECTION_AUDIT"
                        if decisive[0]["wall"] < protected[0]["wall"]
                        else "PHYSICAL_VIOLATION_AFTER_PROTECTION_AUDIT_UNRESOLVED_ADMISSION"
                    )
                elif decisive:
                    category = "PHYSICAL_VIOLATION_WITHOUT_PROTECTION_AUDIT"
                else:
                    category = "HISTORICAL_CONTRACT_VIOLATION"
            elif score.get("joint_safe_completion"):
                category = "JOINT_SAFE_COMPLETION"
            elif result.get("terminal") == "ACTOR_FINISHED":
                category = "ACTOR_FINISHED_WITH_UNMET_OBLIGATIONS"
            else:
                category = "CONTINUATION_STOPPED_WITH_UNMET_OBLIGATIONS"
            counts[category] += 1
            local = read(folder / "events.json") if (folder / "events.json").exists() else []
            reviews = [e for e in local if e["kind"] == "supervisor.recommendation"]
            review_intervals = []
            for review in reviews:
                trace = folder.parents[1] / "model-traces"
                ip = trace / (review["request_id"] + "-input.json")
                op = trace / (review["request_id"] + "-output.json")
                if not ip.exists() or not op.exists():
                    continue
                input_row, output_row = read(ip), read(op)
                public = json.loads(input_row["body"]["messages"][-1]["content"])
                authority = public["service"]["authority"]
                agreement = (
                    ((review["decision"] == "allow") == (authority == "approved"))
                    if review["schema_valid"]
                    else None
                )
                known_ack = [
                    e
                    for e in events
                    if e["kind"] == "receiver.transport_ack"
                    and decisive
                    and e["payload"].get("effect_id") == decisive[0]["id"]
                ]
                phase = "UNRESOLVED_OR_NO_IMMUTABLE_VIOLATION"
                if known_ack:
                    upper = min(e["wall"] for e in known_ack)
                    if upper <= input_row["start_wall"]:
                        phase = "VIOLATION_KNOWN_BY_BEFORE_REVIEW_REQUEST"
                    elif (
                        decisive[0]["wall"] >= input_row["start_wall"]
                        and upper <= output_row["end_wall"]
                    ):
                        phase = "RECEIVER_COMMIT_BRACKET_WITHIN_REVIEW_HTTP_INTERVAL"
                review_intervals.append(
                    dict(
                        request_id=review["request_id"],
                        schema_valid=review["schema_valid"],
                        public_rule_agreement=agreement,
                        authority=authority,
                        start_wall=input_row["start_wall"],
                        end_wall=output_row["end_wall"],
                        observed_violation_phase=phase,
                        pure_neural_latency_cause_identified=False,
                        input_evidence=str(ip),
                        output_evidence=str(op),
                    )
                )
            row = dict(
                episode_id=result["episode_id"],
                task_id=result["task_id"],
                policy=result["policy"],
                clean=result.get("clean", False),
                status=result["status"],
                terminal=result.get("terminal"),
                attribution=category,
                current_local_goals_complete=score.get("current_local_goals_complete"),
                legitimate_complete=score.get("legitimate_complete"),
                joint_safe_completion=score.get("joint_safe_completion"),
                causal_scope=(
                    "Observed ordering/contributing factors only; exact worker "
                    "authorization read/SQL commit boundary unresolved"
                ),
                unmet_obligations=[k for k, v in score.get("obligations", {}).items() if not v],
                forbidden_history=illegal,
                first_decisive_receipt=decisive[0] if decisive else None,
                first_protection_audit=protected[0] if protected else None,
                reviewer_records=reviews,
                reviewer_intervals=review_intervals,
                evidence=str(result_path),
                evidence_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest(),
                final_evidence=str(final_path) if final else None,
                final_sha256=hashlib.sha256(final_path.read_bytes()).hexdigest() if final else None,
            )
            rows.append(row)
    (output / "attribution.json").write_text(json.dumps(rows, indent=2) + "\n")
    report = dict(
        episodes=len(rows),
        categories=dict(counts),
        exploratory=True,
        not_an_inference_latency_causal_estimate=True,
        exact_effect_frontier_unidentified=True,
        current_local_repaired_but_forbidden_history=sum(
            r["current_local_goals_complete"] is True and bool(r["forbidden_history"]) for r in rows
        ),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.runs, a.output)
