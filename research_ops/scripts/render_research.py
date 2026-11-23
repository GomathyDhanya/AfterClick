"""Regenerate publication figures/tables from preserved results; never fits or calls endpoints."""

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from afterclick.research.features import Features

BASE = Path("artifacts/research_runs")
LABELS = {
    "plain_random": "Random",
    "random_min": "Random + minimize",
    "coverage_min": "Coverage + minimize",
    "local_frontier": "Local frontier",
    "enumeration": "Enumeration",
}
ARMS = ["ordinary", "random_cf", "boundary", "combined", "ordinary_equal_rows"]
ARM_LABELS = ["Ordinary", "Random CF", "Boundary", "Combined", "Equal-row ordinary"]


def load(run, file="metrics.json"):
    return json.loads((BASE / run / file).read_text())


def save(fig, output, name):
    fig.tight_layout()
    fig.savefig(output / (name + ".png"), dpi=180, bbox_inches="tight")
    fig.savefig(output / (name + ".svg"), bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)


def table(output, name, headers, rows):
    with (output / (name + ".csv")).open("w") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    def format_value(x):
        return f"{x:.6f}" if isinstance(x, float) else str(x)

    text = "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n"
    text += "".join("| " + " | ".join(format_value(x) for x in row) + " |\n" for row in rows)
    (output / (name + ".md")).write_text(text)


