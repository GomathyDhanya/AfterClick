"""Rebuild vector PDF / 300-dpi PNG figures only from executed audit outputs."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from analyze import HERE, dump, read, sha, table
from enrich import loadcsv

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
    }
)
BLUE, RED, GREEN, GRAY = "#256b9b", "#bc4149", "#27856a", "#8d98a2"
OUT = HERE / "figures"
MANIFEST = []


def save(fig, name, sources, caption):
    fig.savefig(OUT / (name + ".pdf"), bbox_inches="tight")
    fig.savefig(OUT / (name + ".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    MANIFEST.append(
        dict(
            figure=name,
            caption=caption,
            plotting_script="plot.py",
            plotting_script_sha256=sha(Path(__file__)),
            inputs={str(p.relative_to(HERE)): sha(p) for p in sources},
            pdf_sha256=sha(OUT / (name + ".pdf")),
            png_sha256=sha(OUT / (name + ".png")),
        )
    )


def main():
    OUT.mkdir(exist_ok=True)
    report = read(HERE / "report.json")
    timing = [r for r in loadcsv("episode_timing.csv") if r["eligible_prohibited"]]
    decisions = [r for r in loadcsv("decision_opportunities.csv") if not r["pending_allowed"]]
    funnel = report["funnel"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1.35, 1]})
    labels = [
        "All valid P0 stress",
        "Prohibited pending",
        "Sufficient raw evidence",
        "Observable authority",
        "Observation handoff before admission",
        "Actionable response before admission",
        "Business commit before admission",
    ]
    keys = [
        "all_valid_P0_stress",
        "prohibited_pending_requests",
        "sufficient_raw_evidence",
        "observable_authorization",
        "observation_opportunity",
        "response_opportunity",
        "demonstrated_execution_opportunity",
    ]
    vals = [funnel[k] for k in keys]
    axes[0].barh(range(len(labels)), vals, color=[GRAY] + [BLUE] * 6)
    axes[0].set_yticks(range(len(labels)), labels)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 240)
    for i, v in enumerate(vals):
        axes[0].text(v + 3, i, str(v), va="center")
    axes[0].set_xlabel("Executed episodes")
    labs = [
        "Ever proposed protection",
        "Dispatched protection",
        "Committed before admission",
        "Joint safe completion",
    ]
    vals2 = [
        funnel[k]
        for k in [
            "protective_proposal",
            "protective_dispatch",
            "timely_protection",
            "safe_completion",
        ]
    ]
    axes[1].barh(range(4), vals2, color=[RED, RED, GREEN, GREEN])
    axes[1].set_yticks(range(4), labs)
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, 2)
    for i, v in enumerate(vals2):
        axes[1].text(v + 0.04, i, str(v), va="center")
    axes[1].set_xlabel("Of 137 eligible episodes")
    fig.suptitle("Opportunity and protection are separate, overlapping summaries")
    fig.tight_layout()
    table(
        OUT / "01_enrollment_source.csv",
        [dict(group="enrollment/opportunity", category=k, n=funnel[k]) for k in keys]
        + [
            dict(group="protection", category=k, n=funnel[k])
            for k in [
                "protective_proposal",
                "protective_dispatch",
                "timely_protection",
                "safe_completion",
            ]
        ],
    )
    save(
        fig,
        "01_enrollment",
        [OUT / "01_enrollment_source.csv"],
        "Observed opportunities are retrospective bounds. Branches overlap; proposal counts are not a nested continuation of the execution subset.",  # noqa: E501
    )

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2))
    source = []
    for panel, rows, xkey in [
        (0, timing, "first_response_relative_s"),
        (1, decisions, "response_relative_s"),
    ]:
        x = np.array([float(r[xkey]) for r in rows])
        y = np.array([float(r["admission_relative_s"]) for r in rows])
        prop = np.array([r["protective_proposal"] for r in rows])
        axes[panel].scatter(
            x[~prop],
            y[~prop],
            s=14,
            color=BLUE,
            alpha=0.45,
            label="Other response" if panel else "No protection proposed in episode",
        )
        axes[panel].scatter(
            x[prop],
            y[prop],
            s=65,
            color=RED,
            marker="X",
            label="Protective proposal" if panel else "Episode with a later proposal",
            zorder=4,
        )
        limit = max(x.max(), y.max()) * 1.05
        diagonal = np.linspace(0, limit, 4000)
        axes[panel].plot(diagonal, diagonal, "--", color="black", lw=1)
        axes[panel].set_xlim(-0.1, limit)
        axes[panel].set_ylim(-0.1, y.max() * 1.15)
        axes[panel].set_xlabel("Actor response marker − environment start (s)")
        axes[panel].set_ylabel("Observed admission marker − environment start (s)")
        axes[panel].set_title(
            f"{'First response' if panel == 0 else 'Every response'} (n={len(rows)})"
        )
        axes[panel].legend(fontsize=8, loc="upper right")
        for r in rows:
            source.append(
                dict(
                    panel=panel,
                    episode_key=r["episode_key"],
                    request_id=r.get("request_id"),
                    response_s=r[xkey],
                    admission_s=r["admission_relative_s"],
                    protective_proposal=r["protective_proposal"],
                )
            )
    axes[1].set_xscale("symlog", linthresh=1)
    fig.tight_layout()
    table(OUT / "02_admission_response_source.csv", source)
    save(
        fig,
        "02_admission_response",
        [OUT / "02_admission_response_source.csv"],
        "All observations retained. Right panel uses a symmetric log x scale to show long trajectories; diagonal is equality in seconds. Left red mark identifies the episode with a later proposal, not a protective first response.",  # noqa: E501
    )

    cats = [
        "NO_PROPOSAL",
        "REJECTED_PROPOSAL",
        "SKIPPED_PROPOSAL",
        "LATE_DISPATCH",
        "TIMELY_PROTECTION",
        "UNKNOWN",
    ]
    colors = [GRAY, "#e59b35", "#9b64a1", RED, GREEN, "#343e48"]
    counts = [report["failure_attribution"].get(k, 0) for k in cats]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.0), gridspec_kw={"width_ratios": [1.1, 1]})
    left = 0
    for cat, n, color in zip(cats, counts, colors):
        axes[0].barh(0, n, left=left, color=color, label=cat.replace("_", " ").title())
        left += n
    axes[0].set_xlim(0, 137)
    axes[0].set_yticks([0], ["Eligible P0"])
    axes[0].set_xlabel("Episodes")
    axes[1].axis("off")
    axes[1].text(
        0,
        1,
        "\n".join(f"{k.replace('_', ' ').title()}: {v}/137" for k, v in zip(cats, counts)),
        transform=axes[1].transAxes,
        va="top",
        linespacing=1.55,
    )
    fig.suptitle("Historical proposal attribution: batch-abort losses = 0")
    fig.tight_layout()
    table(OUT / "03_outcomes_source.csv", [dict(category=k, n=v) for k, v in zip(cats, counts)])
    save(
        fig,
        "03_protection_outcomes",
        [OUT / "03_outcomes_source.csv", HERE / "failure_attribution.csv"],
        "A successful late suspension transaction does not undo an admitted pending effect. No proposal is distinct from a rejected/skipped proposal.",  # noqa: E501
    )

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    regimes = ["tight", "intermediate", "generous"]
    for panel, key, title in [
        (0, "first_queue_duration_s", "Infrastructure semaphore queue"),
        (1, "first_http_request_interval_s", "HTTP request interval"),
    ]:
        data = [[float(t[key]) for t in timing if t["timing_regime"] == r] for r in regimes]
        axes[panel].boxplot(
            data, tick_labels=[f"{r}\nn={len(x)}" for r, x in zip(regimes, data)], showfliers=True
        )
        axes[panel].set_yscale("symlog", linthresh=0.01)
        axes[panel].set_ylabel("Seconds (symlog)")
        axes[panel].set_title(title)
    slack = np.array(
        [float(t["admission_mono"]) - float(t["first_response_end_mono"]) for t in timing]
    )
    axes[2].hist(slack, bins=22, color=BLUE, edgecolor="white")
    axes[2].axvline(0, color=RED, ls="--")
    axes[2].set_xlabel("Admission marker − first response (s)")
    axes[2].set_ylabel("Episodes")
    axes[2].set_title("Negative: response already late")
    fig.tight_layout()
    source = [
        {
            k: t[k]
            for k in [
                "episode_key",
                "timing_regime",
                "first_queue_duration_s",
                "first_http_request_interval_s",
                "first_response_end_mono",
                "admission_mono",
                "admission_during_queue",
            ]
        }
        for t in timing
    ]
    table(OUT / "04_latency_source.csv", source)
    save(
        fig,
        "04_queue_http_intervals",
        [OUT / "04_latency_source.csv"],
        "HTTP interval includes transport and provider serving/queueing; it is not pure neural inference latency. Queueing crosses admission in five episodes.",  # noqa: E501
    )

    trajectories = read(OUT / "trajectory_source.json")
    fig, axes = plt.subplots(len(trajectories), 1, figsize=(11, 1.85 * len(trajectories)))
    style = {
        "response": (BLUE, "o"),
        "pending admitted": (RED, "X"),
        "pending blocked": (GREEN, "X"),
        "protection command": (GREEN, "s"),
        "other service command": (GRAY, "."),
        "pending receipt": ("#e59b35", "D"),
        "business receipt": ("#a68d63", "d"),
        "business commit audit": (GRAY, "|"),
        "schema rejection": ("#9b64a1", "^"),
    }
    for ax, case in zip(axes, trajectories):

        def event_label(x):
            event = x["event"]
            payload = x.get("payload", {})
            if event == "pending.admission_snapshot":
                return "pending admitted" if payload["admitted"] else "pending blocked"
            if event == "control.command":
                return (
                    "protection command"
                    if payload["command"] in {"Suspend pending service", "Cancel pending service"}
                    else "other service command"
                )
            if event == "receiver.committed":
                return (
                    "pending receipt"
                    if payload.get("receipt_id") == "pending"
                    else "business receipt"
                )
            if event in {"flow.task_committed", "ops.work_order_committed"}:
                return "business commit audit"
            return event

        for event, (color, marker) in style.items():
            stamps = [x["time_s"] for x in case["timeline"] if event_label(x) == event]
            if stamps:
                ax.scatter(stamps, [0] * len(stamps), color=color, marker=marker, s=40, label=event)
        ax.set_yticks([])
        ax.set_title(
            case["label"].replace("_", " ") + "\n" + case["episode_key"], fontsize=8, loc="left"
        )
        ax.set_xlabel("Seconds from environment start")
        ax.set_xscale("symlog", linthresh=1)
        if max(x["time_s"] for x in case["timeline"]) < 12:
            ax.set_xscale("linear")
            ax.set_xlim(left=0)
        ax.set_ylim(-0.5, 0.5)
    legend = {}
    for ax in axes:
        handles, labels = ax.get_legend_handles_labels()
        legend.update(zip(labels, handles))
    fig.legend(list(legend.values()), list(legend), loc="lower center", ncol=4, fontsize=8)
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    save(
        fig,
        "05_recorded_trajectories",
        [OUT / "trajectory_source.json"],
        "Cases selected by explicit rules in enrich.py and supplementary.py, including a safe actually executed P1 sibling. A sibling is not a P0 mid-trajectory counterfactual. Times are audit/response markers, not exact commits.",  # noqa: E501
    )

    uncertainty = loadcsv("uncertainty.csv")
    metrics = ["protective_proposal", "protective_dispatch", "protective_proposal_before_admission"]
    subsets = ["full_eligible", "response_opportunity", "demonstrated_execution_opportunity"]
    labels = [
        "Full eligible\nn=137",
        "Actionable response\nbefore admission, n=62",
        "Business commit\nbefore admission, n=60",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    for j, (metric, color) in enumerate(zip(metrics, [BLUE, RED, GREEN])):
        rows = [
            next(x for x in uncertainty if x["subset"] == s and x["metric"] == metric)
            for s in subsets
        ]
        points = np.array([float(r["point"]) * 100 for r in rows])
        low = np.array([float(r["lower"]) * 100 for r in rows])
        hi = np.array([float(r["upper"]) * 100 for r in rows])
        pos = np.arange(3) + (j - 1) * 0.18
        axes[0].errorbar(
            pos,
            points,
            yerr=[points - low, hi - points],
            fmt="o",
            color=color,
            capsize=3,
            label=metric.replace("protective_", "").replace("_", " "),
        )
    axes[0].set_xticks(range(3), labels, fontsize=8)
    axes[0].set_ylabel("Episodes (%)")
    axes[0].set_ylim(-0.4, 9)
    axes[0].legend(fontsize=8)
    sensitivity = read(HERE / "sensitivity.json")
    for name, color in [("response", BLUE), ("execution", GREEN)]:
        rows = [r for r in sensitivity if r["opportunity"] == name]
        axes[1].plot(
            [r["margin_ms"] for r in rows],
            [r["n"] for r in rows],
            "o-",
            color=color,
            label=name + " opportunity",
        )
    axes[1].set_xlabel("Required headroom before admission marker (ms)")
    axes[1].set_ylabel("Eligible episodes")
    axes[1].legend(fontsize=8)
    axes[1].set_ylim(0, 70)
    fig.tight_layout()
    table(
        OUT / "06_rates_source.csv",
        [r for r in uncertainty if r["metric"] in metrics and r["subset"] in subsets],
    )
    save(
        fig,
        "06_opportunity_conditioned_rates",
        [OUT / "06_rates_source.csv", HERE / "sensitivity.json"],
        "95% task-cluster percentile bootstrap intervals. Ever-proposed and ever-dispatched protection are distinct from proposals before admission (zero). Degenerate bootstrap intervals do not bound unseen tasks. Margins are sensitivity assumptions, not known historical enforcement delays.",  # noqa: E501
    )

    clustering = read(HERE / "clustering.json")
    loadcsv("action_sequences.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1, 1.5]})
    sizes = [clustering["empty_sequences"]] + [r["n"] for r in clustering["clusters"]]
    labs = ["No pre-admission response"] + [
        f"Sequence shape {r['cluster']}" for r in clustering["clusters"]
    ]
    axes[0].barh(labs, sizes, color=[GRAY] + [BLUE] * len(clustering["clusters"]))
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Episodes")
    axes[1].axis("off")
    text = "Exploratory normalized edit distance\n" + "\n".join(
        f"Shape {r['cluster']}: " + " → ".join(r["medoid_sequence"]) for r in clustering["clusters"]
    )
    import textwrap

    axes[1].text(
        0,
        1,
        "\n".join(textwrap.fill(line, 65) for line in text.splitlines()),
        va="top",
        transform=axes[1].transAxes,
        fontsize=9,
    )
    fig.suptitle("Sequence shapes do not identify protection-failure mechanisms", fontsize=12)
    fig.tight_layout()
    save(
        fig,
        "07_exploratory_sequence_shapes",
        [HERE / "action_sequences.csv", HERE / "clustering.json"],
        "Average-linkage normalized Levenshtein clustering, k=2–5 silhouette comparison; task-subsample ARI stability reported in clustering.json. Small clusters and timing/length confounding preclude mechanistic interpretation.",  # noqa: E501
    )

    controls = loadcsv("control_conditions.csv")
    fig, ax = plt.subplots(figsize=(10, 3.8))
    x = np.arange(len(controls))
    ax.bar(
        x - 0.18,
        [int(r["protective_transactions"]) for r in controls],
        width=0.36,
        color=GREEN,
        label="Protection transaction",
    )
    ax.bar(
        x + 0.18,
        [int(r["receipts"]) for r in controls],
        width=0.36,
        color=RED,
        label="Unauthorized pending receipt",
    )
    ax.set_xticks(x, [r["condition"] for r in controls])
    ax.set_xlabel("Scripted condition (A–J); eight valid trials per condition")
    ax.set_ylabel("Trials")
    ax.set_ylim(0, 9.7)
    ax.legend(ncol=2, fontsize=9)
    ax.set_title("Native actor-path controls: E produced seven conflicts and one non-conflict")
    fig.tight_layout()
    save(
        fig,
        "08_scripted_controls",
        [HERE / "control_conditions.csv"],
        "Primary A–J: 83 attempts, 80 technically valid trials; three invalid setup-deadline attempts preserved. One E trial did not induce the intended version conflict and remains valid. Controls use real PostgreSQL, browser, HTTP worker and receiver paths.",  # noqa: E501
    )
    dump(OUT / "provenance.json", MANIFEST)
    (OUT / "README.md").write_text(
        "# Executed audit figures\n\nEvery figure is available as vector PDF and 300-dpi PNG. Rebuild with `../REPRODUCE.sh --plots-only` or `python plot.py`. `provenance.json` binds each figure to its source data and plotting-script hashes.\n\n"  # noqa: E501
        + "\n\n".join(f"**{r['figure']}** — {r['caption']}" for r in MANIFEST)
        + "\n"
    )


if __name__ == "__main__":
    main()
