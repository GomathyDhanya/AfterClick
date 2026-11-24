"""Regenerate summaries from saved evidence; never calls a model or opens a new holdout."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from afterclick.agent.modal_policy import atomic_json


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def wilson(success, n):
    if not n:
        return [None, None]
    z = 1.959963984540054
    p = success / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [mid - half, mid + half]


def exact_sign(a, b):
    wins = sum(x and not y for x, y in zip(a, b))
    losses = sum(y and not x for x, y in zip(a, b))
    n = wins + losses
    p = (
        min(1.0, 2 * sum(math.comb(n, k) * 0.5**n for k in range(min(wins, losses) + 1)))
        if n
        else 1.0
    )
    return dict(wins=wins, losses=losses, discordant=n, exact_two_sided_p=p)


def summarize(runs, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    primary = []
    traces = {}
    calls = []
    forecasts = []
    parents = []
    planned_groups = set()
    planned_arms = set()
    for run in map(Path, runs):
        p = json.loads((run / "protocol.json").read_text())
        planned_arms.update(p["execution_order"])
        from afterclick.tcope.workload_specs import workload_suite

        planned_groups.update(
            t.source_group for t in workload_suite(p["partition"]) if t.case_id == p["case_id"]
        )
        for row in lines(run / "trials.jsonl"):
            row = {**row, "run_id": run.name, "partition": p.get("partition")}
            if row.get("role") == "primary_controller":
                primary.append(row)
                path = run / "raw" / row["arm"] / "world/report.json"
                if path.exists():
                    traces[(row["source_group"], row["arm"])] = json.loads(path.read_text())
            elif row.get("role") == "public_belief_forecast":
                forecasts.append(row)
            elif row.get("role") == "source_parent":
                parents.append(row)
        calls += lines(run / "model_calls.jsonl")
    arms = sorted(planned_arms | {r["arm"] for r in primary})
    groups = sorted(planned_groups | {r["source_group"] for r in primary})
    by = {(r["source_group"], r["arm"]): r for r in primary}
    table = []
    for arm in arms:
        rows = [by[(g, arm)] for g in groups if (g, arm) in by]
        safe = [bool(r["valid"] and not r["censored"] and r["safe_task_success"]) for r in rows]
        reports = [
            traces[(r["source_group"], arm)] for r in rows if (r["source_group"], arm) in traces
        ]
        margins = []
        for report in reports:
            if "tc_runtime" not in report.get("state", {}):
                continue
            frontier = report["state"]["tc_runtime"][0]["state"]["deadline"]
            commands = [
                e
                for e in report["state"]["tc_events"]
                if e["kind"]
                in {"command.cancel_notice", "command.cancel_resource", "command.revoke_access"}
            ]
            if commands:
                margins.append(frontier - min(e["ms"] for e in commands))
        table.append(
            dict(
                arm=arm,
                planned=len(groups),
                attempted=len(rows),
                unattempted=len(groups) - len(rows),
                valid=sum(r["valid"] for r in rows),
                invalid=sum(r["invalid"] for r in rows),
                unknown=sum(r["unknown"] for r in rows),
                censored=sum(r["censored"] for r in rows),
                safe_completed=sum(safe),
                safe_rate=sum(safe) / len(groups) if groups else None,
                safe_wilson95=wilson(sum(safe), len(groups)),
                legitimate_completed=sum(
                    bool(r["goal_success"] and r["valid"] and not r["censored"]) for r in rows
                ),
                unauthorized_receipts=sum(r["unauthorized_receipts"] for r in rows),
                new_calls_including_forecasts=sum(
                    r.get("total_model_calls_including_forecasts", r["model_calls"]) for r in rows
                ),
                new_primary_calls=sum(r["model_calls"] for r in rows),
                mean_primary_wall_seconds=float(np.mean([r["elapsed_seconds"] for r in reports]))
                if reports
                else None,
                prevention_margins_ms=margins,
            )
        )
    contrasts = []
    for a, b in [
        ("tcope", "stage_verify"),
        ("tcope", "fixed_budget"),
        ("stage_verify", "time_blind"),
        ("time_blind", "latency_only"),
    ]:
        common = [g for g in groups if (g, a) in by and (g, b) in by]
        av = [
            bool(by[g, a]["safe_task_success"] and by[g, a]["valid"] and not by[g, a]["censored"])
            for g in common
        ]
        bv = [
            bool(by[g, b]["safe_task_success"] and by[g, b]["valid"] and not by[g, b]["censored"])
            for g in common
        ]
        d = np.array(av, dtype=float) - np.array(bv, dtype=float)
        rng = np.random.default_rng(20261126)
        boot = np.mean(rng.choice(d, (10000, len(d))), axis=1) if len(d) else np.array([np.nan])
        contrasts.append(
            dict(
                a=a,
                b=b,
                source_clusters=len(common),
                difference=float(np.mean(d)) if len(d) else None,
                source_bootstrap_descriptive95=(
                    np.quantile(boot, [0.025, 0.975]).tolist() if len(d) else [None, None]
                ),
                **exact_sign(av, bv),
                caution=(
                    "Degenerate bootstrap intervals on tiny all-tied samples do not establish "
                    "equivalence; one stochastic suffix per source/arm."
                ),
            )
        )
    # Holm across the preregistered first3 contrasts; fourth is secondary placebo.
    order = sorted(range(min(3, len(contrasts))), key=lambda i: contrasts[i]["exact_two_sided_p"])
    last = 0.0
    for rank, i in enumerate(order):
        last = max(last, min(1.0, (len(order) - rank) * contrasts[i]["exact_two_sided_p"]))
        contrasts[i]["holm_primary3_p"] = last
    usage = dict(
        genuine_started_requests=sum(r.get("event") == "started" for r in calls),
        known_finished_requests=sum(
            r.get("event") == "finished" and r.get("usage_known", False) for r in calls
        ),
        input_tokens=sum(r.get("input_tokens", 0) for r in calls if r.get("event") == "finished"),
        output_tokens=sum(r.get("output_tokens", 0) for r in calls if r.get("event") == "finished"),
    )
    result = dict(
        schema_version=1,
        source_groups=groups,
        primary_rows=primary,
        arms=table,
        contrasts=contrasts,
        forecasts=dict(
            attempted=len(forecasts),
            valid=sum(r["valid"] for r in forecasts),
            invalid=sum(r["invalid"] for r in forecasts),
            live_continuations=sum(r["live_continuation"] for r in forecasts),
            model_calls=sum(r["model_calls"] for r in forecasts),
        ),
        source_parents=len(parents),
        usage=usage,
        offline_best_observed_safe=sum(
            any(
                by[g, a]["safe_task_success"] and by[g, a]["valid"] and not by[g, a]["censored"]
                for a in arms
                if (g, a) in by
            )
            for g in groups
        ),
        scope=(
            "Paired real model suffixes conditional on actual prefixes; independent source "
            "instances, repeated mechanism families; no unseen-mechanism or optimality claim"
        ),
    )
    atomic_json(output / "summary.json", result)
    header = (
        "| Policy | Safe completion | Legitimate completion | Unauthorized receipts | "
        "New calls incl forecasts | Invalid / censored |\n|---|---:|---:|---:|---:|---:|\n"
    )
    body = "".join(
        (
            f"| {r['arm']} | {r['safe_completed']}/{r['planned']} | "
            f"{r['legitimate_completed']}/{r['planned']} | {r['unauthorized_receipts']} | "
            f"{r['new_calls_including_forecasts']} | {r['invalid']}/{r['censored']} |\n"
        )
        for r in table
    )
    (output / "table.md").write_text(header + body)
    if table:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout="constrained")
        labels = [r["arm"] for r in table]
        axes[0].bar(labels, [r["safe_rate"] for r in table], color="#27648e")
        axes[0].set_ylim(0, 1)
        axes[0].set_ylabel("Verified safe completion / source")
        axes[0].tick_params(axis="x", rotation=50)
        axes[1].scatter(
            [r["new_calls_including_forecasts"] / max(1, r["planned"]) for r in table],
            [r["safe_rate"] for r in table],
        )
        for r in table:
            axes[1].annotate(
                r["arm"],
                (r["new_calls_including_forecasts"] / max(1, r["planned"]), r["safe_rate"]),
                fontsize=8,
            )
        axes[1].set_xlabel("Actual new calls per source (including forecasts)")
        axes[1].set_ylabel("Verified safe completion")
        axes[1].set_ylim(-0.05, 1.05)
        fig.savefig(output / "safety-compute.png", dpi=180)
        plt.close(fig)
    print(json.dumps(dict(source_groups=len(groups), arms=table, usage=usage), indent=2))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", nargs="+", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    summarize(a.runs, a.output)
