import ast
import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "evidence"


def report(name):
    return json.loads((DATA / name).read_text())


def rows(name):
    return list(csv.DictReader((DATA / name).open()))


def verified_inputs():
    for base in [DATA / "publication", DATA / "v12"]:
        manifest = json.loads((base / "MANIFEST.json").read_text())
        for name, entry in manifest["files"].items():
            assert hashlib.sha256((base / name).read_bytes()).hexdigest() == entry["sha256"], name


verified_inputs()
analysis = report("publication/analysis/report.json")
actuator = report("v12/controlled-actuator/report.json")
primary = report("v12/primary-analysis/report.json")
larger = report("v12/larger-analysis/report.json")
duties = rows("publication/obligations/duties.csv")
reviewers = analysis["reviewers"]

P = Path(__file__).parent / "figures"
P.mkdir(exist_ok=True)
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "figure.dpi": 160,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "legend.fontsize": 8,
    }
)
blue = "#315C91"
red = "#B24B44"
teal = "#267E76"
gray = "#677684"
gold = "#C18D39"
light = "#E8EDF2"


def save(f, n):
    f.savefig(P / (n + ".pdf"), bbox_inches="tight", pad_inches=0.08)
    plt.close(f)


# schematic architecture
f, a = plt.subplots(figsize=(7.2, 3.05))
a.set(xlim=(0, 12), ylim=(0, 5.2))
a.axis("off")


def box(x, y, w, h, title, sub, col):
    a.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=.06,rounding_size=.10", fc="white", ec=col, lw=1.4
        )
    )
    a.text(
        x + w / 2,
        y + h * 0.65,
        title,
        ha="center",
        va="center",
        weight="bold",
        color=col,
        fontsize=9,
    )
    a.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=7.6)


def arr(x, y, X, Y, txt="", col=gray, style="-"):
    a.annotate(
        "",
        (X, Y),
        (x, y),
        arrowprops={"arrowstyle": "->", "color": col, "lw": 1.2, "linestyle": style},
    )
    if txt:
        a.text(
            (x + X) / 2, (y + Y) / 2 + 0.13, txt, ha="center", va="bottom", fontsize=7, color=col
        )


box(0.15, 3.6, 2.5, 1, "Actor LLM", "public observations", blue)
box(0.15, 1.8, 2.5, 1, "Safety controller", "rule or LLM review", blue)
box(3.5, 3.6, 3.0, 1, "Browser gateway", "native tools / responses", blue)
box(3.5, 1.8, 3.0, 1, "Application DB", "state + schema lock", teal)
box(7.4, 1.8, 2.15, 1, "Worker", "admit ticket", gold)
box(10, 1.8, 1.85, 1, "Receiver", "physical effect", red)
box(4.0, 0.15, 5.5, 0.85, "Offline evaluator", "contracts + SQL + receipts + event trace", gray)
arr(2.65, 4.1, 3.5, 4.1)
arr(2.65, 2.3, 3.5, 2.3)
arr(5, 3.6, 5, 2.8)
arr(6.5, 2.3, 7.4, 2.3)
arr(9.55, 2.3, 10, 2.3)
arr(5, 1.8, 5, 0.99, style="--")
arr(8.5, 1.8, 8.5, 1, style="--")
arr(10.9, 1.8, 9.5, 0.6, style="--")
a.text(
    9.35,
    4.1,
    "Workers progress independently\nof actor inference",
    ha="center",
    color=gold,
    fontsize=8,
    weight="bold",
)
a.text(
    1.4,
    0.55,
    "No evaluator labels\nreturned to actor",
    ha="center",
    va="center",
    fontsize=8,
    color=gray,
)
save(f, "architecture")
# confusion matrices
f, axs = plt.subplots(1, 2, figsize=(6.9, 2.45), layout="constrained")
for ax, mat, title in zip(
    axs,
    [
        np.array([[c["L_F"][f"{i},{j}"] for j in range(2)] for i in range(2)])
        for c in analysis["cohorts"].values()
    ],
    [
        f"Primary 9B (n={analysis['cohorts']['primary']['valid']})",
        f"Larger model (n={analysis['cohorts']['larger']['valid']})",
    ],
):
    ax.imshow(
        mat,
        cmap=LinearSegmentedColormap.from_list("x", ["#F1F5F8", "#A6BBD1"]),
        vmin=0,
        vmax=mat.max(),
    )
    ax.set_xticks([0, 1], ["No forbidden history", "Forbidden history"])
    ax.set_yticks([0, 1], ["Incomplete", "Local complete"])
    ax.set_title(title, weight="bold")
    ax.tick_params(length=0, labelsize=8)
    ax.spines[:].set_visible(False)
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{mat[i, j]}",
                ha="center",
                va="center",
                fontsize=15,
                weight="bold",
                color=red if (i, j) == (1, 1) else "#18324A",
            )
    ax.add_patch(plt.Rectangle((0.5, 0.5), 1, 1, fill=False, ec=red, lw=2))
