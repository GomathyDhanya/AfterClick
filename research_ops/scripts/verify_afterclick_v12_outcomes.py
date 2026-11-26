"""Re-score saved experimental snapshots with frozen and separate oracle code."""

import argparse
import hashlib
import json
from pathlib import Path

from afterclick.completion_v12.oracle_v2 import evaluate
from research_ops.scripts.v12_independent_audit import check


def load(p):
    return json.loads(p.read_text())


def main(roots, contracts, output):
    output.mkdir(parents=True, exist_ok=False)
    ledger = []
    errors = []
    for root in roots:
        for p in sorted(root.glob("cloud-batches/**/episodes/*/result.json")):
            row = load(p)
            folder = Path(row.get("raw_result_path", str(p))).parent
            final = folder / "final.json"
            if not final.exists():
                ledger.append(
                    dict(episode=row["episode_id"], status="UNKNOWN_MISSING_FINAL", result=str(p))
                )
                continue
            contract = load(contracts / (row["task_id"] + ".json"))
            data = load(final)
            saved = row.get("score") or {}
            valid = row["status"] == "VALID"
            rescored, separate = {}, []
            if valid:
                try:
                    rescored = evaluate(contract, data)
                    separate = check(contract, data)
                except Exception as error:
                    separate = ["INDEPENDENT_CHECKER_ERROR:" + type(error).__name__]
            else:
                separate = ["UNASSESSED_INVALID_OR_CENSORED_TRIAL"]
            equality = (not valid) or (
                saved.get("joint_safe_completion") == rescored.get("joint_safe_completion")
            )
            agreement = (not valid) or ((not separate) == saved.get("joint_safe_completion"))
            item = dict(
                episode=row["episode_id"],
                status=row["status"],
                frozen_rescore_matches=equality,
                independent_joint_matches=agreement,
                independent_issues=separate,
                result=str(p),
                result_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                final=str(final),
                final_sha256=hashlib.sha256(final.read_bytes()).hexdigest(),
            )
            ledger.append(item)
            if not equality or not agreement:
                errors.append(item)
    report = dict(
        terminal=len(ledger),
        valid=sum(r["status"] == "VALID" for r in ledger),
        disagreements=len(errors),
        passed=not errors,
        independent_implementation=True,
        independent_human_review=False,
        zero_model_calls=True,
        checker_sha256=hashlib.sha256(
            Path("research_ops/scripts/v12_independent_audit.py").read_bytes()
        ).hexdigest(),
    )
    (output / "ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", type=Path, nargs="+", required=True)
    p.add_argument(
        "--contracts", type=Path, default=Path("research_ops/completion_v12/candidate_contracts_v7")
    )
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.runs, a.contracts, a.output)
