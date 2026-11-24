"""Regenerate static manuscript figures from saved SQL-oracle summary only."""

import argparse
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

plt.switch_backend("Agg")
matplotlib.rcParams["svg.hashsalt"] = "afterclick-oecr-v1"


def plot(summary, output):
    output.mkdir(parents=True, exist_ok=True)
    s = json.loads(summary.read_text())
    arms = ["source", "faithful", "fresh"]
    data = s["summary"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    labels = ["Original", "Faithful", "Fresh (invalid sibling)"]
    colors = ["#555555", "#167568", "#c96d32"]
    for index, metric in enumerate(["causal_valid", "task_success"]):
        vals = [data[a][metric] for a in arms]
        ns = [data[a]["attempted"] for a in arms]
        ax[index].bar(labels, vals, color=colors, width=0.6)
        for x, (v, n) in enumerate(zip(vals, ns)):
            ax[index].text(x, v + 0.1, f"{v}/{n}", ha="center")
        ax[index].set_ylim(0, max(ns) + 1)
        ax[index].set_ylabel("Completed continuations")
        ax[index].set_title(
            "Exact reconstruction" if index == 0 else "Original-target task completion"
        )
        ax[index].tick_params(axis="x", rotation=12)
    fig.suptitle(
        "One application; two task templates. Fresh outcomes are diagnostic, not efficacy."
    )
    fig.savefig(output / "oecr-counts.png", dpi=180)
    fig.savefig(output / "oecr-counts.svg", metadata={"Date": None})
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
    metrics = ["first_action_disagrees", "terminal_content_disagrees", "task_success_disagrees"]
    for offset, arm in [(-0.16, "faithful"), (0.16, "fresh")]:
        ax.bar(
            [i + offset for i in range(3)],
            [data[arm][m]["k"] for m in metrics],
            width=0.3,
            label=arm,
        )
    ax.set_xticks(range(3), ["First action", "Final content", "Task completion"])
    ax.set_ylabel(f"Disagreements with original / {s['complete_source_groups']} source groups")
    ax.set_ylim(0, s["complete_source_groups"] + 1)
    ax.legend()
    ax.set_title("Source-paired diagnostic disagreement")
    fig.savefig(output / "oecr-disagreement.png", dpi=180)
    fig.savefig(output / "oecr-disagreement.svg", metadata={"Date": None})
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    plot(a.summary, a.output)