def render(output):
    output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    plt.rcParams["svg.hashsalt"] = "afterclick-evidence-v1"
    search = load("p4-matched-search-v1")
    dev = load("p6-risk-study-v1")
    final = load("p9-locked-confirmation-v1")
    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    for method, values in search["methods"].items():
        ax.plot(range(1, 97), values["mean_curve"], label=LABELS[method], linewidth=2)
    ax.set(
        xlabel="Attempted candidate queries (including repeats)",
        ylabel="Distinct mechanisms with adjacent witness",
        ylim=(-0.1, 4.2),
    )
    ax.legend(fontsize=9, loc="upper left")
    ax.set_title("Strong coverage beats the targeted local method")
    save(fig, output, "search_efficiency")
    table(
        output,
        "search_table",
        ["Method", "Coverage AUC", "Mechanisms at96", "Transition types", "Delta vs coverage"],
        [
            [
                LABELS[k],
                v["mean_coverage_auc"],
                v["mean_unique_mechanisms"],
                v["mean_unique_transitions"],
                v["paired_auc_difference_vs_coverage"],
            ]
            for k, v in search["methods"].items()
        ],
    )

    def mean_brier(arm, model, cohort):
        source = final["learning_metrics"] if cohort == "deadline_final" else dev["metric_rows"]
        return statistics.mean(
            x["brier"]
            for x in source
            if x["arm"] == arm and x["model"] == model and x["cohort"] == cohort
        )

    learning = []
    for arm in ARMS:
        vals = [
            x["training_rows"]
            for x in dev["metric_rows"]
            if x["arm"] == arm and x["model"] == "gradient_boosting" and x["cohort"] == "ID"
        ]
        learning.append(
            [
                arm,
                statistics.mean(vals),
                512,
                mean_brier(arm, "gradient_boosting", "ID"),
                mean_brier(arm, "gradient_boosting", "authority_OOD_current"),
                mean_brier(arm, "gradient_boosting", "deadline_final"),
                mean_brier(arm, "known_mixture", "deadline_final"),
            ]
        )
    table(
        output,
        "learning_table",
        [
            "Data",
            "Mean training rows",
            "Query budget",
            "GB ID Brier",
            "GB authority OOD Brier",
            "GB final Brier",
            "Known-mixture final Brier",
        ],
        learning,
    )
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4))
    for ax, cohort, title in zip(
        axes,
        ["ID", "authority_OOD_current", "deadline_final"],
        ["ID validation", "Authority OOD: current recovery", "Locked deadline test"],
    ):
        values = [mean_brier(a, "gradient_boosting", cohort) for a in ARMS]
        ax.bar(range(5), values, color=["#6c809b", "#8aa2be", "#c45b3f", "#5d9770", "#b5b8bf"])
        ax.axhline(
            mean_brier("ordinary", "known_mixture", cohort),
            color="black",
            linestyle="--",
            label="Known mixture",
        )
        ax.set_xticks(
            range(5), ["Ord.", "Random", "Boundary", "Comb.", "Eq.rows"], rotation=35, ha="right"
        )
        ax.set(ylabel="Brier score (lower is better)", title=title)
        ax.legend(fontsize=8)
    save(fig, output, "risk_comparison")
    table(
        output,
        "final_model_table",
        ["Model", "Ordinary Brier", "Random CF Brier", "Boundary Brier", "Combined Brier"],
        [
            [name, *[mean_brier(a, name, "deadline_final") for a in ARMS[:4]]]
            for name in [
                "base_rate",
                "heuristic",
                "known_mixture",
                "logistic",
                "gradient_boosting",
                "discrete_hazard",
                "visible_only_logistic",
            ]
        ],
    )
    ctrl = [x for x in final["controller_metrics"] if x["budget_cap"] == 0.2]
    table(
        output,
        "controller_table",
        [
            "Controller",
            "Harms /2048",
            "Task completion",
            "Interventions",
            "Approval count",
            "Extra verify operations",
        ],
        [
            [
                x["method"],
                x["harms"],
                x["task_completion"],
                x["interventions"],
                x["human_approvals"],
                x["extra_verification_operations"],
            ]
            for x in ctrl
        ],
    )
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for method in ["random_budget", "authorization_rule", "authorization_timer", "learned_risk"]:
        vals = [x for x in final["controller_metrics"] if x["method"] == method]
        style = "--" if method == "learned_risk" else "-"
        axes[0].plot(
            [x["intervention_rate"] for x in vals],
            [x["harm_rate"] for x in vals],
            style,
            marker="o",
            label=method.replace("_", " "),
        )
        axes[1].plot(
            [x["intervention_rate"] for x in vals],
            [x["task_completion"] for x in vals],
            style,
            marker="o",
        )
    axes[0].set(
        xlabel="Actual suppression fraction",
        ylabel="Unauthorized harm by query horizon",
        title="Learned risk does not beat timer rule",
    )
    axes[0].legend(fontsize=8)
    axes[1].set(
        xlabel="Actual suppression fraction",
        ylabel="Task completion fraction",
        ylim=(0.75, 1.02),
        title="Random suppression sacrifices legitimate tasks",
    )
    save(fig, output, "controller_tradeoff")
    fig, ax = plt.subplots(figsize=(8.2, 4))
    x = [0, 99, 100, 1099, 1100, 1535]
    ax.step(
        x, [0, 0, 1, 1, 0, 0], where="post", label="Current authority unrecoverable", linewidth=2
    )
    ax.step(
        x,
        [0, 0, 1, 1, 1, 1],
        where="post",
        label="Historical unauthorized grant recorded",
        linestyle="--",
        linewidth=2,
    )
    for at, y in [(99, 0), (100, 1), (1099, 1), (1100, 0)]:
        ax.scatter(at, y, s=48, color="black", zorder=3)
    ax.set(
        xlabel="Prospective recovery time (logical ms)",
        ylabel="Finite contract predicate",
        ylim=(-0.08, 1.1),
        title="Current recovery is not an absorbing event",
    )
    ax.legend(fontsize=9, loc="center right")
    save(fig, output, "nonmonotone_recovery")
    finaldir = BASE / "p9-locked-confirmation-v1"
    rows = [json.loads(s) for s in (finaldir / "trials.jsonl").read_text().splitlines() if s]
    selection = dev["selected_trained_controller"]
    models = joblib.load(BASE / "p6-risk-study-v1/raw" / f"models-{selection['arm']}-0.joblib")
    predicted = models[selection["model"]].predict_proba(
        [Features.model_validate(r["features"]).vector() for r in rows]
    )[:, 1]
    y = np.array([r["outcome"] for r in rows])
    bins = []
    for index in range(10):
        mask = (predicted >= index / 10) & (
            predicted < (index + 1) / 10 if index < 9 else predicted <= 1
        )
        if mask.any():
            bins.append((float(predicted[mask].mean()), float(y[mask].mean()), int(mask.sum())))
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.plot([0, 1], [0, 1], ":", color="gray")
    ax.plot([x[0] for x in bins], [x[1] for x in bins], "o-", label="Frozen boundary GB")
    ax.set(
        xlabel="Predicted probability",
        ylabel="Observed fraction (fixed bins)",
        xlim=(-0.02, 1.02),
        ylim=(-0.02, 1.02),
        title="Locked-test calibration",
    )
    ax.legend(fontsize=9)
    save(fig, output, "calibration")
    table(output, "calibration_bins", ["Predicted", "Observed", "Rows"], bins)
    receipt = json.loads(
        (
            BASE / "p2-20261123-distinct-mechanisms-v1/raw/mock_payment_fee-7-unknown.json"
        ).read_text()
    )
    follow = receipt["receipt_followup"]
    events = [
        (follow["certificate"]["receipt_event_time"], "Capture committed", 1.2),
        (receipt["recovery_time"], "Principal refunded", -0.9),
        (receipt["observation_horizon"], "Primary observation\nUNKNOWN", 1.2),
        (follow["certificate"]["receipt_arrival_time"], "Capture receipt\narrives", -0.9),
        (follow["observation_time"], "Follow-up\nUNRECOVERABLE", 1.2),
    ]
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.axhline(0, color="#67809a")
    for at, label, height in events:
        ax.scatter(at, 0, color="#245e85", zorder=3)
        ax.annotate(
            label,
            xy=(at, 0),
            xytext=(at, height),
            ha="center",
            fontsize=9,
            arrowprops={"arrowstyle": "-", "color": "#9aabbc"},
        )
    ax.set(
        xlim=(50, 500),
        ylim=(-1.3, 1.8),
        xlabel="Logical time (ms)",
        title="Effect time and independent evidence arrival differ",
    )
    ax.set_yticks([])
    save(fig, output, "receipt_arrival")
    summary = dict(
        schema_version=1,
        H1_local_minus_coverage=search["methods"]["local_frontier"][
            "paired_auc_difference_vs_coverage"
        ],
        H2_selected=final["primary_H2_boundary_minus_random_cf_Brier"],
        H2_fixed_GB=final["model_specific_H2"]["gradient_boosting"],
        H3=final["primary_H3_learned_minus_timer_harm"],
        PG_controller=final["postgres_controller_replay"],
        visible_collision=(
            load("p7-visible-collision-v1")
            if (BASE / "p7-visible-collision-v1/metrics.json").exists()
            else None
        ),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_metrics_sha256={
            name: hashlib.sha256((BASE / name / "metrics.json").read_bytes()).hexdigest()
            for name in ["p4-matched-search-v1", "p6-risk-study-v1", "p9-locked-confirmation-v1"]
        },
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("Rendered6figures/5tables from saved evidence; no fitting, new labels or endpoint calls")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--runs-root", type=Path, default=BASE)
    args = p.parse_args()
    BASE = args.runs_root
    render(args.output)
