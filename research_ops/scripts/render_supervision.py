"""Render source outcomes and measured role latency from saved supervision analysis."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def render(data, output):
    output.mkdir(parents=True, exist_ok=False)
    v = json.loads(data.read_text())
    arms = ["C1", "C2", "C3"]
    x = np.arange(3)
    width = 0.24
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout="constrained")
    for j, (k, label, color) in enumerate(
        [
            ("safe", "Safe completion", "#226b89"),
            ("legitimate", "Legitimate completion", "#869eaf"),
            ("harm", "Forbidden effect", "#bd634d"),
        ]
    ):
        vals = [v["arms"][a][k] for a in arms]
        axes[0].bar(x + (j - 1) * width, vals, width, label=label, color=color)
    axes[0].set(
        xticks=x,
        xticklabels=arms,
        ylabel="Independent source count",
        ylim=(0, v["planned_sources"] + 0.45),
        yticks=range(v["planned_sources"] + 1),
    )
    axes[0].legend(fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.18), ncol=1, frameon=False)
    for j, (key, label, color) in enumerate(
        [
            ("actor_model_serving_seconds", "Actor HTTP serving", "#226b89"),
            ("supervisor_model_serving_seconds", "Supervisor HTTP serving", "#cc9b42"),
        ]
    ):
        values = [
            np.mean([r[key] for r in v["records"] if r["arm"] == a and r["status"] == "valid"])
            for a in arms
        ]
        axes[1].bar(x + (j - 0.5) * 0.3, values, 0.3, label=label, color=color)
    axes[1].set(xticks=x, xticklabels=arms, ylabel="HTTP serving seconds / branch")
    axes[1].legend(fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.18), frameon=False)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
    fig.suptitle(
        f"Independent supervision: {v['planned_sources']} source instances (paired branches)",
        fontsize=12,
    )
    fig.savefig(
        output / "supervision-outcomes.png",
        dpi=180,
        metadata={"Software": "AfterClick saved-evidence renderer"},
    )
    plt.close(fig)


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--data", type=Path, required=True)
    a.add_argument("--output", type=Path, required=True)
    v = a.parse_args()
    render(v.data, v.output)
