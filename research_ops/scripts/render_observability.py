"""Render saved observability evidence only. No training, simulation, SQL or endpoint calls."""

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

B = Path("artifacts/research_runs")
LABELS = {
    "ordinary": "Ordinary",
    "random_cf": "Random CF",
    "boundary": "Boundary",
    "uncertainty_boundary": "Uncertainty",
    "combined": "Combined",
}
METHODS = {
    "random_min": "Random + min",
    "systematic_min": "Systematic + min",
    "coverage_min": "Coverage + min",
    "frontier": "Local frontier",
}
COLORS = {
    "always_verify": "#899aa9",
    "observable_rule": "#227b55",
    "uncertainty_aware": "#b24a36",
    "declared_law_voi": "#4e71a6",
    "timer": "#8870a6",
    "static_risk": "#d09222",
    "learned_risk": "#a45f90",
}


def load(run):
    return json.loads((B / run / "metrics.json").read_text())


def table(out, name, heads, rows):
    with (out / (name + ".csv")).open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(heads)
        w.writerows(rows)

    def fmt(x):
        return f"{x:.6f}" if isinstance(x, float) else str(x)

    (out / (name + ".md")).write_text(
        "| "
        + " | ".join(heads)
        + " |\n| "
        + " | ".join(["---"] * len(heads))
        + " |\n"
        + "".join("| " + " | ".join(fmt(x) for x in row) + " |\n" for row in rows)
    )