save(f, "mismatch")
# delay heatmap and contrast
f, axs = plt.subplots(
    1, 2, figsize=(7, 2.6), gridspec_kw={"width_ratios": [1.1, 1]}, layout="constrained"
)
cellmap = {ast.literal_eval(k): v for k, v in actuator["cells"].items()}
offsets = sorted({k[0] for k in cellmap})
conditions = [("direct_http", 0), ("browser", 0), ("browser", 300), ("browser", 1500)]
m = np.array(
    [
        [cellmap[(offset, *condition)]["forbidden_history"] for condition in conditions]
        for offset in offsets
    ]
)
a = axs[0]
a.imshow(
    m
    / np.array(
        [
            [cellmap[(offset, *condition)]["registered"] for condition in conditions]
            for offset in offsets
        ]
    )
    * 100,
    cmap=LinearSegmentedColormap.from_list("r", ["#F5F6F7", "#E6A79E", red]),
    vmin=0,
    vmax=100,
    aspect="auto",
)
a.set_xticks(range(4), ["HTTP", "Browser", "+300", "+1500"])
a.set_yticks(range(3), ["150", "600", "1800"])
a.set_ylabel("Configured admission offset (ms)")
a.set_title("(a) Forbidden history / 24 registered")
a.tick_params(length=0)
a.spines[:].set_visible(False)
for i in range(3):
    for j in range(4):
        a.text(
            j,
            i,
            f"{m[i, j]}/{cellmap[(offsets[i], *conditions[j])]['registered']}"
            + ("*" if cellmap[(offsets[i], *conditions[j])].get("INVALID", 0) else ""),
            ha="center",
            va="center",
            color="white" if m[i, j] > 18 else "#24354A",
            weight="bold",
        )
a = axs[1]
e = np.array([c["estimate"] * 100 for c in actuator["contrasts"]])
lo = np.array([c["source_bootstrap95"][0] * 100 for c in actuator["contrasts"]])
hi = np.array([c["source_bootstrap95"][1] * 100 for c in actuator["contrasts"]])
a.errorbar(e, [2, 1, 0], xerr=[e - lo, hi - e], fmt="o", color=red, capsize=3)
a.axvline(0, color=gray, lw=1, ls="--")
a.set_yticks([2, 1, 0], ["HTTP", "+300 ms", "+1500 ms"])
a.set_xlabel("Difference vs. ordinary browser (pp)")
a.set_title("(b) Source-paired effect (95% CI)")
a.grid(axis="x", alpha=0.2)
save(f, "actuator")
# Recorded timestamps; select the exact paper witness, never a synthetic timeline.
forensic = next(
    r
    for r in rows("publication/analysis/rq4-refined-ordering.csv")
    if r["raw_sha256"] == "da46276cc4bf43308efd542d4f91676add6fc1056da48f0c8455d11d1a4b7c29"
)
admission = float(forensic["admission_reported_mono"])
protect = (float(forensic["protection_audit_reported_mono"]) - admission) * 1000
commit = (float(forensic["protection_commit_return_upper_mono"]) - admission) * 1000
receipt = (float(forensic["receipt_reported_mono"]) - admission) * 1000

