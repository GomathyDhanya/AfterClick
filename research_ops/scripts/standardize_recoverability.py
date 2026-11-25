"""Derived evidence inventory and figures; never edits historical runs or performs inference."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "artifacts/research_runs"
OUT = ROOT / "paper/recoverability-generated"


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def group(n):
    if n.startswith(("u",)):
        return "J"
    if n.startswith(("t", "s")):
        return "I"
    if n.startswith(("i", "p1")):
        return "H"
    if n.startswith("o"):
        return "G"
    if n.startswith("p2"):
        return "B"
    if n.startswith("p3"):
        return "C"
    if n.startswith("p4"):
        return "D"
    if n.startswith(("p6", "p7")):
        return "E"
    if n.startswith(("p8", "p9")):
        return "F"
    return "A"


def compact(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=True)


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    for run in sorted(BASE.iterdir()):
        if not run.is_dir() or run.name.startswith("v0-"):
            continue
        p = read(run / "protocol.json")
        m = read(run / "metrics.json")
        manifest = read(run / "manifest.json")
        trials = (
            [json.loads(x) for x in (run / "trials.jsonl").read_text().splitlines() if x.strip()]
            if (run / "trials.jsonl").exists()
            else []
        )
        meta = [x.get("metadata", {}) for x in trials]
        ids = {
            str(
                x.get("source_group")
                or x.get("source")
                or x.get("lineage_group")
                or y.get("lineage_group")
                or ""
            )
            for x, y in zip(trials, meta)
        } - {""}
        journal = (
            [
                json.loads(x)
                for x in (run / "model_calls.jsonl").read_text().splitlines()
                if x.strip()
            ]
            if (run / "model_calls.jsonl").exists()
            else []
        )
        calls = m.get(
            "total_generation_requests", m.get("usage", {}).get("calls", m.get("model_calls"))
        )
        starts = sum(x.get("event") == "started" for x in journal)
        if starts:
            calls = starts
        model = p.get("model", p.get("policy_model", manifest.get("policy_model")))
        rev = p.get("revision", manifest.get("model_version_or_revision"))
        evidence = (
            "fresh LLM continuations plus controlled environment"
            if calls
            else "local scripted/simulated or audit; see protocol"
        )
        row = dict(
            group=group(run.name),
            run_id=run.name,
            question=compact(p.get("question", p.get("target"))),
            hypothesis=compact(p.get("hypothesis", p.get("hypotheses"))),
            mechanism=compact(
                p.get("mechanisms", p.get("independent_environment", p.get("cases")))
            ),
            model=compact(model),
            revision=compact(rev),
            decision_origin=evidence,
            independent_source_instances=compact(
                m.get("finite_source_clusters", m.get("planned_sources"))
            ),
            observed_lineage_ids=len(ids) if ids else "null",
            lineage_note=(
                "IDs are not necessarily independent; "
                "shared source/template and reuse remain grouped"
            ),
            dependent_branches=compact(
                m.get("planned_primary", m.get("primary_counts", m.get("attempted")))
            ),
            genuine_generations=compact(calls),
            journal_started=starts,
            interventions=compact(p.get("interventions", p.get("intervention"))),
            oracle=compact(p.get("oracle", p.get("independent_oracle", p.get("recovery")))),
            metrics_keys=compact(list(m)),
            unknown=compact(m.get("unknown")),
            censored=compact(m.get("censored")),
            invalid=compact(m.get("invalid")),
            validity=compact(m.get("passed", m.get("accepted", manifest.get("status")))),
            partition=compact(p.get("partition", p.get("splits", p.get("phase")))),
            artifact_path=str(run.relative_to(ROOT)),
            protocol_sha256=hashlib.sha256((run / "protocol.json").read_bytes()).hexdigest()
            if (run / "protocol.json").exists()
            else "null",
            metrics_sha256=hashlib.sha256((run / "metrics.json").read_bytes()).hexdigest()
            if (run / "metrics.json").exists()
            else "null",
            reproduce_command=".venv/bin/python -m research_ops.scripts.standardize_recoverability",
            supported_claim=(
                "Study-specific results only; see RECOVERABILITY_CLAIM_MATRIX.md and raw protocol"
            ),
            unsupported_claim=(
                "No pooled population, general algorithm superiority or organic field error rate"
            ),
            protocol_details=compact(p),
        )
        rows.append(row)
    path = ROOT / "research_ops/RECOVERABILITY_EVIDENCE_INVENTORY.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    # Derived tables preserve frozen metric names rather than inventing common labels.
    search = read(BASE / "p4-matched-search-v1/metrics.json")["methods"]
    races = read(BASE / "o2-observability-locked-v1/metrics.json")["cohorts"]
    mechanism = Counter()
    for n in ["p2-20261123-distinct-mechanisms-v1", "p2-capability-diversity-v1"]:
        for line in (BASE / n / "trials.jsonl").read_text().splitlines():
            x = json.loads(line)
            mechanism[x["mechanism"], x["classification"]] += 1
    tables = dict(
        schema_version=1,
        inventory_runs=len(rows),
        backend_classifications=[
            dict(mechanism=k[0], classification=k[1], count=v) for k, v in sorted(mechanism.items())
        ],
        search={k: {x: y for x, y in v.items() if x != "mean_curve"} for k, v in search.items()},
        verification_races={k: v["H5_verify_minus_cancel"] for k, v in races.items()},
        source_artifacts=[
            "p2-20261123-distinct-mechanisms-v1/trials.jsonl",
            "p2-capability-diversity-v1/trials.jsonl",
            "p4-matched-search-v1/metrics.json",
            "o2-observability-locked-v1/metrics.json",
        ],
    )
    (OUT / "tables.json").write_text(json.dumps(tables, indent=2) + "\n")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "svg.hashsalt": "afterclick-recoverability-v1",
        }
    )

    def save(fig, name):
        fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight")
        fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 2.5))
    names = ["random_min", "coverage_min", "local_frontier"]
    names = [k for k in search if k not in ["plain_random", "enumeration"]]
    ax.bar(
        range(len(names)),
        [search[k]["mean_coverage_auc"] for k in names],
        color=["#56879c", "#247564", "#c27a40"][: len(names)],
    )
    ax.set(
        xticks=range(len(names)),
        xticklabels=[k.replace("_", " ") for k in names],
        ylabel="Mean mechanism-coverage AUC",
        title="Controlled search: 30 seeds, 96 charged queries / method / seed",
    )
    save(fig, "search")
    fig, ax = plt.subplots(figsize=(7, 2.6))
    coh = list(races)
    vals = [races[k]["H5_verify_minus_cancel"]["estimate"] for k in coh]
    cis = [races[k]["H5_verify_minus_cancel"]["ci95"] for k in coh]
    ax.errorbar(
        range(3),
        vals,
        yerr=[[v - c[0] for v, c in zip(vals, cis)], [c[1] - v for v, c in zip(vals, cis)]],
        fmt="o",
        color="#247564",
        capsize=5,
    )
    ax.set(
        xticks=range(3),
        xticklabels=coh,
        ylabel="Verify minus cancel risk",
        title="Synthetic timing-mixture contrast; 512 source clusters / cohort",
    )
    ax.axhline(0, color="#888", lw=0.7)
    save(fig, "verification-races")
    fig, ax = plt.subplots(figsize=(7, 2.5))
    names = ["No shield", "Authorization + timer", "Learned risk"]
    control = read(BASE / "p9-locked-confirmation-v1/metrics.json")["controller_metrics"]
    methods = ["none", "authorization_timer", "learned_risk"]
    selected = [
        next(r for r in control if r["method"] == m and r["budget_cap"] == 0.2) for m in methods
    ]
    ax.bar(names, [r["harms"] for r in selected], color=["#ad6251", "#247564", "#56879c"])
    ax.set(
        ylabel="Verified unauthorized harms / 2048 rows",
        title=(
            "Controlled final cohort: full task completion; protected methods use 409 interventions"
        ),
    )
    save(fig, "controller")
    # Measured real Qwen example, not a scripted action sequence.
    report = read(BASE / "t4-distinct-9b-baseline-v1/raw/dev-05/report.json")
    selected_actions = [r for r in report["actions"] if r["source"].get("kind") != "driver"]
    (OUT / "live-trajectory.json").write_text(json.dumps(selected_actions, indent=2) + "\n")
    fig, ax = plt.subplots(figsize=(7, 2.2))
    labels = [r["action"]["kind"] + "\n" + r["action"].get("target", "") for r in selected_actions]
    ax.plot(range(len(labels)), [1] * len(labels), color="#53717b")
    ax.scatter(range(len(labels)), [1] * len(labels), color="#247564")
    for i, label in enumerate(labels):
        ax.text(i, 1.08, label, ha="center", va="bottom", fontsize=8)
    receipts = report["state"]["tc_receipts"]
    ax.text(
        0.5,
        0.12,
        f"Independent receipt: {receipts[0]['ms']} ms; "
        "historical resource consumption remains after cancellation",
        ha="center",
        transform=ax.transAxes,
        fontsize=8,
    )
    ax.set_ylim(0.6, 1.5)
    ax.axis("off")
    ax.set_title("Recorded Qwen resource task: selected actions through Gateway")
    save(fig, "live-trajectory")
    # Structural diagram, no numerical experimental claims.
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(7, 2.7))
    ax.axis("off")
    boxes = [
        (0.01, 0.58, 0.27, 0.27, "Natural-language task\nQwen native tools"),
        (0.36, 0.58, 0.28, 0.27, "Gateway + FlowBoard\nPostgreSQL jobs"),
        (0.72, 0.58, 0.27, 0.27, "Async fake services\nExternal observer history"),
        (0.30, 0.12, 0.40, 0.25, "Independent SQL/history oracle\nPrivate grading + certificates"),
    ]
    for x, y, w, h, text in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=.01",
                facecolor="#eef3f5",
                edgecolor="#53717b",
                transform=ax.transAxes,
            )
        )
        ax.text(
            x + w / 2, y + h / 2, text, transform=ax.transAxes, ha="center", va="center", fontsize=8
        )
    for a, b in [
        ((0.28, 0.72), (0.35, 0.72)),
        ((0.65, 0.72), (0.71, 0.72)),
        ((0.50, 0.57), (0.50, 0.38)),
        ((0.85, 0.57), (0.71, 0.26)),
    ]:
        ax.annotate(
            "",
            xy=b,
            xytext=a,
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="->", color="#53717b"),
        )
    ax.text(
        0.5,
        0.01,
        "Model sees public inputs only; hidden schedules and grades are withheld.",
        fontsize=8,
        ha="center",
        transform=ax.transAxes,
    )
    save(fig, "architecture")
    (OUT / "provenance.json").write_text(
        json.dumps(
            dict(
                schema_version=1,
                derivation="research_ops/scripts/standardize_recoverability.py",
                tables="tables.json",
                structural_figures=["architecture"],
                measured_figures={
                    "search": "p4-matched-search-v1/metrics.json",
                    "verification-races": "o2-observability-locked-v1/metrics.json",
                    "controller": "p9-locked-confirmation-v1/metrics.json",
                    "live-trajectory": "t4-distinct-9b-baseline-v1/raw/dev-05/report.json",
                },
                no_new_model_calls=True,
            ),
            indent=2,
        )
        + "\n"
    )
    print(f"Inventoried {len(rows)} runs; generated versioned tables and figures")


if __name__ == "__main__":
    main()
