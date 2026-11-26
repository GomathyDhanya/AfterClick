"""Offline final analysis and publication assembly after all finite jobs close."""

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/research_runs"
KIT = ROOT / "research_ops/completion_v12"
PACKAGE = KIT / "final_package"
PROTOCOL = KIT / "proposed_protocol_v4_final_credit_bound/PROTOCOL_FROZEN.json"


def read(p):
    return json.loads(p.read_text())


def write(p, d):
    p.write_text(json.dumps(d, indent=2) + "\n")


def main():
    state = read(KIT / "FINANCE_STATE.json")
    assert state["active"] is None, "Paid job is still active"
    assert (PACKAGE / "tail-execution.json").exists(), "Finite tail has not reconciled"
    out = RUNS / "v12-final-evidence-v1"
    out.mkdir(exist_ok=False)
    log = (out / "commands.log").open("w")
    steps = []

    def call(script, args):
        command = [sys.executable, "research_ops/scripts/" + script, *map(str, args)]
        steps.append(command)
        log.write(" ".join(command) + "\n")
        log.flush()
        subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)

    models = {}
    for tag in ["primary", "larger"]:
        roots = []
        for file in sorted(RUNS.glob("v12-*/registration.json")):
            reg = read(file)
            if (
                reg.get("mode") == "FROZEN_TEST"
                and reg.get("model_tag") == tag
                and reg.get("episodes")
                and list((file.parent / "cloud-batches").glob("**/episodes/*/result.json"))
            ):
                roots.append(file.parent)
        original = RUNS / (
            "v12-44-frozen-primary-test-v1" if tag == "primary" else "v12-43-frozen-larger-test-v1"
        )
        a = out / (tag + "-analysis")
        g = out / (tag + "-graphs")
        v = out / (tag + "-oracle-verification")
        f = out / (tag + "-forensics")
        d = out / (tag + "-interval-diagnostics")
        prefix = out / (tag + "-recoverability-prefixes")
        joins = out / (tag + "-native-joins")
        call(
            "v12_confirmatory_analysis.py",
            ["--registrations", original / "registration.json", "--runs", *roots, "--output", a],
        )
        call("verify_afterclick_v12_outcomes.py", ["--runs", *roots, "--output", v])
        call("v12_graphs.py", ["--runs", *roots, "--output", g])
        call("v12_verify_graphs.py", [g])
        call("analyze_afterclick_v12_forensics.py", ["--runs", *roots, "--output", f])
        call("analyze_afterclick_v12_interval_diagnostics.py", ["--analysis", a, "--output", d])
        call("annotate_afterclick_v12_recoverability.py", ["--graphs", g, "--output", prefix])
        call("augment_afterclick_v12_native_graphs.py", ["--graphs", g, "--output", joins])
        call("render_afterclick_v12.py", ["--graphs", g, "--output", out / (tag + "-atlas")])
        inventory = out / (tag + "-trace-inventory")
        call(
            "inventory_afterclick_v12_traces.py",
            ["--runs", *roots, "--graphs", g, "--output", inventory],
        )
        call(
            "verify_afterclick_v12_graph_extensions.py",
            [
                "--graphs",
                g,
                "--joins",
                joins,
                "--inventory",
                inventory,
                "--output",
                out / (tag + "-extended-graph-verification"),
            ],
        )
        models[tag] = dict(
            registration=str((original / "registration.json").relative_to(ROOT)),
            runs=[str(p.relative_to(ROOT)) for p in roots],
            analysis_report=str((a / "report.json").relative_to(ROOT)),
            graphs=str(g.relative_to(ROOT)),
            verification=str((v / "report.json").relative_to(ROOT)),
            forensics=str(f.relative_to(ROOT)),
            interval_diagnostic=str((d / "report.json").relative_to(ROOT)),
        )
    eroots = [
        RUNS / name
        for name in [
            "v12-44-frozen-primary-test-v1",
            "v12-56-official-external-test-finite",
            "v12-67-official-external-never-started-resume",
            "v12-68-final-credit-bound-continuation",
        ]
    ]
    ereg = eroots[0] / "external-registration.json"
    external = out / "official-external-analysis"
    call(
        "analyze_afterclick_v12_external.py",
        ["--registration", ereg, "--runs", *eroots, "--output", external],
    )
    call(
        "analyze_afterclick_v12_models.py",
        [
            "--primary",
            ROOT / Path(models["primary"]["analysis_report"]).parent,
            "--larger",
            ROOT / Path(models["larger"]["analysis_report"]).parent,
            "--output",
            out / "model-comparison",
        ],
    )
    actuator = RUNS / "v12-37-complex-actuator-analysis-v1/report.json"
    figures = ROOT / "paper/v12/figures"
    call(
        "render_afterclick_v12.py",
        [
            "--analysis",
            ROOT / models["primary"]["analysis_report"],
            "--actuator",
            actuator,
            "--output",
            figures,
        ],
    )
    call(
        "render_afterclick_v12_supplement.py",
        [
            "--actuator",
            actuator,
            "--forensics",
            ROOT / models["primary"]["forensics"] / "attribution.json",
            "--output",
            figures,
        ],
    )
    reports = {k: read(ROOT / v["analysis_report"]) for k, v in models.items()}
    ex = read(external / "report.json")
    registered = sum(r["registered"] for r in reports.values()) + ex["registered"]
    terminal = sum(r["terminal"] for r in reports.values()) + ex["terminal"]
    missing = registered - terminal
    assert registered == 2904
    reconcile = []
    for tag, spec in models.items():
        table = read(ROOT / Path(spec["analysis_report"]).parent / "episode-table.json")
        for row in table:
            reconcile.append(
                dict(
                    model=tag,
                    episode_id=row["episode_id"],
                    task_id=row["task_id"],
                    policy=row["policy"],
                    clean=row["clean"],
                    status=row["status"],
                    joint_safe_completion=row["joint_safe_completion"],
                    evidence=row["evidence"],
                    evidence_sha256=row["evidence_sha256"],
                )
            )
    for row in read(external / "episode-table.json"):
        reconcile.append(
            dict(
                model="official_external_primary",
                episode_id=row["episode_id"],
                task_id=row["task_id"],
                policy=row["method"] + "-" + row["condition"],
                clean=row["condition"] == "CONTROL",
                status=row["status"],
                joint_safe_completion=row["overall_success"],
                evidence=row["evidence"],
                evidence_sha256=hashlib.sha256(Path(row["evidence"]).read_bytes()).hexdigest()
                if row["evidence"]
                else None,
            )
        )
    with (PACKAGE / "FROZEN_MATRIX_RECONCILIATION.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(reconcile[0]))
        writer.writeheader()
        writer.writerows(reconcile)
    full = missing == 0
    index = dict(
        original_workspace_root=str(ROOT),
        utc=datetime.now(timezone.utc).isoformat(),
        freeze=str(PROTOCOL.relative_to(ROOT)),
        freeze_sha256=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        **models,
        external=dict(
            registration=str(ereg.relative_to(ROOT)),
            runs=[str(p.relative_to(ROOT)) for p in eroots],
            analysis_report=str((external / "report.json").relative_to(ROOT)),
        ),
        evidence_root=str(out.relative_to(ROOT)),
        registered_test=registered,
        terminal_test=terminal,
        unexecuted_test=missing,
        full_matrix_complete=full,
        full_research_complete=False,
        all_scientific_unknowns_retained=True,
    )
    write(PACKAGE / "RELEASE_INDEX.json", index)
    write(out / "executed-commands.json", steps)
    build_manuscript(index, reports, ex, out)
    log.close()
    print(
        json.dumps(
            dict(
                evidence=str(out),
                registered=registered,
                terminal=terminal,
                missing=missing,
                full_matrix_complete=full,
            )
        )
    )


def build_manuscript(index, reports, external, out):
    primary = reports["primary"]
    larger = reports["larger"]
    ledger = read(KIT / "FINANCE_STATE.json")
    guard = max(
        sum(r["guard_charge_usd"] for r in ledger["runs"]),
        ledger["account_metered_highwater_usd"] - ledger["baseline_metered_usd"],
    )
    unknown = sum(r.get("usage", {}).get("uncertain", 0) for r in ledger["runs"])
    calls = sum(r.get("usage", {}).get("calls", 0) for r in ledger["runs"])
    tokens = sum(r.get("usage", {}).get("tokens", 0) for r in ledger["runs"])
    for name in ["v12-44-frozen-primary-test-v1", "v12-68-final-credit-bound-continuation"]:
        reconciliation = RUNS / name / "recovered-usage-reconciliation.json"
        if reconciliation.exists():
            recovered = read(reconciliation)
            original = read(RUNS / name / "lifecycle.json")["usage"]
            actual = recovered["recovered_all_batch_usage"]
            calls += actual["calls"] - original["calls"]
            tokens += actual["tokens"] - original["tokens"]
            unknown += actual["uncertain"] - original["uncertain"]
    status = (
        "INCOMPLETE: the frozen evaluation remains budget-censored"
        if not index["full_matrix_complete"]
        else "All frozen assignments have terminal records; validity and unknown outcomes remain separately reported"
    )
    paper = [
        "# AfterClick: task restoration and irreversible history in asynchronous agent workflows",
        "",
        f"**Research status: {status}.**",
        "",
        "## Abstract",
        "",
        f"We implement two different application environments with real PostgreSQL, Chromium, asynchronous workers and separate synthetic-effect HTTP services. The benchmark contains 72 DEV and 216 TEST task contracts, each with independently executable obligations. Two browser reference paths per contract produce 576 witnesses accepted by separately coded checkers; 10,944 evidence/obligation mutations are rejected. A protocol frozen before TEST enrolls 2,904 credit-capped assignments, of which {index['terminal_test']} have terminal records and {index['unexecuted_test']} remain unexecuted. Invalid, censored and unknown outcomes are retained. A separately completed 288-branch fixed-recommendation experiment shows that adding 300/1,500 ms to browser enforcement raises observed forbidden-history incidence by 27.78/60.56 percentage points on 12 constructed sources. These are actuator effects under the implemented backends, not pure neural inference effects. Observed and executed-alternative graphs are separated from bounded formal certificates and unknown recoverability. The evaluation does not establish a generally superior or novel controller.",
        "",
    ]
    methods = (ROOT / "paper/v12/METHODS.md").read_text().splitlines()
    paper += methods[2:]
    paper += [
        "",
        "## Results and completeness",
        "",
        f"The primary queue has {primary['terminal']}/{primary['registered']} terminal records; the larger-model supplement has {larger['terminal']}/{larger['registered']}; the official external benchmark has {external['terminal']}/{external['registered']}. A terminal record is not necessarily valid and need not contain a successful generation. The full frozen matrix is reconciled in the artifact CSV. Unexecuted assignments do not count as executed trials.",
        "",
        "| Primary arm | Registered | Valid | Joint safe | Invalid or missing |",
        "|---|---|---|---|---|",
    ]
    for arm, c in primary["arms"].items():
        paper.append(
            f"| {arm} | {c['registered']} | {c.get('VALID', 0)} | {c.get('joint_safe_completion', 0)} | {c['registered'] - c.get('VALID', 0)} |"
        )
    paper += [
        "",
        "Joint-safe counts are observed lower bounds on full-assignment completion. The valid subset is selected by execution and censoring and must not be interpreted as a completed representative evaluation.",
        "",
        "![Figure 1. Full registered denominators, with unknown cases retained.](figures/policy-outcomes.png)",
        "",
        "### Frozen contrasts",
        "",
        "| Contrast | Complete source clusters | Complete-pair difference | Full-assignment range | Holm secondary p |",
        "|---|---|---|---|---|",
    ]
    for c in primary["contrasts"]:
        e = c["complete_pair_estimate"]
        b = c["assignment_bounds"]
        p = c.get("holm_adjusted_secondary_p")
        p_label = "Primary" if p is None else f"{p:.4f}"
        paper.append(
            f"| {c['contrast']} | {c['complete_pair_source_clusters']} | {e:.4f} | [{b[0]:.4f}, {b[1]:.4f}] | {p_label} |"
            if e is not None and b
            else f"| {c['contrast']} | 0 | Unidentified | Unidentified | Not interpretable |"
        )
    paper += [
        "",
        "Differences are in probability units. These are frozen complete-pair outputs, separated from bounds over every enrolled assignment. Censoring and limited completed support prevent a completed confirmatory claim. Singleton-cell bootstrap diagnostics and the frozen studentized standard errors are published separately; no point interval is treated as precise evidence.",
        "",
        "![Figure 2. Paired policy estimates and full-assignment bounds; bootstrap intervals on singleton focused cells are uninformative.](figures/policy-contrasts.png)",
        "",
        "### Controlled actuator effects",
        "",
        "All 288 fixed-recommendation branches execute: 287 valid and one invalid. Added 300 ms delay changes forbidden-history incidence by +27.78 percentage points (source bootstrap 95% interval 23.61 to 31.94); added 1,500 ms changes it by +60.56 points (55.83 to 64.72). The latter missing-outcome range is 59.72 to 61.11 points. Direct HTTP minus ordinary browser is -2.78 points (-9.72 to 4.17). These results condition on twelve constructed task contracts and six shared mechanisms.",
        "",
        "![Figure 3. Actual controlled delay effects with source-cluster intervals.](figures/controlled-delay.png)",
        "",
        "![Figure 4. Every actuator-by-eligibility cell; one invalid case remains unknown.](figures/actuator-cells.png)",
        "",
        "### Current local state and irreversible history",
        "",
        "![Figure 5. Independent current-local-state and historical-effect dimensions.](figures/state-history.png)",
        "",
        "A locally completed task can coexist with prohibited external history. These are observed final-state cross-tabulations, not evidence that all later states are repairable. First immutable violation, protection-audit ordering, unmet duties and actual reviewer records are linked per episode in the forensic ledger. When the worker admission/read boundary is unavailable, causal attribution remains unresolved.",
        "",
        "### Larger-model and official external scope",
        "",
        "The larger-model comparison uses only its fixed 36-source common support and the same declared tools/budgets. Model weights, precision, hardware and serving details differ. It does not identify model scale alone or establish generalization to unrelated model families. Full common-support tables and assignment bounds are provided in the artifact.",
        "",
        "| Official method | CONTROL safe / registered | FAULT safe / registered | Complete control-capable pairs | Conditional recovery |",
        "|---|---|---|---|---|",
    ]
    for m in external["methods"]:
        paper.append(
            f"| {m['method']} | {m['control_success']}/{m['registered_control']} | {m['fault_success']}/{m['registered_fault']} | {m['complete_control_capable_pairs']} | {m['conditional_recovery_success']:.3f} |"
        )
    paper += [
        "",
        "The official engine and dual evaluator are unchanged. Context seeds are not independent randomized fault programs. Goal-only success, forbidden effects and duplicates remain separate in the machine-readable report. Unavailable EvoUndo is not assigned an invented score. P5 is a suspension-first proxy, not a reproduction of Cordon.",
        "",
        "## Compute and limitations",
        "",
        f"The independent ledger records {calls:,} model-call attempts across engineering, DEV and TEST and {tokens:,} known provider-reported tokens. It retains {unknown} response-uncertain calls; their unknown usage is not fabricated. Conservative guard accounting is ${guard:.4f} against the authorized $18 cap. Guard accounting is not an isolated provider invoice. Historical financial records remain separate; fresh billing snapshots and finite lifecycle closure evidence are included.",
        "",
        "The original larger prospective matrix was revised before TEST for the explicit credit limit. The revised matrix is still incomplete when unexecuted assignments remain. No negative or null outcome is removed to obtain a controller win. Task construction, trusted fixture authority, non-atomic backend state reads, limited model diversity, serving load, parent deadlines, singleton bootstrap cells and absent exact commit/read timestamps limit interpretation. These limitations are material and preclude a claim that this artifact completes the full requested confirmatory research program.",
        "",
        "## Evidence availability",
        "",
        "All task contracts, frozen manifests, reference qualification, old and corrected DEV labels, actual API bodies and model outputs, application/receiver snapshots, graph provenance, independent checkers, source/environment manifests, original negative evidence and regeneration commands are included in the local reproducibility release. The appendix defines graph epistemic labels and all scoring/invalidity rules. Saved-data analysis makes no model or provider call.",
        "",
        "## Interpretation",
        "",
        "The supported result is a scoped systems characterization: history-aware obligations and legitimate restoration must be evaluated together, and an actual delayed actuator can lose a correct recommendation while external workers progress. Safe initial siblings are conditional witnesses, not an online recovery policy. The incomplete model matrix cannot establish general controller superiority, equivalence or a universal consequence frontier. The remaining assignments and exact technical/financial dispositions are published so that incompleteness is independently visible. Cached-equivalent-information, irrelevant-verification, no-restoration-needed and adversarial-restoration controls are not separately executed arms; arbitrary mid-trajectory counterfactual reconstruction is also absent. The unmet-requirements register distinguishes these gaps from completed software and artifact work.",
        "",
        "## References",
        "",
    ]
    references = (PACKAGE / "REFERENCES.md").read_text()
    paper.append(references[references.index("| Primary source") :])
    (ROOT / "paper/v12/AFTERCLICK_V12_MANUSCRIPT.md").write_text("\n".join(paper) + "\n")
    appendix = (ROOT / "paper/v12/APPENDIX_METHODS.md").read_text()
    appendix += (
        "\n## K. Final execution reconciliation\n\n"
        + status
        + ".\n\n"
        + f"Registered TEST assignments: {index['registered_test']}; terminal records: {index['terminal_test']}; unexecuted: {index['unexecuted_test']}. The complete per-assignment table includes all failed, invalid, censored and missing cases.\n\n"
    )
    (ROOT / "paper/v12/AFTERCLICK_V12_APPENDIX.md").write_text(appendix)
    write(
        PACKAGE / "FINAL_FINANCIAL_SUMMARY.json",
        dict(
            guard_accounted_usd=guard,
            authorized_ceiling_usd=18,
            within_guard_ceiling=guard <= 18,
            model_call_attempts=calls,
            known_reported_tokens=tokens,
            response_uncertain_calls=unknown,
            actual_isolated_invoice_usd=None,
        ),
    )


if __name__ == "__main__":
    main()
