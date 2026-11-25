"""Rebuild and independently verify the complete archived 36+6 trajectory cohort."""

import argparse
import json
from pathlib import Path

from afterclick.completion_v12.evidence import historical_audit
from afterclick.completion_v12.graphs import build
from afterclick.completion_v12.verify_graphs import verify

RUNS = [
    "x3-progressing-qwen-confirmation-b1-v2",
    "x3-progressing-qwen-confirmation-b2-v3",
    "x3-progressing-qwen-confirmation-b3-v3",
    "c1-supervisor-development-v1",
]


def execute(root, output):
    from research_ops.scripts.verify_supervision import verify as verify_supervision
    from research_ops.scripts.verify_timing_study import verify as verify_timing

    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    historical = historical_audit(root, output / "historical-integrity.json")
    scores = [
        (verify_supervision if name.startswith("c1-") else verify_timing)(
            root / "artifacts/research_runs" / name
        )
        for name in RUNS
    ]
    (output / "independent-rescores.json").write_text(json.dumps(scores, indent=2) + "\n")
    result = build(root, ["artifacts/research_runs/" + name for name in RUNS], output / "graphs")
    audit = verify(root, output / "graphs")
    report = dict(
        historical_runs=len(historical["historical_run_ids"]),
        historical_files=historical["checked_files"],
        branches=len(result["branches"]),
        graph_verifier=audit,
        new_model_calls=0,
        new_paid_compute_usd=0,
        v12_test_executions=0,
    )
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    execute(args.root, args.output)
