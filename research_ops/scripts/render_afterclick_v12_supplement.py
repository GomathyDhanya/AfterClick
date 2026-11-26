"""Offline figures of actual actuator cells and current-state/history divergence."""

import argparse
import ast
import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def save(fig, path):
    for extension in ["png", "svg", "pdf"]:
        fig.savefig(path.with_suffix("." + extension), dpi=190, bbox_inches="tight")
    plt.close(fig)


def main(actuator, forensics, output):
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans"})
    if actuator:
        report = json.loads(actuator.read_text())
        rows = [150, 600, 1800]
        cols = [("direct_http", 0), ("browser", 0), ("browser", 300), ("browser", 1500)]
        matrix = np.zeros((3, 4))
        unknown = np.zeros((3, 4), dtype=int)
        counts = np.zeros((3, 4), dtype=int)
        for key, data in report["cells"].items():
            threshold, method, delay = ast.literal_eval(key)
            i = rows.index(threshold)
            j = cols.index((method, delay))
            counts[i, j] = data["forbidden_history"]
            matrix[i, j] = data["forbidden_history"] / data["registered"]
            unknown[i, j] = data.get("INVALID", 0)
        fig, ax = plt.subplots(figsize=(6.9, 3.2))
        im = ax.imshow(matrix, vmin=0, vmax=1, cmap="YlOrRd", aspect="auto")
        for i in range(3):
            for j in range(4):
                ax.text(
                    j,
                    i,
                    f"{counts[i, j]} / 24"
                    + (f"\n{unknown[i, j]} unknown" if unknown[i, j] else ""),
                    ha="center",
                    va="center",
                    color="white" if matrix[i, j] > 0.6 else "#222",
                )
        ax.set_xticks(range(4), ["Direct HTTP", "Browser", "Browser\n+300 ms", "Browser\n+1500 ms"])
        ax.set_yticks(range(3), [f"{v} ms" for v in rows])
        ax.set_ylabel("Configured eligibility offset")
        ax.set_title(
            "Executed forbidden histories across timing conditions", loc="left", fontweight="bold"
        )
        fig.colorbar(im, ax=ax, label="Forbidden / registered")
        fig.subplots_adjust(bottom=0.25, left=0.16, right=0.91, top=0.86)
        fig.text(
            0.01,
            0.02,
            "12 sources × 2 worlds per cell; 288 real branches, no LLM.\nOne invalid branch is unknown; cell colors show observed lower bounds.",
            fontsize=8,
        )
        save(fig, output / "actuator-cells")
    if forensics:
        rows = json.loads(forensics.read_text())
        matrix = np.zeros((2, 2), dtype=int)
        unknown = 0
        for row in rows:
            local = row.get("current_local_goals_complete")
            if row["status"] != "VALID" or local is None:
                unknown += 1
                continue
            matrix[int(local), int(bool(row["forbidden_history"]))] += 1
        fig, ax = plt.subplots(figsize=(5.6, 3.7))
        im = ax.imshow(matrix, cmap="Blues", aspect="auto")
        for i in range(2):
            for j in range(2):
                ax.text(
                    j,
                    i,
                    str(matrix[i, j]),
                    ha="center",
                    va="center",
                    fontsize=15,
                    color="white" if matrix[i, j] > 0.55 * max(1, matrix.max()) else "#222",
                )
        ax.set_xticks([0, 1], ["No forbidden history", "Forbidden history"])
        ax.set_yticks([0, 1], ["Local goals incomplete", "Local goals complete"])
        ax.set_title("Current local state and immutable history", loc="left", fontweight="bold")
        fig.subplots_adjust(left=0.31, right=0.96, bottom=0.25, top=0.85)
        fig.text(
            0.01,
            0.02,
            f"{int(matrix.sum())} valid observed finals; {unknown} invalid or unassessed finals.\nA locally repaired state does not erase a prohibited physical effect.",
            fontsize=8,
        )
        save(fig, output / "state-history")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--actuator", type=Path)
    p.add_argument("--forensics", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.actuator, a.forensics, a.output)
