# ruff: noqa: E501
"""Offline publication figures and evidence-linked trajectory atlas.

Rendering only: frozen outcomes/estimators are read without modification.
"""

import argparse
import collections
import html
import json
from pathlib import Path


def read(p):
    return json.loads(Path(p).read_text())


def figures(analysis, actuator, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.bbox": "tight",
        }
    )
    report = read(actuator)
    labels = ["Direct HTTP", "Browser +300 ms", "Browser +1500 ms"]
    estimates = [c["estimate"] * 100 for c in report["contrasts"]]
    cis = np.array([c["source_bootstrap95"] for c in report["contrasts"]]) * 100
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    x = np.arange(3)
    ax.errorbar(
        estimates, x, xerr=np.array(estimates) - cis[:, 0], fmt="none", color="#245581", capsize=4
    )
    # Draw asymmetric intervals explicitly (errorbar above is left only).
    ax.clear()
    ax.hlines(x, cis[:, 0], cis[:, 1], color="#245581", lw=2)
    ax.scatter(estimates, x, color="#245581", s=35, zorder=3)
    ax.axvline(0, color="#aaa", lw=0.8)
    ax.set_yticks(x, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Change in forbidden-history rate vs ordinary browser\n(percentage points)")
    ax.set_title(
        "Controlled gateway delay, fixed correct recommendation", loc="left", fontweight="bold"
    )
    fig.subplots_adjust(left=0.29, right=0.98, bottom=0.33, top=0.86)
    fig.text(
        0.01,
        0.01,
        "12 source contracts; 72 matched worlds/contrast; source bootstrap 95% intervals.\nOne invalid branch retained in full-assignment bounds; no LLM latency effect inferred.",
        fontsize=8,
    )
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(output / f"controlled-delay.{ext}", dpi=190)
    plt.close(fig)
    if analysis is None:
        return
    report = read(analysis)
    arms = report["arms"]
    names = list(arms)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    x = np.arange(len(names))
    valid = np.array([arms[n].get("VALID", 0) for n in names])
    safe = np.array([arms[n].get("joint_safe_completion", 0) for n in names])
    registered = np.array([arms[n]["registered"] for n in names])
    invalid = registered - valid
    ax.bar(x, safe / registered * 100, label="Joint safe completion", color="#267a65")
    ax.bar(
        x,
        (valid - safe) / registered * 100,
        bottom=safe / registered * 100,
        label="Valid failure",
        color="#c0cbd4",
    )
    ax.bar(
        x,
        invalid / registered * 100,
        bottom=valid / registered * 100,
        label="Unknown / invalid / missing",
        color="#d8a44d",
        hatch="///",
    )
    ax.set_xticks(x, [n.replace("-", "\n") for n in names])
    ax.set_ylabel("Percent of registered assignments")
    ax.set_ylim(0, 100)
    ax.set_title("Full-denominator outcomes by policy", loc="left", fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=3, fontsize=8)
    for i, n in enumerate(names):
        ax.text(i, 98, str(registered[i]), ha="center", va="top", fontsize=8)
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(output / f"policy-outcomes.{ext}", dpi=190)
    plt.close(fig)
    contrasts = report["contrasts"]
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    for i, c in enumerate(contrasts):
        if c["complete_pair_estimate"] is None:
            continue
        lo, hi = c["source_stratified_bootstrap95"]
        ax.plot([100 * lo, 100 * hi], [i, i], color="#245581")
        ax.plot(
            c["complete_pair_estimate"] * 100,
            i,
            "o",
            color="#a64a40" if c["primary"] else "#245581",
        )
        if c["assignment_bounds"]:
            ax.plot(
                np.array(c["assignment_bounds"]) * 100, [i + 0.12, i + 0.12], color="#d4a247", lw=2
            )
    ax.axvline(0, color="#aaa", lw=0.8)
    ax.set_yticks(range(len(contrasts)), [c["contrast"] for c in contrasts])
    ax.invert_yaxis()
    ax.set_xlabel("Difference in joint safe completion (percentage points)")
    ax.set_title("Paired source-task contrasts", loc="left", fontweight="bold")
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.31, top=0.86)
    fig.text(
        0.01,
        0.01,
        "Blue/red: complete-pair estimate and source bootstrap 95% interval.\nGold: full-assignment bounds. Degenerate intervals do not establish equivalence.",
        fontsize=8,
    )
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(output / f"policy-contrasts.{ext}", dpi=190)
    plt.close(fig)


