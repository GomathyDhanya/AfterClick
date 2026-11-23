"""Read-only verification and analysis regeneration; optional explicitly local replica."""

import argparse
import json
import re
import shutil
import traceback
from pathlib import Path

from afterclick.model_sprint.diagnostic import probe
from afterclick.model_sprint.driver import append
from afterclick.model_sprint.records import register, seal, sha
from research_ops.scripts.analyze_live_sprint import analyze
from research_ops.scripts.verify_observability import verify


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--diagnostic-replica", help="Fresh run ID, local-only; no model requests")
    args = p.parse_args()
    verify(Path(__file__).resolve().parents[2])
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    (output / "raw").mkdir()
    (output / "figures").mkdir()
    source = Path("artifacts/research_runs/s1-natural-qwen-pilot-v1")
    shutil.copy(source / "model_calls.jsonl", output / "model_calls.jsonl")
    for report in (source / "raw").glob("task-*/report.json"):
        target = output / "raw" / report.parent.name
        target.mkdir()
        shutil.copy(report, target / "report.json")
    metrics = analyze(output)
    original = json.loads((source / "behavior-metrics.json").read_text())
    if metrics != original:
        raise ValueError("Derived pilot metrics differ from sealed results")
    if args.diagnostic_replica:
        if not re.fullmatch(r"s2-replica-[a-zA-Z0-9_-]+", args.diagnostic_replica):
            raise ValueError("Replica ID must start s2-replica-")
        old = Path("artifacts/research_runs/s2-comment-commit-diagnostic-v1")
        protocol = json.loads((old / "protocol.json").read_text())
        for name in ["schema_version", "run_id", "registered_utc"]:
            protocol.pop(name)
        protocol.update(replica_of=old.name, original_protocol_sha256=sha(old / "protocol.json"))
        protocol["exact_command"] = (
            ".venv/bin/python -m afterclick.model_sprint.diagnostic --run "
            "artifacts/research_runs/" + args.diagnostic_replica
        )
        run = register(args.diagnostic_replica, protocol)
        try:
            result = probe(run)
            expected = json.loads((old / "metrics.json").read_text())
            if result != expected:
                raise ValueError("Diagnostic replication differs")
        except BaseException:
            (run / "raw/replication-error.txt").write_text(traceback.format_exc())
            append(run / "trials.jsonl", dict(schema_version=1, event="crashed_or_interrupted"))
            seal(run, status="failed")
            raise
        (run / "analysis.md").write_text(
            "Exact local diagnostic replica: all aggregate results equal the original. "
            "Recorded/scripted actions only; zero new model requests.\n"
        )
        (run / "next_experiment.md").write_text("No paid work authorized by this replica.\n")
        seal(run)
    print("Verified sealed evidence and reproduced all pilot metrics; zero model requests.")


if __name__ == "__main__":
    main()
