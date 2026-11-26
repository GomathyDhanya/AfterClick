"""Versioned offline grading; never alter an original trajectory or recorded score."""

import argparse
import json
import shutil
from pathlib import Path

from afterclick.completion_v12.evidence import sha
from afterclick.completion_v12.oracle_v2 import evaluate


def load(path):
    return json.loads(path.read_text())


def main(args):
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path("afterclick/completion_v12/oracle_v2.py")
    shutil.copyfile(source, args.output / "oracle-source.py")
    contracts = {
        p.stem: load(p) for p in args.contracts.glob("*.json") if p.name != "manifest.json"
    }
    positives = []
    for key, c in contracts.items():
        for index in range(2):
            path = args.qualification / key / f"final-{index}.json"
            score = evaluate(c, load(path))
            assert score["status"] == "VALID" and score["joint_safe_completion"] is True, (
                key,
                index,
                score,
            )
            positives.append(
                dict(
                    task_id=key, replicate=index, evidence=str(path), sha256=sha(path), score=score
                )
            )
    (args.output / "reference-rescores.json").write_text(json.dumps(positives, indent=2) + "\n")
    derived = args.output / "derived-development"
    derived.mkdir()
    shutil.copyfile(args.dev / "registration.json", derived / "registration.json")
    shutil.copyfile(args.dev / "queue-reconciliation.json", derived / "queue-reconciliation.json")
    changes = []
    scores = []
    for path in args.dev.glob("cloud-batches/**/episodes/*/result.json"):
        row = load(path)
        snapshot_path = path.parent / "final.json"
        if not snapshot_path.exists():
            scores.append(
                dict(episode_id=row["episode_id"], status="MISSING_FINAL", raw_result=str(path))
            )
            continue
        old = row.get("score")
        errors = load(path.parent / "worker-errors.json")
        score = evaluate(contracts[row["task_id"]], load(snapshot_path), errors)
        updated = dict(
            row,
            original_score=old,
            score=score,
            status=score["status"],
            raw_result_path=str(path.resolve()),
            raw_result_sha256=sha(path),
            raw_final_path=str(snapshot_path.resolve()),
            raw_final_sha256=sha(snapshot_path),
            derived_only=True,
            new_model_calls=0,
            oracle_source_sha256=sha(source),
        )
        target = derived / path.relative_to(args.dev)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(updated, indent=2) + "\n")
        if old.get("joint_safe_completion") != score["joint_safe_completion"]:
            changes.append(
                dict(
                    episode_id=row["episode_id"],
                    old=old.get("joint_safe_completion"),
                    new=score["joint_safe_completion"],
                    raw_result=str(path),
                    raw_sha256=sha(path),
                    implicit_receipt_reconciliations=score["implicit_receipt_reconciliations"],
                )
            )
        scores.append(
            dict(
                episode_id=row["episode_id"],
                status=score["status"],
                joint_safe_completion=score["joint_safe_completion"],
            )
        )
    result = dict(
        reference_witnesses=len(positives),
        reference_accepted=len(positives),
        dev_records=len(scores),
        changed_dev_labels=len(changes),
        dev_safe=sum(r.get("joint_safe_completion") is True for r in scores),
        original_data_unchanged=True,
        new_model_calls=0,
        grader_sha256=sha(source),
        derived_development=str(derived),
        complete=len(positives) == 576 and len(scores) == 252,
        reason=(
            "Pre-TEST correction accepts actual receipt-backed idempotent "
            "reconciliation, without inventing events or relaxing immutable-effect "
            "constraints"
        ),
    )
    (args.output / "changed-labels.json").write_text(json.dumps(changes, indent=2) + "\n")
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for key in ["contracts", "qualification", "dev", "output"]:
        p.add_argument("--" + key, type=Path, required=True)
    main(p.parse_args())