f, a = plt.subplots(figsize=(7, 2.15), layout="constrained")
a.set(xlim=(-12, 290), ylim=(0, 3.0))
a.set_yticks([])
a.spines[:].set_visible(False)
a.hlines(1.25, 0, receipt, color=gray, lw=1.5)
a.axvspan(protect, commit, ymin=0.28, ymax=0.69, color=gold, alpha=0.45)
a.scatter(
    [0, protect, commit, receipt],
    [1.25] * 4,
    c=[blue, gold, teal, red],
    s=[50, 30, 30, 55],
    zorder=4,
)
a.annotate(
    "Admission audit\n0 ms",
    (0, 1.25),
    (34, 2.45),
    ha="center",
    arrowprops={"arrowstyle": "-", "color": blue},
)
a.annotate(
    f"Protection audit → commit-return bound\n{protect:.2f}–{commit:.2f} ms",
    (7.5, 1.25),
    (112, 0.28),
    ha="center",
    arrowprops={"arrowstyle": "-", "color": gold},
)
a.annotate(
    f"Persisted receipt\n{receipt:.2f} ms",
    (receipt, 1.25),
    (239, 2.45),
    ha="center",
    arrowprops={"arrowstyle": "-", "color": red},
)
a.set_xlabel("Reported elapsed time relative to admission audit (ms)")
a.set_xticks([0, 50, 100, 150, 200, 250])
save(f, "forensic")
# policy rates and duty discharge
f, axs = plt.subplots(
    1, 2, figsize=(7.1, 3.3), gridspec_kw={"width_ratios": [1.35, 1]}, layout="constrained"
)
a = axs[0]
arms = [primary["arms"][f"P{i}-stress"] for i in range(4)]
n = np.array([r["VALID"] for r in arms])
g = np.array([r["legitimate_complete"] for r in arms])
F = np.array([r["forbidden_history"] for r in arms])
y = np.array([r["joint_safe_completion"] for r in arms])
x = np.arange(4)
w = 0.24
for k, v, c, label in [
    (-1, 100 * g / n, blue, "Legitimate goal"),
    (0, 100 * (n - F) / n, teal, "No forbidden history"),
    (1, 100 * y / n, gray, "Joint safe"),
]:
    a.bar(x + k * w, v, w, color=c, label=label)
a.set_xticks(x, ["P0", "P1", "P2", "P3"])
a.set_ylim(0, 110)
a.set_ylabel("Valid episodes (%)")
a.set_title("(a) Primary stress policies")
a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=2, frameon=False)
a.grid(axis="y", alpha=0.18)
a = axs[1]
types = ["SERVICE_REOPEN", "APPROVED_REQUEST_RESUBMIT"]
d = np.array(
    [sum(r["kind"] == t and r["status"] == "DISCHARGED_OBSERVED" for r in duties) for t in types]
)
o = np.array(
    [sum(r["kind"] == t and r["status"] == "OUTSTANDING_CENSORED" for r in duties) for t in types]
)
n = d + o
a.barh([1, 0], d / n * 100, color=teal, label="Discharged")
a.barh([1, 0], o / n * 100, left=d / n * 100, color=gold, label="Outstanding")
a.set_yticks([1, 0], [f"Reopen\n(n={n[0]})", f"Resubmit\n(n={n[1]})"])
a.set_xlim(0, 100)
a.set_xlabel("Triggered duties (%)")
a.set_title("(b) Restoration at censoring")
for i, j in enumerate([1, 0]):
    a.text(54, j, f"{o[i]}/{n[i]} outstanding", ha="center", va="center", fontsize=8, weight="bold")
a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), frameon=False)
save(f, "debt")
# bounds plot
f, a = plt.subplots(figsize=(7.1, 3.1), layout="constrained")
bounds_rows = [
    (
        r["contrast"].replace("-", "−") + f" ({r['complete_pair_source_clusters']})",
        r["complete_pair_estimate"] * 100,
        *[x * 100 for x in r["source_stratified_bootstrap95"]],
        *[x * 100 for x in r["assignment_bounds"]],
    )
    for r in primary["contrasts"]
]
r = larger["contrasts"][0]
bounds_rows.append(
    (
        "Larger " + r["contrast"].replace("-", "−") + f" ({r['complete_pair_source_clusters']})",
        r["complete_pair_estimate"] * 100,
        *[x * 100 for x in r["source_stratified_bootstrap95"]],
        *[x * 100 for x in r["assignment_bounds"]],
    )
)
for i, (lab, e, lower, h, L, H) in enumerate(bounds_rows):
    yy = len(bounds_rows) - 1 - i
    a.hlines(yy, L, H, color="#B8C2CD", lw=5, label="Full assignment bounds" if i == 0 else None)
    a.hlines(yy, lower, h, color=blue, lw=3, label="Observed source bootstrap" if i == 0 else None)
    a.plot(e, yy, "o", color=red, ms=5, label="Observed estimate" if i == 0 else None)
