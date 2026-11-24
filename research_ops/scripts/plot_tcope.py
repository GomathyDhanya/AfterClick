"""Generate standalone figures only from archived native-policy evidence."""

import argparse
import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from afterclick.tcope.workload_specs import workload_suite


def architecture(output):
    fig, ax = plt.subplots(figsize=(13, 4.8), layout="constrained")
    ax.set(xlim=(0, 13), ylim=(0, 5))
    ax.axis("off")
    boxes = [
        (0.2, 3.3, 2.3, 1.1, "Natural instruction\n+ public browser state"),
        (3.1, 3.3, 2.5, 1.1, "Frozen 9B policy\nNative call + tool ID"),
        (6.3, 3.3, 2.6, 1.1, "Public-only controller\nProtect / compute / act"),
        (9.6, 3.3, 3.0, 1.1, "Real Gateway + main world\nBackground jobs keep running"),
        (
            6.3,
            0.7,
            2.6,
            1.3,
            "Independent-belief forecasts\nNEW live model suffixes\nNo actual hidden schedule",
        ),
        (
            9.6,
            0.7,
            3.0,
            1.3,
            "Immutable fake HTTP receipts\nIndependent offline oracle\nNo oracle → selector feedback",
        ),
    ]
    for x, y, w, h, label in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h, boxstyle="round,pad=.08", facecolor="#e9f1f8", edgecolor="#315b7d"
            )
        )
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10)
    for start, end in [
        ((2.6, 3.85), (3.0, 3.85)),
        ((5.7, 3.85), (6.2, 3.85)),
        ((9.0, 3.85), (9.5, 3.85)),
        ((7.6, 3.2), (7.6, 2.1)),
        ((8.95, 1.35), (9.5, 1.35)),
        ((11.1, 3.2), (11.1, 2.1)),
    ]:
        ax.annotate(
            "", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=1.6, color="#315b7d")
        )
    ax.annotate(
        "public summary",
        xy=(8.4, 3.2),
        xytext=(8.4, 2.15),
        arrowprops=dict(arrowstyle="->", color="#315b7d"),
        ha="center",
        fontsize=8,
    )
    ax.text(
        0.25,
        1.8,
        "Exact evaluator clones copy application/jobs/observer/browser/conversation.\nOnline forecasts instead sample a public prior.\nPrimary policies are compared at matched actual source checkpoints.",
        fontsize=10,
        va="top",
    )
    fig.savefig(output / "architecture.png", dpi=180)
    fig.savefig(output / "architecture.svg")
    plt.close(fig)


def plot(runs, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    architecture(output)
    sources = []
    overheads = []
    for run in map(Path, runs):
        protocol = json.loads((run / "protocol.json").read_text())
        spec = next(
            t for t in workload_suite(protocol["partition"]) if t.case_id == protocol["case_id"]
        )
        rows = [json.loads(line) for line in (run / "trials.jsonl").read_text().splitlines()]
        primary = [r for r in rows if r.get("role") == "primary_controller"]
        if spec.service_goal in {"cancel", "restore_access"}:
            sources.append((run, spec, primary))
        ends = {
            r["request_id"]: r
            for r in [
                json.loads(line) for line in (run / "model_calls.jsonl").read_text().splitlines()
            ]
            if r["event"] == "finished"
        }
        for path in (run / "raw").glob("*/controller/decision-*/forecast-*/public-summary.json"):
            report = path.parent / "continuation/report.json"
            if not report.exists():
                continue
            summary = json.loads(path.read_text())
            data = json.loads(report.read_text())
            ids = data.get("model_request_ids")
            if ids is None:
                continue  # No fabricated per-conversation allocation for old engines.
            inference = sum(ends[key].get("latency_ms", 0) for key in ids if key in ends) / 1000
            elapsed = summary["elapsed_ms"] / 1000
            overheads.append(
                dict(
                    run=run.name,
                    arm=path.relative_to(run / "raw").parts[0],
                    forecast=str(path),
                    public_summary_seconds=elapsed,
                    inference_seconds=inference,
                    other_construction_browser_tools_seconds=max(0, elapsed - inference),
                )
            )
    (output / "forecast-overhead-data.json").write_text(json.dumps(overheads, indent=2) + "\n")
    if overheads:
        fig, ax = plt.subplots(figsize=(11, 4.8), layout="constrained")
        x = range(len(overheads))
        ax.bar(
            x,
            [r["inference_seconds"] for r in overheads],
            label="Actual HTTP inference latency",
            color="#27648e",
        )
        ax.bar(
            x,
            [r["other_construction_browser_tools_seconds"] for r in overheads],
            bottom=[r["inference_seconds"] for r in overheads],
            label="World construction / browser / tools / scheduling",
            color="#db9c45",
        )
        ax.set(
            xlabel="Individual live public-belief forecast", ylabel="Seconds until public summary"
        )
        ax.legend(fontsize=8)
        fig.savefig(output / "forecast-overhead.png", dpi=180)
        plt.close(fig)
    if sources:
        fig, axes = plt.subplots(
            len(sources), 1, figsize=(12, 2.8 * len(sources)), layout="constrained", squeeze=False
        )
        for ax, (run, spec, rows) in zip(axes[:, 0], sources):
            source = json.loads((run / "checkpoints/source.json").read_text())
            scheduled = source["world"]["tc_runtime"][0]["state"]["deadline"] / 1000
            start = source["world"]["tc_runtime"][0]["clock_ms"] / 1000
            labels = []
            for index, row in enumerate(rows):
                path = run / "raw" / row["arm"] / "world/report.json"
                if not path.exists():
                    continue
                data = json.loads(path.read_text())
                state = data["state"]
                stop = data.get("agent_stop_state", state)["tc_runtime"][0]["clock_ms"] / 1000
                labels.append(row["arm"] + (" [censored]" if row["censored"] else ""))
                ax.plot([start, stop], [index, index], color="#8293a0", lw=2)
                for event in state["tc_events"]:
                    if event["kind"] in {
                        "command.cancel_notice",
                        "command.cancel_resource",
                        "command.revoke_access",
                    }:
                        ax.scatter(
                            event["ms"] / 1000, index, color="#26834b", marker="v", s=55, zorder=4
                        )
                    if event["kind"] in {"dispatch.issued", "access.ticket_snapshot"}:
                        ax.scatter(
                            event["ms"] / 1000, index, color="#7153a4", marker="|", s=160, zorder=4
                        )
                for receipt in state["tc_receipts"]:
                    ax.scatter(
                        receipt["ms"] / 1000, index, color="#c33e45", marker="x", s=65, zorder=5
                    )
            ax.axvline(scheduled, color="#5c5c5c", linestyle="--", label="Scheduled eligibility D")
            ax.set(
                yticks=range(len(labels)),
                yticklabels=labels,
                xlabel="Actual branch clock (seconds)",
                title=spec.case_id + " / " + spec.family,
            )
        axes[0, 0].text(
            0.01,
            1.14,
            "▼ protective command    | actual dispatch/ticket event    × independent receipt    — agent-active interval; dashed D is a schedule, not an exact physical frontier",
            transform=axes[0, 0].transAxes,
            fontsize=8,
        )
        fig.savefig(output / "timelines.png", dpi=180)
        plt.close(fig)
    print(output)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs", nargs="+", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    plot(a.runs, a.output)
