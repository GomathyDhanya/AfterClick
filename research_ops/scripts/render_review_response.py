"""Regenerate reviewer-response numerical figures from archived derived/official metrics."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    base = Path("artifacts/research_runs")
    out = Path("paper/review-generated")
    out.mkdir(exist_ok=True)
    metrics = json.loads((base / "w0d-recovery-predicates-v2-1/metrics.json").read_text())
    comparisons = metrics["comparisons"]
    keys = [
        "local_rollback_success__vs__current_state_recoverable",
        "local_rollback_success__vs__full_history_contract_recoverable",
        "current_state_recoverable__vs__full_history_contract_recoverable",
    ]
    fig, ax = plt.subplots(figsize=(7, 2.6), layout="constrained")
    ax.bar(
        range(3),
        [comparisons[k]["disagree"] for k in keys],
        color=["#537f93", "#2c7869", "#c28648"],
    )
    ax.set(
        xticks=range(3),
        xticklabels=["Local / current", "Local / full history", "Current / full history"],
        ylabel="Disagreements / 78 determinate cases",
        title="Preserved authored fixtures; 24 unknown/censored excluded from binary scores",
    )
    fig.savefig(out / "predicate-disagreement.png", dpi=180)
    plt.close(fig)
    ranking = json.loads(
        (base / "w2-undobench-official-local-v1/raw/scoring-ranking.json").read_text()
    )
    names = list(ranking)
    labels = [n.replace("official-dev-", "") for n in names]
    fig, ax = plt.subplots(figsize=(7, 2.8), layout="constrained")
    for shift, field, label in [
        (-0.17, "local_state_success", "Local state"),
        (0.17, "official_history_aware_success", "Official full oracle"),
    ]:
        ax.bar(
            [i + shift for i in range(len(names))],
            [ranking[n][field] for n in names],
            width=0.32,
            label=label,
        )
    ax.set(
        xticks=range(len(names)),
        xticklabels=labels,
        ylabel="FAULT successes / 10 paired instances",
        title="Unmodified UndoBench DEV; official scripted agent, no new LLM calls",
    )
    ax.legend(fontsize=8)
    fig.savefig(out / "official-metric-ranking.png", dpi=180)
    plt.close(fig)
    (out / "provenance.json").write_text(
        json.dumps(
            dict(
                schema_version=1,
                predicate_input="w0d-recovery-predicates-v2-1/metrics.json",
                external_input="w2-undobench-official-local-v1/raw/scoring-ranking.json",
                model_calls=0,
                independent_units=(
                    "Same fixture/source clusters retained; not independent rows or new model tasks"
                ),
                semantic_version="v2.1",
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