a.axvline(0, color=gray, ls="--")
a.set_yticks(range(len(bounds_rows)), [r[0] for r in bounds_rows][::-1])
a.set_xlabel("Difference in joint safe completion (percentage points)")
a.set_xlim(-100, 100)
a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False, fontsize=7.6)
a.grid(axis="x", alpha=0.15)
save(f, "bounds")
# reviewer distribution
f, axs = plt.subplots(1, 2, figsize=(7, 2.1), layout="constrained")
a = axs[0]
a.barh(
    [1, 0],
    [reviewers["exact_rule_agreements"], reviewers["approved_inputs_suspended"]],
    color=[teal, red],
)
a.set_yticks([1, 0], ["Protect per rule", "Allow per rule"])
a.set_xlim(0, 205)
a.set_xlabel("Historical prompts")
a.set_title(f"(a) All {reviewers['received']} recommend suspend")
for y, n in [(1, reviewers["exact_rule_agreements"]), (0, reviewers["approved_inputs_suspended"])]:
    a.text(n + 4, y, str(n), va="center", weight="bold")
a = axs[1]
q = reviewers["http_interval_quantiles"]
a.hlines(0, q[0], q[-1], color=gray)
a.add_patch(plt.Rectangle((q[1], -0.13), q[3] - q[1], 0.26, fc=light, ec=blue))
a.vlines(q[2], -0.13, 0.13, color=blue, lw=2)
a.scatter([q[4]], [0], marker="D", color=red, zorder=4)
a.text(q[4], 0.19, f"p95 {q[4]:.2f} s", ha="center", fontsize=8)
a.text(q[2], -0.30, f"median {q[2]:.2f} s", ha="left", fontsize=8)
a.set_ylim(-0.5, 0.5)
a.set_yticks([])
a.set_xlabel("Observed HTTP request interval (s)")
a.set_title("(b) Transport + serving + inference")
save(f, "reviewer")
# sensitivity plot from report
f, a = plt.subplots(figsize=(6.8, 2.65), layout="constrained")
sensitivity = rows("publication/analysis/structural-sensitivity.csv")
ordered = [r for r in sensitivity if r["cohort"] == "primary"]
labels = ["Exclude " + r["excluded_value"].replace("_", " ") for r in ordered]
p = np.array([float(r["conditional_rate"]) for r in ordered]) * 100
larger_rates = (
    np.array(
        [
            float(
                next(
                    v
                    for v in sensitivity
                    if v["cohort"] == "larger"
                    and v["excluded_dimension"] == r["excluded_dimension"]
                    and v["excluded_value"] == r["excluded_value"]
                )["conditional_rate"]
            )
            for r in ordered
        ]
    )
    * 100
)
y = np.arange(8)[::-1]
a.scatter(p, y + 0.12, color=blue, label="Primary")
a.scatter(larger_rates, y - 0.12, color=gold, label="Larger")
a.axvline(
    analysis["cohorts"]["primary"]["conditional_mismatch"]["estimate"] * 100,
    color=blue,
    alpha=0.45,
    ls="--",
)
a.axvline(
    analysis["cohorts"]["larger"]["conditional_mismatch"]["estimate"] * 100,
    color=gold,
    alpha=0.45,
    ls="--",
)
a.set_yticks(y, labels)
a.set_xlabel("Conditional mismatch rate (%)")
a.set_xlim(15, 52)
a.legend(frameon=False, loc="lower right")
a.grid(axis="x", alpha=0.2)
save(f, "sensitivity")
