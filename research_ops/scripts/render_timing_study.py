"""Generate publication plots only from saved source-level timing analysis."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from afterclick.agent.modal_policy import atomic_json
from afterclick.model_sprint.records import sha


def render(data_path, out):
    d = json.loads(data_path.read_text())
    out.mkdir(parents=True, exist_ok=True)
    arms = ["immediate", "verify_first", "post_action"]
    labels = ["Immediate protection", "Verification-first", "Delayed containment"]
    colors = ["#277c75", "#b05c2e", "#686b80"]
    n = d["planned_sources"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), layout="constrained")
    for i, (arm, label, color) in enumerate(zip(arms, labels, colors)):
        a = d["arms"][arm]
        v = a["valid"]
        rate = a["safe"] / v if v else 0
        lo, hi = a["safe_rate_interval"]
        axes[0].bar(i, rate, color=color)
        if v:
            axes[0].errorbar(
                i, rate, yerr=[[rate - lo], [hi - rate]], fmt="none", ecolor="#222", capsize=4
            )
        axes[0].text(i, 0.04, f"{a['safe']}/{v}", ha="center", color="white", fontweight="bold")
        axes[1].bar(i - 0.17, a["legitimate"] / v if v else 0, width=0.32, color=color)
        axes[1].bar(
            i + 0.17,
            a["harm"] / a["attempted"] if a["attempted"] else 0,
            width=0.32,
            color=color,
            alpha=0.4,
            hatch="//",
        )
    for ax in axes:
        ax.set(
            ylim=(0, 1.15),
            xticks=range(3),
            xticklabels=["Immediate", "Verify-first", "Delayed"],
            ylabel="Source-level fraction",
        )
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_title("Safe task completion (95% binomial intervals)")
    axes[1].set_title("Legitimate completion / forbidden effect")
    axes[1].text(
        0.5,
        0.96,
        "Solid: legitimate completion; hatched: forbidden effect",
        transform=axes[1].transAxes,
        ha="center",
        fontsize=8,
    )
    fig.suptitle(
        f"Frozen cohort: {n} sources, three mock mechanisms; sibling arms paired", fontsize=11
    )
    fig.savefig(out / "live-confirmation.png", dpi=180)
    plt.close(fig)
    # All prohibited sources, rather than selecting a favorable example.
    records = [r for r in d["records"] if not r["authorized"]]
    sources = sorted({r["source_id"] for r in records})
    fig, ax = plt.subplots(figsize=(8, max(3, len(sources) * 0.55)), layout="constrained")
    markers = ["o", "^", "s"]
    for j, arm in enumerate(arms):
        for i, s in enumerate(sources):
            r = next((r for r in records if r["source_id"] == s and r["arm"] == arm), None)
            if r and r["first_protective_command_ms"] is not None:
                delta = (r["first_protective_command_ms"] - r["prevention_deadline_ms"]) / 1000
                ax.scatter(
                    delta,
                    i + (j - 1) * 0.15,
                    color=colors[j],
                    marker=markers[j],
                    label=labels[j] if i == 0 else None,
                )
    ax.axvline(0, color="#333", linestyle="--", linewidth=1)
    ax.set(
        yticks=range(len(sources)),
        yticklabels=sources,
        xlabel="First actual cancel/revoke command minus scheduled eligibility (s)",
        title="All prohibited source instances; negative = command before deadline",
    )
    ax.legend(fontsize=8, loc="best")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(out / "live-deadline-margins.png", dpi=180)
    plt.close(fig)
    atomic_json(
        out / "provenance.json",
        dict(
            schema_version=1,
            input=str(data_path),
            input_sha256=sha(data_path),
            planned_sources=n,
            renderer="research_ops/scripts/render_timing_study.py",
            renderer_sha256=sha(__file__),
            figures={p.name: sha(p) for p in sorted(out.glob("*.png"))},
            uncertainty=(
                "Binomial working-model intervals conditional on authored source "
                "cohort; not cross-application population coverage. Paired "
                "contrasts are in numerical analysis."
            ),
        ),
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    render(a.data, a.output)