def atlas(graph, output):
    output.mkdir(parents=True, exist_ok=False)
    grouped = collections.defaultdict(list)
    for line in (graph / "nodes.jsonl").open():
        n = json.loads(line)
        grouped[n["episode"]].append(n)
    entries = []
    colors = {
        "model": "#315c86",
        "browser": "#8c6bb1",
        "controller": "#d88d32",
        "actor": "#d88d32",
        "receiver": "#ae4b43",
        "external": "#ae4b43",
    }
    for index, (episode, nodes) in enumerate(grouped.items()):
        timed = [n for n in nodes if n.get("wall") is not None]
        if not timed:
            continue
        start = min(n["wall"] for n in timed)
        end = max(n["wall"] for n in timed)
        span = max(end - start, 0.01)
        lanes = [
            "Model",
            "Actor / controller",
            "Browser HTTP",
            "External / receiver",
            "Application",
        ]
        svg = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="335" viewBox="0 0 1100 335">',
            '<rect width="1100" height="335" fill="white"/>',
            f'<text x="20" y="25" font-family="sans-serif" font-size="14">{html.escape(episode)}</text>',
        ]
        for i, lane in enumerate(lanes):
            y = 70 + i * 43
            svg += [
                f'<text x="12" y="{y + 4}" font-family="sans-serif" font-size="11">{lane}</text>',
                f'<line x1="160" x2="1070" y1="{y}" y2="{y}" stroke="#ddd"/>',
            ]
        for n in timed:
            k = n["kind"]
            prefix = k.split(".")[0]
            lane = (
                0
                if prefix == "model"
                else 1
                if prefix in {"actor", "controller", "evidence"}
                else 2
                if prefix == "browser"
                else 3
                if prefix in {"receiver", "external"}
                else 4
            )
            x = 160 + 910 * (n["wall"] - start) / span
            y = 70 + lane * 43
            color = colors.get(prefix, "#66806c")
            tip = html.escape(
                f"{k} | +{n['wall'] - start:.3f}s | {n['evidence_path']}#{n['pointer']}"
            )
            svg.append(
                f'<circle cx="{x:.2f}" cy="{y}" r="3" fill="{color}"><title>{tip}</title></circle>'
            )
        for t in range(6):
            x = 160 + 910 * t / 5
            svg.append(
                f'<text x="{x:.1f}" y="290" text-anchor="middle" font-family="sans-serif" font-size="10">{span * t / 5:.1f}s</text>'
            )
        svg.append(
            '<text x="160" y="320" font-family="sans-serif" font-size="10">Elapsed from first recorded event; audit/HTTP time bounds, not exact SQL COMMIT. Hover for raw provenance.</text></svg>'
        )
        name = f"trajectory-{index:05d}.svg"
        (output / name).write_text("\n".join(svg))
        terminal = next((n["label"] for n in nodes if n["kind"] == "episode.terminal"), "UNKNOWN")
        entries.append(dict(episode=episode, svg=name, status=terminal, nodes=len(nodes)))
    rows = "".join(
        f'<tr><td><a href="{e["svg"]}">{html.escape(e["episode"])}</a></td><td>{e["status"]}</td><td>{e["nodes"]}</td></tr>'
        for e in entries
    )
    (output / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>AfterClick evidence atlas</title><style>body{font:14px system-ui;margin:32px;max-width:1400px}td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd}input{padding:10px;width:70%}a{color:#245581}</style><h1>AfterClick trajectory evidence atlas</h1><p>Actual event timestamps and raw-file pointers. Intermediate reachability is UNKNOWN. Each link opens a standalone vector timeline; hover over events for provenance.</p><input placeholder="Filter task, policy or outcome" oninput="for(const r of document.querySelectorAll(\'tbody tr\'))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())"><table><thead><tr><th>Executed trajectory</th><th>Recoverability label</th><th>Observed nodes</th></tr></thead><tbody>'
        + rows
        + "</tbody></table>"
    )
    (output / "manifest.json").write_text(json.dumps(entries, indent=2) + "\n")
    print(json.dumps(dict(trajectories=len(entries), index=str(output / "index.html"))))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--analysis", type=Path)
    p.add_argument("--actuator", type=Path)
    p.add_argument("--graphs", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.graphs:
        atlas(a.graphs, a.output)
    else:
        figures(a.analysis, a.actuator, a.output)
