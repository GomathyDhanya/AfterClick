"""Audit official DEV baseline metrics and evaluator-private fields without changing scoring."""

import json
from pathlib import Path


def main():
    run = Path("artifacts/research_runs/w2-undobench-official-local-v1")
    rows = []
    for p in sorted((run / "raw/baselines").glob("*/summary.json")):
        x = json.loads(p.read_text())
        rows.append(
            dict(
                method=p.parent.name,
                **{
                    k: x.get(k)
                    for k in ["total_pairs", "control_rate", "rsr", "crsr", "eor", "der", "mer"]
                },
            )
        )
    (run / "raw/official-baseline-table.json").write_text(json.dumps(rows, indent=2) + "\n")
    samples = []
    for p in sorted((run / "raw/baselines").glob("*/trajectories.jsonl")):
        for line in p.read_text().splitlines():
            row = json.loads(line)
            trace = row.get("benchmark_hidden_trace", {})
            # Keep full official trajectory. Only inspect documented oracle contract.
            v = trace.get("oracle_verdict", {})
            samples.append(
                dict(
                    method=p.parent.name,
                    task=row.get("task_id"),
                    condition=row.get("condition"),
                    official_final_status=row.get("final_status"),
                    local_state=v.get("final_state_correct"),
                    historical_forbidden_absent=v.get("forbidden_effects_absent"),
                    official_full=v.get("overall_success"),
                    prevention_feasible=None,
                )
            )
    (run / "raw/official-contract-projection.json").write_text(json.dumps(samples, indent=2) + "\n")
    print(json.dumps(rows))


if __name__ == "__main__":
    main()
