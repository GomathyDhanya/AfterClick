"""Time-indexed historical trace atlas with conditional sibling witnesses.

Static scientific SVGs and machine-readable cuts are generated from raw records.
An event-prefix fingerprint is explicitly not a complete live replay snapshot.
"""

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path

from afterclick.completion_v12.evidence import EvidenceStore, digest, sha


def render(graph_dir, output, root=Path.cwd()):
    graph_dir, output = Path(graph_dir), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    data = json.loads((graph_dir / "summary.json").read_text())
    store = EvidenceStore(root)
    witnesses, cuts, panels = [], [], []
    groups = defaultdict(list)
    for branch in data["branches"]:
        groups[branch["run_id"], branch["source_id"]].append(branch)
    for (run, source), siblings in groups.items():
        if len({b["cut_sha256"] for b in siblings}) != 1:
            raise ValueError("Cannot join sibling witnesses across unequal cuts")
        safe = [b for b in siblings if b["safe"]]
        for branch in siblings:
            arm = branch["arm"]
            base = f"artifacts/research_runs/{run}/raw/{source}/{arm}"
            final_path, report_path = base + "/final.json", base + "/report.json"
            final, report = store.read(final_path), store.read(report_path)
            events = final["tc_events"]
            bad_ids = set(report["oracle"]["unauthorized_mock_receipt_ids"])
            history = []
            ordered = [(float(e["wall"]), "tc_events", i, e) for i, e in enumerate(events)]
            ordered += [
                (float(r["wall"]), "tc_receipts", i, r) for i, r in enumerate(final["tc_receipts"])
            ]
            dirty = False
            for wall, table, i, raw in sorted(ordered):
                history.append([table, raw["id"]])
                dirty |= table == "tc_receipts" and raw["id"] in bad_ids
                cuts.append(
                    dict(
                        run_id=run,
                        source_id=source,
                        arm=arm,
                        wall=wall,
                        logical_ms=raw["ms"],
                        raw_evidence=store.reference(final_path, table, i),
                        source_cut_sha256=branch["cut_sha256"],
                        event_prefix_sha256=digest(history),
                        fingerprint_scope="Recorded event prefix; incomplete live state",
                        historical_status="RECORDED_FORBIDDEN_HISTORY"
                        if dirty
                        else "NO_FORBIDDEN_RECEIPT_IN_OBSERVED_PREFIX",
                        current_state_repair="UNKNOWN",
                        existential="UNKNOWN",
                        robust="UNKNOWN",
                        remaining_obligations="UNKNOWN_UNTIL_TERMINAL_SNAPSHOT",
                    )
                )
            witnesses.append(
                dict(
                    run_id=run,
                    source_id=source,
                    arm=arm,
                    safe=branch["safe"],
                    cut_sha256=branch["cut_sha256"],
                    witnessed_safe_alternatives=[b["arm"] for b in safe if b["arm"] != arm],
                    witnessed_from="COMMON_CERTIFIED_SOURCE_CUT_ONLY",
                    deployable_oracle=False,
                    schedule_robustness="UNKNOWN",
                )
            )
            panels.append((branch, final, report, base))
    (output / "time-indexed-cuts.jsonl").write_text(
        "".join(json.dumps(c, sort_keys=True) + "\n" for c in cuts)
    )
    (output / "sibling-witnesses.json").write_text(json.dumps(witnesses, indent=2) + "\n")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    paths = []
    for branch, final, report, base in panels:
        if (store.root / (base + "/worker-intervals.json")).exists():
            workers = store.read(base + "/worker-intervals.json")
        else:
            workers = report["worker_intervals"]
        zero = min(w["start_wall"] for w in workers)
        fig, ax = plt.subplots(figsize=(11, 3.6), layout="constrained")
        for name in ["inference.jsonl", "actor-inference.jsonl"]:
            if not (store.root / base / name).exists():
                continue
            for interval in store.read(base + "/" + name):
                ax.plot(
                    [interval["start_wall"] - zero, interval["end_wall"] - zero],
                    [3, 3],
                    color="#32669a",
                    linewidth=6,
                    solid_capstyle="butt",
                )
        for event in sorted(final["tc_events"], key=lambda e: float(e["wall"])):
            kind = event["kind"]
            lane = 2 if kind.startswith("command.") else 1
            label = kind.removeprefix("command.").replace("_", " ")
            x = float(event["wall"]) - zero
            color = (
                "#ba3b32" if kind in {"dispatch.issued", "access.ticket_snapshot"} else "#555555"
            )
            ax.scatter(x, lane, c=color, s=23)
            ax.annotate(
                label, (x, lane), xytext=(2, 7), textcoords="offset points", fontsize=6, rotation=32
            )
        for receipt in final["tc_receipts"]:
            bad = receipt["id"] in report["oracle"]["unauthorized_mock_receipt_ids"]
            x = float(receipt["wall"]) - zero
            ax.scatter(x, 1, marker="X", c="#ba3b32" if bad else "#34765c", s=65)
            ax.annotate(
                receipt["kind"], (x, 1), xytext=(0, -20), textcoords="offset points", fontsize=7
            )
        end = max(w["stop_wall"] for w in workers) - zero
        ax.scatter(end, 0, c="#34765c" if branch["safe"] else "#ba3b32", s=50)
        ax.annotate(
            f"terminal: legitimate={branch['legitimate']}, safe={branch['safe']}",
            (end, 0),
            xytext=(-270, 0),
            textcoords="offset points",
            fontsize=8,
        )
        ax.set_yticks(
            [0, 1, 2, 3],
            [
                "Terminal obligations",
                "Worker / receiver",
                "API command ledger events",
                "Actor inference intervals",
            ],
        )
        ax.set_ylim(-0.5, 3.7)
        ax.set_xlim(-0.1, end + 0.4)
        ax.set_xlabel("Measured host seconds after first resumed worker tick")
        ax.set_title(f"{branch['source_id']} · {branch['arm']} · historical evidence")
        ax.grid(axis="x", alpha=0.2)
        fig.text(
            0.01,
            0.005,
            "Red X: forbidden receipt; blue: measured inference. "
            "Undated native actions omitted from time axis. "
            "Unknown feasibility is not impossibility.",
            fontsize=7,
        )
        filename = branch["source_id"] + "-" + branch["arm"] + ".svg"
        fig.savefig(output / filename)
        plt.close(fig)
        paths.append(filename)
    links = "".join(
        '<p><a href="' + html.escape(p) + '">' + html.escape(p) + "</a></p>" for p in paths
    )
    (output / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>AfterClick historical trajectory atlas</title>'
        "<h1>Historical trajectory atlas</h1><p>42 archived branches; no new model inference. "
        "Observed timing, recorded provenance, and source-cut sibling witnesses. "
        "Current-state and robust recoverability remain UNKNOWN.</p>" + links
    )
    result = dict(
        branches=len(panels),
        source_clusters=len(groups),
        event_cuts=len(cuts),
        failed_branches=sum(not b["safe"] for b in data["branches"]),
        failed_with_safe_sibling=sum(
            not w["safe"] and bool(w["witnessed_safe_alternatives"]) for w in witnesses
        ),
        figures={p: sha(output / p) for p in paths},
        new_model_calls=0,
        input_graph_summary_sha256=sha(graph_dir / "summary.json"),
    )
    (output / "atlas-manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "figures"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graphs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    render(a.graphs, a.output)
