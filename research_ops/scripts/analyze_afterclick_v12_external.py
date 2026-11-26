"""Official dual-verdict summaries, clustered by upstream task (exploratory intervals)."""

import argparse
import collections
import json
from pathlib import Path
import numpy as np


def main(registration, roots, output):
    output.mkdir(parents=True, exist_ok=False)
    registered = json.loads(registration.read_text())
    actual = {}
    for root in roots:
        for p in root.glob("external-episodes/*/result.json"):
            r = json.loads(p.read_text())
            assert r["episode_id"] not in actual
            actual[r["episode_id"]] = dict(r, evidence=str(p))
    rows = []
    pairs = collections.defaultdict(dict)
    for cell in registered["episodes"]:
        r = actual.get(cell["episode_id"], dict(status="NOT_RUN"))
        v = r.get("official_verdict", {})
        row = dict(
            cell,
            status=r["status"],
            overall_success=v.get("overall_success"),
            goal_satisfied=v.get("goal_satisfied"),
            forbidden_effects_absent=v.get("forbidden_effects_absent"),
            duplicate_effects_count=v.get("duplicate_effects_count"),
            failure_classification=v.get("failure_classification"),
            evidence=r.get("evidence"),
        )
        rows.append(row)
        pairs[(cell["task_id"], cell["method"], cell["seed"])][cell["condition"]] = row
    summaries = []
    rng = np.random.default_rng(251126)
    for method in sorted({r["method"] for r in rows}):
        p = [v for (task, m, seed), v in pairs.items() if m == method]
        control = [v["CONTROL"] for v in p]
        fault = [v["FAULT"] for v in p]
        capable = [v for v in p if v["CONTROL"]["overall_success"] is True]
        eligible = [v for v in capable if v["FAULT"]["overall_success"] is not None]
        task_ids = sorted({v["CONTROL"]["task_id"] for v in p})
        draws = []
        for _ in range(10000):
            sampled = rng.choice(task_ids, len(task_ids), replace=True)
            num = den = 0
            for task in sampled:
                for v in eligible:
                    if v["CONTROL"]["task_id"] == task:
                        den += 1
                        num += v["FAULT"]["overall_success"] is True
            if den:
                draws.append(num / den)
        summary = dict(
            method=method,
            registered_control=len(control),
            registered_fault=len(fault),
            control_success=sum(r["overall_success"] is True for r in control),
            fault_success=sum(r["overall_success"] is True for r in fault),
            unknown_control=sum(r["overall_success"] is None for r in control),
            unknown_fault=sum(r["overall_success"] is None for r in fault),
            control_capable_pairs=len(capable),
            complete_control_capable_pairs=len(eligible),
            conditional_recovery_success=(
                sum(v["FAULT"]["overall_success"] is True for v in eligible) / len(eligible)
            )
            if eligible
            else None,
            conditional_task_bootstrap95=np.quantile(draws, [0.025, 0.975]).tolist()
            if draws
            else None,
            bootstrap_zero_support_draws=10000 - len(draws),
            goal_only_fault=sum(
                r["goal_satisfied"] is True and r["overall_success"] is False for r in fault
            ),
            unsafe_fault=sum(r["forbidden_effects_absent"] is False for r in fault),
            duplicate_effects=sum(r["duplicate_effects_count"] or 0 for r in fault),
        )
        summaries.append(summary)
    report = dict(
        registered=len(rows),
        terminal=len(actual),
        missing=[r["episode_id"] for r in rows if r["status"] == "NOT_RUN"],
        methods=summaries,
        cluster_unit="Official task; context seeds are not independent fault programs",
        intervals="Exploratory 10000 task bootstrap draws; tiny 12-source external scope",
        unavailable_methods=["EvoUndo"],
        official_engine_tasks_tools_prompts_oracles_unchanged=True,
    )
    (output / "episode-table.json").write_text(json.dumps(rows, indent=2) + "\n")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registration", type=Path, required=True)
    p.add_argument("--runs", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.registration, a.runs, a.output)