def save(out, name, fig):
    fig.tight_layout()
    fig.savefig(out / (name + ".png"), dpi=180, bbox_inches="tight")
    fig.savefig(out / (name + ".svg"), bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update(
        {
            "font.size": 10,
            "svg.hashsalt": "afterclick-observability-v1",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    dev = load("o1-observability-development-v1")
    final = load("o2-observability-locked-v1")
    ablation = load("o4-context-ablation-v1")
    audit = load("o3-frontier-certificate-audit-v1")
    formats = json.loads((B / "i1-format-pair-v1/comparison.json").read_text())
    table(
        out,
        "format_table",
        [
            "Format",
            "Task accepted",
            "Generation requests",
            "Tokens",
            "Repeated proposals",
            "Executed repeats",
        ],
        [
            [
                r["format"],
                r["accepted"],
                r["policy_usage"]["calls"],
                r["policy_usage"]["known_total_tokens"],
                r["repeated_proposals"],
                r["executed_repetitions"],
            ]
            for r in formats["arms"]
        ],
    )
    search_rows = []
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for k, (label, result) in enumerate(
        [("Push development", dev["search"]), ("Pull locked", final["heldout_search"])]
    ):
        values = []
        for method in METHODS:
            rows = [x for x in result["rows"] if x["method"] == method]
            avg = statistics.mean(x["coverage_auc"] for x in rows)
            values.append(avg)
            search_rows.append(
                [
                    label,
                    METHODS[method],
                    192,
                    avg,
                    statistics.mean(x["unique_schedule_witnesses"] for x in rows),
                    statistics.mean(x["duplicate_queries"] for x in rows),
                ]
            )
        ax.bar(np.arange(4) + (k - 0.5) * 0.35, values, 0.35, label=label)
    ax.set_xticks(np.arange(4), METHODS.values())
    ax.set(
        ylabel="Mean cumulative timing-profile coverage",
        title="Coverage remains stronger than local frontier",
    )
    ax.legend()
    save(out, "search", fig)
    table(
        out,
        "search_table",
        [
            "Cohort",
            "Method",
            "Attempt budget",
            "Coverage AUC",
            "Timing profiles",
            "Duplicate queries",
        ],
        search_rows,
    )
    cohort_names = list(final["cohorts"])
    learning = []
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4))
    for ax, cohort in zip(axes, cohort_names):
        vals = []
        for arm in LABELS:
            rows = [
                x
                for x in final["learning_metrics"]
                if x["arm"] == arm
                and x["cohort"] == cohort
                and x["model"] == "discrete_hazard"
                and x["target"] == "harm_after_verify"
            ]
            v = statistics.mean(x["brier"] for x in rows)
            vals.append(v)
            learning.append([cohort, arm, v])
        ax.bar(range(5), vals, color=["#758caa", "#9aacc2", "#be684e", "#ba955c", "#62977b"])
        for model, style in [("observable_heuristic", "--"), ("declared_train_law", ":")]:
            v = statistics.mean(
                x["brier"]
                for x in final["learning_metrics"]
                if x["cohort"] == cohort
                and x["arm"] == "ordinary"
                and x["model"] == model
                and x["target"] == "harm_after_verify"
            )
            ax.axhline(
                v,
                color="black" if model == "observable_heuristic" else "#3d5791",
                linestyle=style,
                label=model.replace("_", " "),
            )
        ax.set_xticks(
            range(5), ["Ord.", "Random", "Boundary", "Uncert.", "Comb."], rotation=35, ha="right"
        )
        ax.set(title=cohort.replace("_", " "), ylabel="Brier (lower is better)")
        ax.legend(fontsize=7)
    save(out, "learning", fig)
    table(
        out, "learning_table", ["Cohort", "Data", "Preselected hazard verification Brier"], learning
    )
    controller_rows = []
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2))
    for ax, cohort in zip(axes, cohort_names):
        rows = [x for x in final["cohorts"][cohort]["controllers"] if x["budget"] == 0.3]
        for x in rows:
            controller_rows.append(
                [
                    cohort,
                    x["method"],
                    x["harms"],
                    x["legitimate_completion"],
                    x["task_completion"],
                    x["interventions"],
                    x["verification_count"],
                    x["logical_added_latency_mean"],
                ]
            )
            if x["method"] in COLORS:
                ax.scatter(
                    x["legitimate_completion"],
                    x["harm_rate"],
                    color=COLORS[x["method"]],
                    s=55,
                    label=x["method"].replace("_", " "),
                )
        ax.set(
            title=cohort.replace("_", " "),
            xlabel="Legitimate clean completion",
            ylabel="Unauthorized exposure rate",
        )
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.13))
    save(out, "controller_tradeoff", fig)
    table(
        out,
        "controller_table",
        [
            "Cohort",
            "Controller",
            "Harms /512",
            "Clean completion",
            "Overall task completion",
            "Interventions",
            "Verifications",
            "Mean logical latency ms",
        ],
        controller_rows,
    )
    races = []
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for k, (field, label) in enumerate(
        [
            ("H5_verify_minus_cancel", "Verify minus immediate cancel"),
            ("H5_slow_minus_fast", "Slow minus fast verification"),
        ]
    ):
        means = []
        low = []
        high = []
        for cohort in cohort_names:
            r = final["cohorts"][cohort][field]
            means.append(r["estimate"])
            low.append(r["estimate"] - r["ci95"][0])
            high.append(r["ci95"][1] - r["estimate"])
            races.append([cohort, label, r["estimate"], r["ci95"][0], r["ci95"][1], 512])
        ax.errorbar(
            np.arange(3) + (k - 0.5) * 0.1, means, yerr=[low, high], fmt="o", capsize=4, label=label
        )
    ax.set_xticks(np.arange(3), [c.replace("_", " ") for c in cohort_names])
    ax.set(
        ylabel="Additional unauthorized exposure fraction",
        title="Verification delay consumes preventive options",
    )
    ax.legend(fontsize=8)
    save(out, "verification_races", fig)
    table(
        out,
        "race_table",
        ["Cohort", "Paired contrast", "Risk difference", "CI lower", "CI upper", "Source clusters"],
        races,
    )
    vals = []
    for key, contrast in ablation["differences"].items():
        rows = [x for x in ablation["rows"] if x["original"] + "_" + x["model"] == key]
        vals.append(
            [
                key,
                statistics.mean(x["random_time_brier"] for x in rows),
                statistics.mean(x["boundary_brier"] for x in rows),
                contrast["estimate"],
                contrast["ci95"][0],
                contrast["ci95"][1],
            ]
        )
    table(
        out,
        "ablation_table",
        [
            "Development-only contrast",
            "Random-time same-context Brier",
            "Boundary Brier",
            "Random minus boundary",
            "CI lower",
            "CI upper",
        ],
        vals,
    )
    calibration_rows = []
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, cohort in zip(axes, cohort_names):
        ax.plot([0, 1], [0, 1], ":", color="gray")
        for model in ["discrete_hazard", "observable_heuristic"]:
            row = next(
                x
                for x in final["learning_metrics"]
                if x["cohort"] == cohort
                and x["arm"] == "ordinary"
                and x["repeat"] == 0
                and x["model"] == model
                and x["target"] == "harm_after_verify"
            )
            bins = row["calibration_bins"]
            ax.plot(
                [x["predicted"] for x in bins],
                [x["observed"] for x in bins],
                "o-",
                label=model.replace("_", " "),
            )
            calibration_rows.append(
                [
                    cohort,
                    model,
                    row["brier"],
                    row["auroc"],
                    row["auprc"],
                    row["ece10"],
                    row["fnr_at_half"],
                ]
            )
        ax.set(
            title=cohort.replace("_", " "),
            xlabel="Predicted risk",
            ylabel="Observed fraction",
            xlim=(-0.03, 1.03),
            ylim=(-0.03, 1.03),
        )
        ax.legend(fontsize=7)
    save(out, "calibration", fig)
    table(
        out,
        "calibration_table",
        ["Cohort", "Frozen repeat0 model", "Brier", "AUROC", "AUPRC", "ECE10", "FNR .5"],
        calibration_rows,
    )
    complete = []
    for cohort in cohort_names:
        for arm in LABELS:
            for model in [
                "base_rate",
                "timer",
                "observable_heuristic",
                "declared_train_law",
                "logistic",
                "gradient_boosting",
                "discrete_hazard",
            ]:
                rows = [
                    x
                    for x in final["learning_metrics"]
                    if x["cohort"] == cohort
                    and x["arm"] == arm
                    and x["model"] == model
                    and x["target"] == "harm_after_verify"
                ]
                complete.append(
                    [
                        cohort,
                        arm,
                        model,
                        512,
                        4,
                        *[
                            statistics.mean(x[k] for x in rows)
                            for k in ["brier", "auroc", "auprc", "ece10", "fnr_at_half"]
                        ],
                    ]
                )
    table(
        out,
        "all_model_metrics",
        [
            "Cohort",
            "Data",
            "Model",
            "Sources",
            "Fits",
            "Brier",
            "AUROC",
            "AUPRC",
            "ECE10",
            "FNR .5",
        ],
        complete,
    )
    # Clock separation is a saved SQL witness, not an invented illustration.
    witnesses = [
        json.loads(p.read_text())
        for p in (B / "o3-frontier-certificate-audit-v1/raw").glob("world-*.json")
    ]
    w = next(
        x
        for x in witnesses
        if x["witness"]["mechanism"] == "pull"
        and x["at"] == x["witness"]["pair"][1]
        and x["result"]["receipts"]
    )
    i = w["witness"]["instance"]
    receipt = w["result"]["receipts"][0]["arrival"]
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.axhline(0, color="#7d929c")
    events = [
        (i["frontier"], "Last cancellation frontier", 1),
        (i["commit"], "External restricted read", -0.9),
        (receipt, "Independent acknowledgment", 1),
    ]
    for at, label, y in events:
        ax.scatter(at, 0, color="#215c80", s=45)
        ax.annotate(
            label,
            xy=(at, 0),
            xytext=(max(10, at), y),
            ha="center",
            arrowprops={"arrowstyle": "-", "color": "#8c9ca5"},
            fontsize=9,
        )
    ax.set(
        xlabel="Logical time ms",
        ylim=(-1.3, 1.5),
        xlim=(-30, receipt + 65),
        title="Loss of prevention can precede physical exposure and its receipt",
    )
    ax.set_yticks([])
    save(out, "three_clocks", fig)
    (out / "summary.json").write_text(
        json.dumps(
            dict(
                schema_version=1,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                sql_witness_worlds=audit["valid"],
                distinct_paths=2,
                files_generated=sorted(p.name for p in out.iterdir()),
                input_metric_hashes={
                    name: hashlib.sha256((B / name / "metrics.json").read_bytes()).hexdigest()
                    for name in [
                        "o1-observability-development-v1",
                        "o2-observability-locked-v1",
                        "o3-frontier-certificate-audit-v1",
                        "o4-context-ablation-v1",
                    ]
                },
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    main(p.parse_args().output)
