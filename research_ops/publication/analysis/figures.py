"""Deterministic scientific figures from compact, verified publication tables."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def load(p):
    return json.loads(p.read_text())


def table(p):
    return list(csv.DictReader(p.open()))


def generate(data, out):
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.bbox": "tight",
        }
    )
    report = load(data / "analysis/report.json")
    act = load(data.parent / "v12/controlled-actuator/report.json")

    def finish(fig, name):
        for suffix in ["png", "svg", "pdf"]:
            fig.savefig(
                out / (name + "." + suffix),
                dpi=220,
                metadata={"Creator": "AfterClick anonymous study"} if suffix == "pdf" else None,
            )
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.3, 2.65))
    ax.set(xlim=(0, 10), ylim=(0, 3))
    ax.axis("off")
    labels = [
        (0.1, 1.3, 1.6, "Actor / reviewer\npublic observations"),
        (2.3, 1.3, 1.6, "Browser / HTTP\nprotection"),
        (4.5, 1.3, 1.6, "PostgreSQL\nserialized admission"),
        (6.7, 1.3, 1.6, "Admitted ticket\nnot recalled"),
        (8.6, 1.3, 1.3, "HTTP receiver\nphysical effect"),
    ]
    for x, y, w, text in labels:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, 0.9, boxstyle="round,pad=0.08", facecolor="#e6eef4", edgecolor="#355d73"
            )
        )
        ax.text(x + w / 2, y + 0.45, text, ha="center", va="center", fontsize=8)
    for left, right in zip(labels, labels[1:]):
        ax.add_patch(
            FancyArrowPatch(
                (left[0] + left[2] + 0.05, 1.75),
                (right[0] - 0.1, 1.75),
                arrowstyle="-|>",
                mutation_scale=12,
            )
        )
    ax.text(
        5,
        0.68,
        "Evaluator-only evidence: contract obligations, durable receipts and effect history",
        ha="center",
        fontsize=10,
        color="#8c3a32",
    )
    ax.text(
        5,
        0.25,
        "Audit insertion < transaction commit < response return; receipt is a separate boundary",
        ha="center",
        fontsize=9,
    )
    finish(fig, "f1-boundaries")
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 2.9))
    for ax, (tag, c) in zip(axes, report["cohorts"].items()):
        grid = np.array([[c["L_F"][f"{local},{harm}"] for harm in [0, 1]] for local in [0, 1]])
        ax.imshow(grid, cmap="Blues", vmin=0, vmax=500)
        for (i, j), v in np.ndenumerate(grid):
            ax.text(
                j,
                i,
                str(v),
                ha="center",
                va="center",
                fontsize=16,
                color="white" if v > 260 else "#142b3b",
            )
        ax.set(
            xticks=[0, 1],
            xticklabels=["F=0", "F=1"],
            yticks=[0, 1],
            yticklabels=["L=0", "L=1"],
            title=f"{tag.title()}: {c['valid']} valid",
        )
    fig.suptitle("Current local completion L versus forbidden history F", y=1.02)
    fig.tight_layout()
    finish(fig, "f2-state-history")
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2), gridspec_kw={"width_ratios": [1.25, 1]})
    arms = [("direct_http", 0), ("browser", 0), ("browser", 300), ("browser", 1500)]
    offsets = [150, 600, 1800]
    grid = np.zeros((3, 4))
    for i, offset in enumerate(offsets):
        for j, arm in enumerate(arms):
            cell = act["cells"][str((offset, *arm))]
            grid[i, j] = cell["forbidden_history"] / cell["VALID"]
    axes[0].imshow(grid, cmap="OrRd", vmin=0, vmax=1, aspect="auto")
    for (i, j), v in np.ndenumerate(grid):
        c = act["cells"][str((offsets[i], *arms[j]))]
        label = f"{c['forbidden_history']}/{c['VALID']}" + (" +1 ?" if c.get("INVALID") else "")
        axes[0].text(
            j, i, label, ha="center", va="center", fontsize=8, color="white" if v > 0.7 else "black"
        )
    axes[0].set(
        xticks=range(4),
        xticklabels=["HTTP 0", "Browser 0", "+300 ms", "+1500 ms"],
        yticks=range(3),
        yticklabels=offsets,
        ylabel="Configured admission offset (ms)",
        title="Forbidden history / valid branches",
    )
    for i, c in enumerate(act["contrasts"]):
        ci = c["source_bootstrap95"]
        x = c["estimate"]
        axes[1].errorbar(x, i, xerr=[[x - ci[0]], [ci[1] - x]], fmt="o", color="#235675", capsize=4)
    axes[1].axvline(0, color="grey", lw=1)
    axes[1].set(
        yticks=range(3),
        yticklabels=["HTTP vs browser", "+300 ms", "+1500 ms"],
        xlabel="Source-paired change in F",
        title="10,000-draw source bootstrap",
    )
    fig.tight_layout()
    finish(fig, "f3-actuator")
    primary = load(data.parent / "v12/primary-analysis/report.json")
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.1))
    for policy, color in zip(
        ["P0", "P1", "P2", "P3"], ["#8a3d36", "#25688a", "#58834b", "#9b7130"]
    ):
        row = primary["arms"][policy + "-stress"]
        n = row["VALID"]
        x = row["legitimate_complete"] / n
        y = 1 - row["forbidden_history"] / n
        axes[0].scatter(x, y, s=65, color=color)
        axes[0].annotate(
            f"{policy} n={n}\nY={row['joint_safe_completion']}/{n}",
            (x, y),
            xytext=(6, 17) if policy == "P1" else (6, -23) if policy == "P2" else (5, 6),
            textcoords="offset points",
            fontsize=8,
        )
    axes[0].set(
        xlim=(0, 0.62),
        ylim=(0.25, 1.15),
        xlabel="Legitimate completion G / valid",
        ylabel="No forbidden history / valid",
        title="9B stress: descriptive policy rates",
    )
    debt = load(data / "checks/report.json")
    types = ["Service reopen", "Approved resubmit"]
    closed = [
        debt["discharged_by_type"]["SERVICE_REOPEN"],
        debt["discharged_by_type"]["APPROVED_REQUEST_RESUBMIT"],
    ]
    opened = [
        debt["outstanding_by_type"]["SERVICE_REOPEN"],
        debt["outstanding_by_type"]["APPROVED_REQUEST_RESUBMIT"],
    ]
    axes[1].barh(types, closed, label="Observed discharge", color="#50866b")
    axes[1].barh(types, opened, left=closed, label="Censored outstanding", color="#b77861")
    for i, (a, b) in enumerate(zip(closed, opened)):
        axes[1].text(a + b + 7, i, f"{a} / {b}", va="center", fontsize=8)
    axes[1].set(
        xlim=(0, 650),
        xlabel="Induced duties, both internal cohorts",
        title="Discharged / outstanding duties",
    )
    axes[1].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    finish(fig, "f5-obligations")
    timing = table(data / "analysis/rq4-refined-ordering.csv")
    # Fixed selection rule: lexicographically first episode, independent of elapsed magnitude.
    row = sorted(timing, key=lambda r: r["episode_key"])[0]
    base = float(row["admission_reported_mono"])
    control = float(row["protection_audit_reported_mono"]) - base
    upper = float(row["protection_commit_return_upper_mono"]) - base
    receipt = float(row["receipt_reported_mono"]) - base
    fig, ax = plt.subplots(figsize=(7.8, 2.4))
    ax.hlines(0, 0, receipt, color="#607483", lw=2)
    ax.plot(0, 0, "o", label="Admission audit")
    ax.axvspan(
        control, upper, color="#d9bd79", alpha=0.9, label="Protection: audit to return bound"
    )
    ax.plot(receipt, 0, "s", color="#b7483c", label="Persisted receipt")
    ax.set(
        ylim=(-0.5, 0.5),
        yticks=[],
        xlabel="Seconds since observed admission audit",
        title="Late receipt with pre-admitted ticket (lexicographic example)",
    )
    ax.legend(loc="upper center", ncol=1, fontsize=8)
    fig.tight_layout()
    finish(fig, "f4-forensic-interval")
    fig, axes = plt.subplots(1, 2, figsize=(8, 2.6))
    for i, (tag, c) in enumerate(report["cohorts"].items()):
        m = c["conditional_mismatch"]
        lo, hi = m["bootstrap95"]
        axes[0].errorbar(
            m["estimate"],
            i,
            xerr=[[m["estimate"] - lo], [hi - m["estimate"]]],
            fmt="o",
            capsize=4,
            color="#235675",
        )
        lo, hi = c["full_assignment_conditional_mismatch_bounds"]
        axes[0].hlines(i + 0.17, lo, hi, color="#bc7758", lw=3)
        x = next(
            x
            for x in load(data.parent / f"v12/{tag}-analysis/report.json")["contrasts"]
            if x["contrast"] == "P3-P2"
        )
        lo, hi = x["source_stratified_bootstrap95"]
        axes[1].hlines(i, lo, hi, color="#235675", lw=4)
        axes[1].plot(x["complete_pair_estimate"], i, "o", color="#235675")
        lo, hi = x["assignment_bounds"]
        axes[1].hlines(i + 0.17, lo, hi, color="#bc7758", lw=3)
    axes[0].set(
        yticks=[0, 1],
        yticklabels=["Primary", "Larger"],
        xlim=(0, 1),
        xlabel="P(F=1 | L=1)",
        title="RQ1: valid-cohort CI and missing bounds",
    )
    axes[1].set(
        yticks=[0, 1],
        yticklabels=["Primary", "Larger"],
        xlim=(-1, 1),
        xlabel="P3 minus P2 joint safe completion",
        title="Policy bundle: CI and missing bounds",
    )
    axes[1].axvline(0, color="grey", lw=1)
    for ax in axes:
        ax.text(
            0.02,
            -0.47,
            "Blue: complete observed data; orange: full-assignment unknown bounds",
            transform=ax.transAxes,
            fontsize=7,
        )
    fig.tight_layout()
    finish(fig, "f6-uncertainty")
    # Per-case time-indexed forensic atlas, with original read/commit boundary left unknown.
    atlas = out / "forensic-atlas"
    atlas.mkdir(exist_ok=True)
    for r in timing:
        a = float(r["admission_reported_mono"])
        c = float(r["protection_audit_reported_mono"]) - a
        u = float(r["protection_commit_return_upper_mono"]) - a
        p = float(r["receipt_reported_mono"]) - a
        fig, ax = plt.subplots(figsize=(7, 1.8))
        ax.hlines(0, 0, p, color="#556b7d")
        ax.plot(0, 0, "o")
        ax.axvspan(c, u, color="#d9bd79")
        ax.plot(p, 0, "s", color="#b7483c")

        ax.set(yticks=[], ylim=(-1, 1), xlabel="Seconds since admission audit")
        ax.set_title(r["episode_key"], fontsize=6)
        fig.tight_layout()
        fig.savefig(atlas / (r["episode_key"].replace(":", "--") + ".svg"))
        plt.close(fig)
    (out / "sources.json").write_text(
        json.dumps(
            dict(
                data_root=str(data),
                figures=[
                    "f1-boundaries",
                    "f2-state-history",
                    "f3-actuator",
                    "f5-obligations",
                    "f4-forensic-interval",
                    "f6-uncertainty",
                ],
                forensic_case_selection="lexicographic first; all34 available in atlas",
                provider_calls=0,
                model_calls=0,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    generate(a.data, a.output)
