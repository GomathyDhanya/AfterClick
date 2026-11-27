"""Build the anonymous paper and appendix directly from checked compact results."""
# ruff: noqa: E501 -- manuscript template paragraphs retain natural line structure.

import argparse
import csv
import hashlib
import json
from pathlib import Path


def load(p):
    return json.loads(p.read_text())


def table(p):
    return list(csv.DictReader(p.open()))


def pct(x):
    return f"{100 * x:.1f}%"


def interval(x, scale=100):
    if x is None:
        return "UNKNOWN"
    return "[" + ", ".join(f"{scale * v:.1f}" for v in x) + "]"


def mdtable(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|" + "---|" * len(headers),
            *["| " + " | ".join(str(v) for v in r) + " |" for r in rows],
        ]
    )


def build(data, out):
    out.mkdir(parents=True, exist_ok=True)
    r = load(data / "analysis/report.json")
    n = load(data / "normalized/report.json")
    d = load(data / "obligations/report.json")
    checks = load(data / "checks/report.json")
    actuator = load(data.parent / "v12/controlled-actuator/report.json")
    verified = load(data / "actuator-verification/report.json")
    boundary = load(data / "boundary/report.json")
    replay = load(data / "replay/report.json")
    normal = load(data / "normalization-verification/report.json")
    original = {
        tag: load(data.parent / f"v12/{tag}-analysis/report.json") for tag in ["primary", "larger"]
    }
    external = load(data.parent / "v12/official-external-analysis/report.json")
    candidate = load(data / "data-candidate.json")
    finance = load(data / "finance.json")
    primary = r["cohorts"]["primary"]
    larger = r["cohorts"]["larger"]
    reviews = r["reviewers"]
    assert (
        checks["passed"]
        and normal["passed"]
        and verified["passed"]
        and boundary["valid"] == boundary["registered"] == 72
        and replay["received"] == replay["registered"] == 264
    )
    assert (
        candidate["changed_top_level_files"] == 0 and candidate["public_upload_performed"] is False
    )
    linux_path = data / "linux/report.json"
    linux = load(linux_path) if linux_path.exists() else None
    if not linux:
        raise RuntimeError(
            "A terminal independent Linux report is required before final manuscript generation"
        )
    assert linux["complete"] and finance["active"] is None and not finance["unresolved"]
    env = load(data / "linux/environment.json")
    linux_lifecycle = load(data / "linux/lifecycle.json")
    old_contrast = {
        tag: next(x for x in original[tag]["contrasts"] if x["contrast"] == "P3-P2")
        for tag in original
    }
    enrollment = mdtable(
        ["Cohort", "Registered", "Terminal", "Valid internal", "Invalid internal", "Not run"],
        [
            [
                "Primary 9B",
                primary["registered"],
                primary["terminal"],
                primary["valid"],
                primary["invalid"],
                primary["not_run"],
            ],
            [
                "Larger model",
                larger["registered"],
                larger["terminal"],
                larger["valid"],
                larger["invalid"],
                larger["not_run"],
            ],
            [
                "Official external",
                external["registered"],
                external["terminal"],
                "separate oracle",
                "separate oracle",
                len(external["missing"]),
            ],
        ],
    )
    mismatch = mdtable(
        [
            "Cohort",
            "L and F / L",
            "Conditional rate",
            "Cluster 95% CI (%)",
            "All-assignment bounds (%)",
        ],
        [
            [
                tag.title(),
                f"{c['conditional_mismatch']['numerator']}/{c['conditional_mismatch']['denominator']}",
                pct(c["conditional_mismatch"]["estimate"]),
                interval(c["conditional_mismatch"]["bootstrap95"]),
                interval(c["full_assignment_conditional_mismatch_bounds"]),
            ]
            for tag, c in r["cohorts"].items()
        ],
    )
    policy = mdtable(
        ["Policy", "Valid stress", "G", "F", "Y"],
        [
            [
                p,
                original["primary"]["arms"][p + "-stress"]["VALID"],
                original["primary"]["arms"][p + "-stress"]["legitimate_complete"],
                original["primary"]["arms"][p + "-stress"]["forbidden_history"],
                original["primary"]["arms"][p + "-stress"]["joint_safe_completion"],
            ]
            for p in ["P0", "P1", "P2", "P3"]
        ],
    )
    debt_table = mdtable(
        ["Induced duty", "Triggered", "Observed discharge", "Outstanding at censoring"],
        [
            [
                "Service reopening",
                d["types"]["SERVICE_REOPEN"],
                checks["discharged_by_type"]["SERVICE_REOPEN"],
                checks["outstanding_by_type"]["SERVICE_REOPEN"],
            ],
            [
                "Approved request resubmission",
                d["types"]["APPROVED_REQUEST_RESUBMIT"],
                checks["discharged_by_type"]["APPROVED_REQUEST_RESUBMIT"],
                checks["outstanding_by_type"]["APPROVED_REQUEST_RESUBMIT"],
            ],
        ],
    )
    effect_table = mdtable(
        [
            "Intervention vs browser 0",
            "Matched source clusters",
            "Change in F (pp)",
            "Source 95% CI (pp)",
            "Missing bounds (pp)",
        ],
        [
            [
                str(c["treatment"]),
                c["complete_source_clusters"],
                f"{100 * c['estimate']:.2f}",
                interval(c["source_bootstrap95"]),
                interval(c["unknown_bounds"]),
            ]
            for c in actuator["contrasts"]
        ],
    )
    linux_steps = mdtable(
        ["Linux command", "Exit code", "Seconds"],
        [[s["name"], s["returncode"], f"{s['elapsed']:.1f}"] for s in linux["steps"]],
    )
    main = f"""# AfterClick: Admission, Irreversible Effects, and Restoration in Asynchronous Agent Workflows

Anonymous manuscript. 26 November 2026.

## Abstract

An agent can finish its local task after an external effect has already violated the task's authorization. Protecting a workflow also creates a second requirement: restoring legitimate functionality. We study these distinctions in two PostgreSQL-backed applications with progressing workers, browser interaction, and synthetic HTTP receivers. Our analysis preserves the complete disposition of a partially executed frozen evaluation: {primary["terminal"] + larger["terminal"] + external["terminal"]:,} of {primary["registered"] + larger["registered"] + external["registered"]:,} assignments have terminal records; {primary["not_run"] + larger["not_run"]:,} remain unexecuted. Among valid internal episodes with current local goals complete, forbidden effect history occurs in {primary["conditional_mismatch"]["numerator"]}/{primary["conditional_mismatch"]["denominator"]} primary-model and {larger["conditional_mismatch"]["numerator"]}/{larger["conditional_mismatch"]["denominator"]} larger-model episodes. A separately enrolled, fixed-recommendation actuator experiment records an increase of {100 * actuator["contrasts"][1]["estimate"]:.1f} percentage points in forbidden history for an imposed 300 ms browser delay. A source audit corrects an earlier interpretation: admission and protection already share a database lock. All {r["post_audit_cases"]["total"]} examined late-receipt cases instead show admission before protection. {boundary["registered"]} new barrier probes reproduce this non-revocable-ticket boundary. We reconstruct {d["duties"]} protection-induced restoration duties and replay all {replay["registered"]} available reviewer prompts; every replay chooses suspension, including publicly approved requests. These bounded measurements support history-aware evaluation and explicit restoration accounting. Incomplete enrollment, low clean competence, shared synthetic workloads, and missing causal information controls prevent a general controller or neural-latency superiority claim.

## 1. Introduction

A successful browser response is an observation of an operation, not the whole consequence of executing it. A worker may authorize a request, issue a durable ticket, and deliver an irreversible effect while the agent continues planning. A later protection command can commit successfully after the decisive admission has occurred. Conversely, a command that blocks a pending request can preserve safety while leaving an approved task unfinished. The relevant evaluation therefore spans local task state, effect history, timing boundaries, and legitimate restoration.

This study asks four questions. RQ1 asks how often current local completion coexists with forbidden history, and whether those cases contain an observed corrective action. RQ2 asks what a controlled increase in enforcement delay changes when recommendation and continuation are fixed. RQ3 asks which restoration duties protection activates and which are actually discharged. RQ4 asks what historical reviewer decisions and timing records establish about additional deliberation.

The contribution is a bounded measurement and reproducibility study. We provide separately implemented evidence checks, an audit of every state/history mismatch, obligation-level debt witnesses, and explicit assignment bounds. The source audit is substantively important: a previous description suggested an unlocked authorization-read/controller-write race. The released implementation already uses a common PostgreSQL advisory transaction lock. Our new probes validate a different mechanism: a ticket admitted under serialized state remains deliverable after containment. This correction changes the causal explanation without changing the original outcomes.

The distinction between state and effect history is established in prior work. UndoBench already evaluates state and wire-level effects [1], Cordon explicitly stages irreversible effects before release [2], and execution-monitoring theory distinguishes controllable from observable events [7]. AfterClick measures these boundaries in its own constructed workflows and exposes the limits of inferring recoverability from selected trajectories. It does not claim a new enforcement theorem, general recovery algorithm, or superior agent controller.

## 2. Testbed, trust boundary, and outcomes

### 2.1 Applications and task contracts

FlowBoard stores versioned business tasks, dependency edges, scoped capability grants, and approval comments. OpsConsole independently implements work orders, assets, capacity, scopes, and approval transitions. Their business tables and mutation engines differ; audit, synthetic receiver, benchmark vocabulary, and policy orchestration are shared infrastructure. They are two application environments, not two independently designed benchmark populations.

The historical catalog contains 72 DEV and 216 TEST contracts across six business-policy families, two applications, and three configured complexity levels. Reference workflows include dependency chains, alternative scopes, approval waiting, collaborator preservation, uncertain acknowledgments, authorized resubmission, and preexisting restoration operations. Each catalog contract has two executed browser reference witnesses. The qualification artifacts contain 576 witnesses and 10,944 rejected evidence mutations; those are automated checks, not independent human task review. Six policy vocabularies and 24 structural layouts are reused. Configured workflow complexity must not be read as demonstrated long-horizon model competence.

Workers progress while model requests, browser actions, and protection execute. Effects are persisted by an HTTP receiver outside the actor's ordinary business-state view. Examples include synthetic notices, restricted-record exports, delegated reads, non-refundable capacity consumption, and service commitments. These effects exercise real HTTP and SQL persistence. They do not send real customer messages, disclose actual confidential records, or model human cognition. PostgreSQL schemas are isolated with `ac_*` names. Snapshot reads support evidence and sibling comparison; snapshot replacement is not a live recovery action.

![Figure 1. Actor-visible observations, protection, serialized admission, and the separate receiver boundary. The evaluator observes durable evidence that the actor does not receive. A response-return stamp is an upper bound after commit; audit insertion occurs inside a transaction.](figures/f1-boundaries.png)

### 2.2 Visibility and authority

The actor receives public policy documents, business records, service status, and native tool results. Controllers use declared public authorization predicates or the same public observations. Evaluators separately inspect hidden contract choices, final tables, receiver records, and scheduling evidence. Neither oracle judgments nor future scheduler state are sent to the model. Evaluator-derived debt labels and forensic graph labels are retrospective evidence, never live hints.

Ambiguous authorization can be resolved through public signed verification. Under the benchmark's explicit pending-service rule, visible approved authority permits the pending service; unresolved or prohibited authority calls for reversible suspension. This narrow rule is distinct from whether every other operation in a complex workflow has completed. Human validation of the natural-language policy and public/private consistency remains outstanding, so disagreements below are stated relative to this implemented rule.

### 2.3 Separate outcome definitions

Let L denote the native current-local-goals-complete indicator. Let G denote independently checked legitimate task completion, including required operations, preservation, legitimate service availability, reconciliation, and approved pending delivery. F denotes the presence of a forbidden effect in durable history, supported by matching receiver and physical-effect records. Joint safe completion is Y = G and not F. Invalid or unexecuted trials have unknown scientific outcomes; they are not assigned F=0 or Y=0.

The definitions of L and G are kept separate even though their observed labels agree in all {n["valid"]} valid internal episodes. Such agreement is a property of these data and oracles, not a general equivalence theorem. A local/history mismatch is L=1 and F=1. It becomes an observed repair case only when the trace contains the relevant incorrect state and a subsequent corrective operation. Ordinary successful completion alone does not establish error recovery.

## 3. Enrollment, provenance, and analysis

### 3.1 Preserve the frozen evaluation

The original TEST protocol and its source/gate hashes were frozen before TEST. The registered core and supplementary cohorts were reduced prospectively under the old budget, but the reduced matrix was itself only partly executed. The full original disposition remains:

{enrollment}

The official external cohort uses a separate benchmark oracle and is not pooled with internal validity labels. Every internal terminal record is retained, including {primary["invalid"] + larger["invalid"]} invalid episodes. No missing assignment is replaced by a new prompt replay or mechanism probe. The original release, older studies, financial records, and negative results remain preserved.

The internal primary model is Qwen3.5-9B. The supplementary larger model is Qwen3.6-35B-A3B-FP8 on a fixed 36-source subset. Model family/revision, active parameterization, precision, hardware, and serving differ; the comparison cannot isolate parameter count. Primary clean joint success is {original["primary"]["arms"]["P0-clean"]["joint_safe_completion"]}/{original["primary"]["arms"]["P0-clean"]["VALID"]} valid episodes. The larger cohort's clean result is {original["larger"]["arms"]["P0-clean"]["joint_safe_completion"]}/{original["larger"]["arms"]["P0-clean"]["VALID"]}. These competence limits motivate a descriptive paper rather than a broad intervention-win claim.

### 3.2 Provenance and independent implementation

Read-only adapters normalize {n["internal_terminal_episodes"] if "internal_terminal_episodes" in n else primary["terminal"] + larger["terminal"]:,} internal terminal episodes. Rows preserve native IDs, cohort, outcome status, raw path, SHA-256, JSON pointer, and clock-domain qualification. The independent pointer checker verifies {normal["raw_files_verified"]:,} raw files, resolves {normal["resolved_pointers"]:,} pointers, and checks all {normal["physical_case_witnesses"]} mismatch-case physical witnesses. Separately coded local/history logic agrees with the native valid-episode labels; the earlier independent full-outcome verifier also records zero disagreements. These are independent software implementations operated in the same research process, not independent human adjudication.

### 3.3 Statistical units and missing outcomes

The new RQ1 analysis is explicitly retrospective on opened data. It uses 10,000 deterministic bootstrap draws, resampling whole source-task clusters, with worlds nested within a source. Its estimand is the episode-pooled conditional mismatch rate within observed valid data. Shared mechanisms limit the effective diversity beyond the nominal source count. Application and family leave-one-out results are supplied rather than treating episodes as independent tasks.

The original controlled-delay and policy analyses retain their frozen source-weighted estimators. We distinguish bootstrap intervals conditional on observed valid support from worst-case bounds over the full registered assignments. Bounds assign unknown outcomes adversarially and make no missing-at-random assumption. In sparse stratified cells, a point bootstrap interval can reflect a zero-variance sampling design rather than certainty. We retain studentized/sign diagnostics and unidentifiable mixed-model outcomes instead of manufacturing finite coefficients. No new outcome-selected significance test or tuning of frozen TEST is performed.

## 4. RQ1: local completion and irreversible history

Figure 2 shows both L by F cross-tabs. Conditional on local completion, mismatch rates are:

{mismatch}

![Figure 2. Current local completion versus forbidden history, using only valid internal episodes. The primary and larger cohorts retain separate denominators. L and G coincide empirically here; their definitions remain distinct.](figures/f2-state-history.png)

All {primary["conditional_mismatch"]["numerator"] + larger["conditional_mismatch"]["numerator"]} mismatch cases have individually linked persisted receipts and physical content. The primary joint mismatch rate is {pct(primary["joint_mismatch"]["estimate"])} of all valid episodes; the larger-cohort joint rate is {pct(larger["joint_mismatch"]["estimate"])}. Conditioning on L substantially changes the question, which is why both numerators and both denominators are reported. Broad missing-outcome bounds prevent extrapolating the conditional rates to the uncompleted registered population.

The trace audit finds no wrong-to-correct business-commit sequence in these cases. Most are ordinary local completion with forbidden prior history, not evidence of a repair algorithm. Three cases additionally contain observed containment followed by service reopening: two primary FlowBoard cases and one larger-model OpsConsole case. Their raw trigger and discharge pointers appear in the case atlas. The historical scripted actuator cohort provides a separate, stronger service-restoration witness: all {verified["valid"]} valid reference continuations contain containment and reopening, including {verified["restored_with_forbidden_history"]} with forbidden history. Scripted restoration and autonomous LLM restoration remain separate denominators.

These findings show that current business completion or restored service cannot erase an already recorded forbidden effect. They do not prove that every unsuccessful trajectory was unrecoverable, that every locally complete trajectory repaired an error, or that these synthetic effect rates describe production agents.

## 5. RQ2: enforcement delay and the admission boundary

### 5.1 Existing controlled actuator experiment

The independently enrolled controlled study executes {actuator["registered"]} branches on 12 constructed L3 DEV sources, two seeded worlds, three configured admission offsets, and four gateway/delay arms. The same public suspension recommendation is fixed before the imposed delay. Independent workers and actual browser/HTTP reference continuations execute in every arm. All branches have terminal records; {actuator["valid"]} are valid and one remains invalid. Independent hashing confirms every reconstructed initial cut rather than trusting a stored validity Boolean.

{effect_table}

![Figure 3. Left: actual forbidden-history counts over valid branches at each configured offset and gateway delay; the single invalid branch remains explicitly unknown. Right: original source-paired effect estimates with source bootstrap intervals. Configured admission offsets are not measured individual prevention deadlines.](figures/f3-actuator.png)

At fixed information and recommendation, additional browser delay raises forbidden-history incidence in the short-slack cells. The 1,800 ms cells show no forbidden effects under these configured interventions. The near-zero HTTP/browser contrast has a confidence interval spanning both signs. These are effects of the imposed gateway intervention and the executing local runtime under its recorded load. The experiment does not isolate neural inference time, estimate a universal deadline, or validate a deployment-grade latency budget.

### 5.2 Corrected source interpretation and new probes

The legacy database transaction obtains a per-schema PostgreSQL advisory transaction lock. Admission and controller writes share it. FlowBoard's transaction-bound wrapper and the runner's migration wrapper preserve this lock. Consequently, the blanket hypothesis of an unlocked read/modify/write race is unsupported by the released source.

A different gap remains: a pending ticket admitted in one transaction can later be delivered even after suspension or cancellation commits. The receiver does not revalidate the current containment state for that already-admitted ticket. In all {r["post_audit_cases"]["total"]} historical post-protection-audit violations, the same-effect admission audit precedes the protection audit. Matching action responses also place the physical receipt after the recorded protection commit-return upper bound. The original traces do not contain exact authorization-read or SQL commit instants. This ordering is a source-supported interpretation of persisted identities and transaction serialization, not a reconstructed exact original read timestamp.

![Figure 4. The lexicographically first audited late-receipt case. The protection band spans audit insertion to commit-return upper bound. Admission is already recorded before that band; the receiver persists the effect later. All examined cases, including different elapsed spans, are available in the forensic atlas.](figures/f4-forensic-interval.png)

We prospectively register a finite mechanism-probe matrix after two-application DEV validation. Its {boundary["registered"]} branches reuse the 12 open DEV sources and cross three engineered schedules with suspension/cancellation. A wrapper preserves the original transaction context while recording process identity, clock domain, lock acquisition, authority-read return/version, and commit-return bounds. One barrier holds the original schema lock while the controller attempts acquisition. Actual worker threads, PostgreSQL transactions, and HTTP receivers execute; no model is invoked. All {boundary["registered"]} probes are valid: pre-admission protection prevents the effect in 24 branches, whereas {boundary["pending_received"]} branches with admission or receipt before protection retain the effect. These are mechanism tests on reused sources, not an independently authored benchmark, randomized delay replication, receiver-side fencing implementation, or power-backed population study.

## 6. RQ3: protection-induced restoration obligations

The analysis separates preexisting business duties from protection-induced duties. A contract-required business `restore` operation exists before containment. A service-reopening duty is activated by an observed false-to-true suspension transition. An approved-request resubmission duty is activated when protection causes admission of an approved pending request to be denied. It is discharged only by an observed request-requeueing Resume transition. Reopening alone does not establish approved delivery, which remains a separate legitimate-task obligation.

{debt_table}

The independent reconstructions agree on all {checks["service_items_exactly_agree"]} service-duty trigger/discharge identities. Together the {d["duties"]} induced duties have {sum(checks["discharged_by_type"].values())} observed discharges and {sum(checks["outstanding_by_type"].values())} outstanding censored items. At most {d["max_concurrent"]} unit-weight duties are simultaneously active in the observed per-episode duty model. We supply dependency commands, trigger and discharge pointers, D(t) components, maximum debt, and debt area over the observed backend audit span. Exact commit-to-commit durations and complete termination horizons are unavailable; censored spans are lower-bound exposure, not a Kaplan-Meier estimate of a stable population distribution.

![Figure 5. Left: primary stress-cohort legitimate completion, absence of forbidden history, and joint success counts. Denominators differ across policy bundles, so these marginal rates are descriptive. Right: observed discharge versus outstanding censoring for two induced-duty types across both valid internal cohorts.](figures/f5-obligations.png)

{policy}

P1 can prevent a pending effect while leaving service suspended, and P3 can suspend an approved request while the underlying business plan remains incomplete. Those mechanisms do not make every incomplete task a restoration failure. The audit separately labels failed business obligations, approved-pending omission, reconciliation, preservation, and final service restoration. Labels can overlap within an episode. Conditioning on a containment transition selects a mediator of policy behavior, so the debt comparison is descriptive. P4's restoration checks are also a bundled intervention on a small selected support; neither marginal rates nor the matched observational table establish a causal benefit of a restoration reminder. A matched no-restoration-needed/reminder factorial was not executed.

## 7. RQ4: what additional review establishes

The historical traces contain {reviews["requests"]} actual reviewer responses: {reviews["by_cohort"]["primary"]["requests"]} primary and {reviews["by_cohort"]["larger"]["requests"]} larger-model requests. All are strict JSON; all choose `suspend`. The actor runner processes {reviews["processed"]} of them, leaving {reviews["requests"] - reviews["processed"]} received responses unprocessed. Parser validity and controller application therefore have different denominators. {reviews["approved_inputs_suspended"]} inputs visibly mark the pending authority approved, yet the reviewer suspends them; {reviews["approved_inputs_suspended_and_processed"]} of these recommendations are processed. These are disagreements with the declared pending-service public rule. They are not a human judgment about all surrounding natural-language policy obligations.

Observed reviewer HTTP intervals have median {reviews["http_interval_quantiles"][2]:.2f} seconds, interquartile range {reviews["http_interval_quantiles"][1]:.2f} to {reviews["http_interval_quantiles"][3]:.2f} seconds, and 95th percentile {reviews["http_interval_quantiles"][4]:.2f} seconds. They include transport, queueing, and serving overhead, and are not isolated neural inference measurements. Raw explanations often discuss other unfinished workflow requirements, approval uncertainty, or receipt reconciliation. Decision content and timing both differ from a narrow deterministic pending-service rule.

The frozen primary P3-minus-P2 joint-success contrast on complete observed source support is {100 * old_contrast["primary"]["complete_pair_estimate"]:.2f} percentage points, with source bootstrap interval {interval(old_contrast["primary"]["source_stratified_bootstrap95"])}. Its full-assignment unknown bounds are {interval(old_contrast["primary"]["assignment_bounds"])} percentage points. Thus a selected-support policy-bundle association cannot establish a population effect, and certainly not a pure latency effect.

![Figure 6. Conditional sampling intervals and full-assignment unknown bounds answer different questions. The larger policy contrast has a degenerate stratified bootstrap interval; this is not evidence of precision or equivalence.](figures/f6-uncertainty.png)

To check decision reproducibility, a separate finite new-account job replays every available historical reviewer input once through the same pinned primary 9B weights. It preserves message content and generation settings, changing only the served model alias. All {replay["registered"]} requests receive strict JSON, consume {replay["known_tokens"]:,} reported tokens, and again choose suspension. There are zero unknown responses. The {reviews["by_cohort"]["primary"]["requests"]} primary inputs are a same-weight serving-stack reproducibility diagnostic; the {reviews["by_cohort"]["larger"]["requests"]} larger-model inputs are cross-model prompt replay through 9B. They are not fresh TEST cases, live actor trajectories, counterfactual world continuations, or evidence of clean agent competence. This repeat supports the decision-content finding under the new serving setup, without isolating why the model chooses suspension.

Cached-equivalent review, irrelevant verification, latency-matched deterministic review, and informative-access factorial controls remain unexecuted. The paper therefore reports associated review outcomes and a separately controlled actuator effect, not the causal value or harm of additional LLM deliberation.

## 8. Recoverability and related work

The evidence graphs distinguish actual executed transitions, acknowledged controller commands, processed reviewer responses, and reference sibling continuations. A certified quiescent initial cut can support a witnessed safe sibling when that sibling was actually executed. It does not certify arbitrary in-flight JavaScript, reconstruct an unexecuted mid-trajectory branch, or establish robust recovery from every possible hidden state. Most intermediate prefixes remain UNKNOWN. A fixed forbidden-history prefix is incompatible with future Y under the modeled immutable-effect contract, even if local goals remain attainable. Formal certificates in small earlier finite models remain separate from the complex LLM trajectory graphs, where the formal-certificate count is zero.

UndoBench [1] already separates competence and recovery and observes both state and external effect history, including lost acknowledgments and different mutation phases. The official external subset here uses its released history-aware evaluator with five configured strategy wrappers; it is a supplementary comparison on 12 base tasks, not a reproduction of all published experiments or a new version of its oracle. Cordon [2] provides a task-level staging/validation boundary and recovery metadata. AfterClick's P5 suspension-first queue hold is a proxy, not a semantic transaction or an implementation of Cordon.

Async-RBench [3] evaluates responses to asynchronous result arrival with explicit change, preservation, avoidance, and reverification contracts. ReInBench [4] studies error events and self-recovery rather than equating terminal completion with a corrective action. Safe to Resume? [5] analyzes inconsistencies across checkpoint restoration and external dependencies. AgentTrust [6] interposes runtime rules and LLM judgments at tool execution. Basin et al. [7] formalize the relevance of controllable versus merely observable events. The shared issues of timing, history, and enforcement boundary are established. The present contribution is the traceable measurement, corrected source explanation, and restoration-duty accounting in this testbed; a broad novelty or priority claim would exceed the evidence.

## 9. Reproduction, limitations, and availability

The archived original contains 151,623 payload files plus its release manifest and remains unchanged. A separate candidate recompresses it and adds audit metadata. The audit expands {candidate["expanded_members_audited"]:,} outer/nested members, finds zero matches for its credential patterns, and changes zero original file payloads. Pattern scanning is not proof that arbitrary sensitive information cannot exist. The candidate is local; no public asset URL, DOI, or newly granted open data license is claimed. Its exact digest and restore instructions are in the companion appendix. Prior-source and third-party licenses must be respected; model weights are not redistributed.

Independent cloud Linux executions restore the audited archive at a relocated path, check every payload, and run the recorded saved-data, oracle, graph, timing, obligation, and regression commands under network-blocked Modal Sandboxes. The initial archive-only setup misses test prerequisites; a separate complete source snapshot with locked frontend builds supplies them. It injects no provider credentials and makes zero model/provider calls. This is independent automated execution on another machine, not an independently operated human reproduction. Its actual exit codes, environment, test results, and all errors are reported in Appendix A. A missing or failed check is not represented as a pass. New-account conservative accounting is ${finance["guard_accounted_usd"]:.4f} within a $28 cap, with cash billed ${linux_lifecycle["cash_billed_usd"]:.2f}; the historical $18 ledger remains separate.

Limits are substantial. The old evaluation is incomplete, with outcome-dependent execution order and no assumption that missing assignments resemble observed ones. Invalidity and clean competence limit policy comparisons. Constructed applications share mechanisms and layouts, and independent human authority/oracle review is absent. Original clock origin/process identity and exact commit/read boundaries are incomplete. New barrier instrumentation cannot backfill those historical measurements. The mechanism probes reuse open DEV tasks; the prompt replay uses opened observations. Neither is a new independent holdout. No exact mid-trajectory counterfactual continuation, realistic adversarial domain validation, or complete information/restoration factorial was added. The statistical intervals describe selected support and source sampling assumptions. General model scale, controller superiority, and production security guarantees remain unsupported.

## 10. Conclusion

In this testbed, completed local goals and restored service can coexist with durable forbidden history. Imposed actuator delay changes outcomes when admission progresses, and protection after serialized admission cannot recall the legacy ticket. Containment also activates duties whose discharge must be witnessed separately from ordinary completion. Historical and repeated reviewer outputs show that decision content is a material part of the policy bundle, preventing a latency-only explanation. The supported result is a bounded empirical account with explicit unknowns and a reproducible audit trail, not completion of the original experimental program.

## References

[1] Dolly Sah, Tanmay Sah, Harshul Jain, and Tanya Sah. 2026. UndoBench: Separating Task Competence from Recovery Capability in Tool-Using AI Agents. [arXiv:2610.05622](https://arxiv.org/abs/2610.05622).

[2] Zheng Chen, Hanqing Liu, Duling Xu, Dong Dong, Jialin Li, Bangzheng Pu, and Jidong Zhai. 2026. Cordon: Semantic Transactions for Tool-Using LLM Agents. [arXiv:2606.17573](https://arxiv.org/abs/2606.17573).

[3] Detao Zeng et al. 2026. Async-RBench: Benchmarking Asynchronous Task Execution in LLM Agents. [arXiv:2610.32429](https://arxiv.org/abs/2610.32429).

[4] Chiming Duan et al. 2026. When to Intervene? An Empirical Study of Errors and Self-Recovery in LLM Agents. [arXiv:2610.36471](https://arxiv.org/abs/2610.36471).

[5] Guanlong Wu et al. 2026. Safe to Resume? Breaking Execution Continuity of Agent Execution via Rollback. [arXiv:2608.29381](https://arxiv.org/abs/2608.29381).

[6] Chenglin Yang. 2026. AgentTrust: Runtime Safety Evaluation and Interception for AI Agent Tool Use. [arXiv:2605.04785](https://arxiv.org/abs/2605.04785).

[7] David Basin, Vincent Juge, Felix Klaedtke, and Eugen Zalinescu. 2012. Enforceable Security Policies Revisited. POST, pp. 309-328. [DOI:10.1007/978-3-642-28641-4_17](https://doi.org/10.1007/978-3-642-28641-4_17).
"""
    arms = []
    for tag, report in original.items():
        for name, c in sorted(report["arms"].items()):
            arms.append(
                [
                    tag,
                    name,
                    c["registered"],
                    c.get("VALID", 0),
                    c.get("INVALID", 0),
                    c.get("NOT_RUN", 0),
                    c["legitimate_complete"],
                    c["forbidden_history"],
                    c["joint_safe_completion"],
                ]
            )
    external_table = mdtable(
        [
            "Wrapper",
            "Control success / 24",
            "Fault success / 24",
            "Capable controls",
            "Conditional recovery",
            "Source 95% CI (%)",
        ],
        [
            [
                m["method"],
                m["control_success"],
                m["fault_success"],
                m["control_capable_pairs"],
                pct(m["conditional_recovery_success"]),
                interval(m["conditional_task_bootstrap95"]),
            ]
            for m in external["methods"]
        ],
    )
    model = load(data.parent / "v12/model-comparison/report.json")
    model_table = mdtable(
        [
            "Arm",
            "Common source clusters",
            "Larger minus primary (pp)",
            "Studentized 95% CI (pp)",
            "Assignment bounds (pp)",
        ],
        [
            [
                x["arm"],
                x["complete_source_clusters"],
                f"{100 * x['larger_minus_primary_source_mean']:.2f}",
                interval(x["studentized95"]),
                interval(x["full_assignment_bounds"]),
            ]
            for x in model["contrasts"]
        ],
    )
    prefix = {
        tag: load(data.parent / f"v12/{tag}-recoverability-prefixes/report.json")
        for tag in ["primary", "larger"]
    }
    graph_table = mdtable(
        [
            "Cohort",
            "Prefix nodes",
            "Unknown",
            "Witnessed safe initial",
            "Realized safe final",
            "Formal certificates",
        ],
        [
            [
                tag,
                p["nodes"],
                p["labels"].get("UNKNOWN", 0),
                p["labels"].get("WITNESSED_SAFE_INITIAL_CONTINUATION", 0),
                p["labels"].get("REALIZED_SAFE_COMPLETION", 0),
                p["formal_certificates_in_complex_graph"],
            ]
            for tag, p in prefix.items()
        ],
    )
    full_arms = mdtable(
        ["Cohort", "Arm", "Enrolled", "Valid", "Invalid", "Not run", "G", "F", "Y"], arms
    )
    all_contrasts = mdtable(
        [
            "Cohort",
            "Contrast",
            "Complete source clusters",
            "Estimate (pp)",
            "Cluster CI (pp)",
            "Assignment bounds (pp)",
        ],
        [
            [
                tag,
                c["contrast"],
                c["complete_pair_source_clusters"],
                (
                    "UNKNOWN"
                    if c["complete_pair_estimate"] is None
                    else f"{100 * c['complete_pair_estimate']:.2f}"
                ),
                interval(c["source_stratified_bootstrap95"]),
                interval(c["assignment_bounds"]),
            ]
            for tag, rr in original.items()
            for c in rr["contrasts"]
        ],
    )
    appendix = f"""# AfterClick: Experimental and Reproducibility Appendix

Anonymous companion to the current manuscript. Generated from the same evidence manifest.

## A. Independent Linux execution

Actual platform: {env["platform"]}. Python: {env["python"]}. Relocated source root: `/work/afterclick-v12`. PostgreSQL uses the 17.7 base image; Python dependencies are exported without re-resolution from `uv.lock`. Chromium and OS dependencies are installed in the image before the network block. Runtime outbound access is blocked by the sandbox policy; PostgreSQL and HTTP receivers run on loopback. No inference or cloud SDK is invoked by the reproduction payload. Parent-side authenticated Modal transfer is separately recorded.

{linux_steps}

Preserved history all-step status is `{linux["all_steps_passed"]}` because earlier failed attempts remain. Final required-check status after corrections is `{linux["final_required_checks_passed"]}`. The archive-only suite recorded {linux["original_archive_only_regression"]["passed"]} passes and {linux["original_archive_only_regression"]["failed"]} failures across {linux["original_archive_only_regression"]["tests"]} tests. The complete-source suite then recorded {int(linux["corrected_full_regression"]["tests"]) - int(linux["corrected_full_regression"]["failures"])} passes and {linux["corrected_full_regression"]["failures"]} failures across {linux["corrected_full_regression"]["tests"]} tests, all naming one omitted archived smoke-input fixture. Restoring that fixture unchanged and rechecking every failure gave {linux["missing_fixture_followup"]["pytest"]["tests"]} passes and {linux["missing_fixture_followup"]["pytest"]["failures"]} failures. Thus {linux["cumulative_distinct_tests_passed"]} distinct cases passed across the full run and follow-up; no single all-passing full-suite run is claimed. These are terminal results, not anticipated checks. The machines are external to the author's workstation; the operator remains the same automated research process. Independent human policy review, annotation agreement and unguided researcher reproduction have not been performed.

The first archive-only regression lacked `fixtures/` and the generated OECR client. A separate corrected run uses a complete Git source snapshot and independently builds both clients from the locked npm dependencies before runtime network isolation. The old archive remains unchanged and must be used alongside a full checkout. An initial launch failed before resources were created because an unsupported SDK keyword was used; its source, error, empty-app proof and finance reconciliation remain. Corrected v2 is a separate finite run. Earlier parser attempts, a list-versus-Boolean actuator check, a relative-path error, and original negative research runs remain in the artifacts. No native outcome, regression assertion or frozen experimental source was weakened to obtain a pass.

## B. Exact enrollment and policy semantics

{enrollment}

{full_arms}

P0 is actor-only execution; clean P0 is separately enrolled. P1 applies fast deterministic pending-service containment. P2 adds fast public verification/guards without a second LLM reviewer. P3 adds sequential reviewer inference. P4 adds explicit public legitimate-task restoration feedback/checks on a focused subset. P5 is suspension-first queue holding with LLM review on a focused subset; it is not a general semantic staging implementation. Controls can fail, be late, contain an approved task, or remain unprocessed. The same native tools and real effect history are evaluated. Exact prompt/tool definitions and per-arm budgets are preserved in the frozen source and registration.

The full benchmark implements 72 DEV and 216 TEST sources. All 216 TEST sources have reference qualification, but primary terminal evaluation covers only 185 sources. A qualified reference task, an executed agent assignment, a valid assignment, and a safe completion are four different quantities. Completion of the appendix does not close the {primary["not_run"] + larger["not_run"]} missing original assignments.

## C. Statistics and sensitivity

{all_contrasts}

The larger P4/P5 arms were not enrolled; their contrasts remain unestimated (UNKNOWN), not zero performance. The historical primary contrast is P3 minus P2 in joint safe completion. Original bootstrap seed is 8261125, with 10,000 source draws stratified by application/family/complexity. Policy estimates weight source means rather than treating every world as an independent task. A singleton or zero-variance stratum can yield a point interval; source sign/studentized diagnostics, assignment bounds and the design limitation remain necessary. Secondary contrasts retain the original multiplicity adjustments. The supplementary mixed model reports separation/unidentifiability or optimization warnings rather than reliable finite Wald effects. Model coefficients are not used as headline evidence.

The post hoc mismatch bootstrap uses seed 11262026 and 10,000 unstratified whole-source draws. Support is {primary["conditional_mismatch"]["source_clusters"]} valid primary source clusters and {larger["conditional_mismatch"]["source_clusters"]} larger clusters. Its ratio is the number of observed valid L=1,F=1 episodes divided by observed valid L=1 episodes. For missing-outcome conditional bounds, unknown assignments may contribute an L=1,F=0 denominator at the lower extreme or L=1,F=1 at the upper extreme. These bounds differ from unconditional joint mismatch bounds, supplied in the machine-readable report. Leave-one-family/application-out rates and all strata remain available.

The original source-clustered power analysis was frozen before TEST and disclosed poor power near a zero-success floor. No post hoc sample extension is represented as prospectively powered. The new 72-branch study is an engineered schedule validation with deterministic expected boundary behavior; it makes no population power claim. The all-input reviewer replay is a census of available historical prompts, not an independent source sample. Optional 576-branch delay replication, 384-branch information factorial and live restoration factorial were proposed but not registered or executed in this publication phase.

## D. Every state/history mismatch and timing witness

The companion `analysis/cases/` contains all 65 mismatch case cards with raw SHA-256 and JSON pointers. The JSONL audit distinguishes ordinary local completion from observed containment/service reopening. Exactly three LLM cases have the latter witness; no case is promoted to wrong-business-state repair without a corrective business commit. All 77 scripted actuator cases with restoration and forbidden history have their own trigger/discharge rows in the actuator verification table.

All 34 late-receipt cases are represented in `rq4-refined-ordering.csv` and the forensic SVG atlas. Each row names the effect ID, admission event, first protection event, unique browser-action join, commit-return upper bound, receipt, file hashes and interpretation. Exact original worker authorization-read and SQL commit timestamps remain unknown. The authority-read event in the new probes is explicitly a measured return boundary, not the instant at which PostgreSQL executed the SELECT. Commit-begin and commit-return span commit; neither is falsely presented as an exact SQL commit instant.

The 72-branch probe registration precedes its confirmation execution and follows 12 successful DEV probes. It crosses 12 reused open DEV task contracts, three orderings and two commands. Before-admission arms execute protection then worker admission. Admission-before-protection arms hold the original worker schema lock while the controller attempts its lock, then release admission and permit protection to complete before delivery. Receipt-before-protection arms persist the effect first. Future delivery is advanced with the ordinary worker method and actual elapsed-time eligibility, not snapshot restoration. Every world uses a fresh `ac_*` schema and is dropped only after evidence is saved.

## E. Restoration duty schema and observed exposure

{debt_table}

A duty has episode ID, type, unit weight, trigger identity/pointer, dependency commands, optional discharge identity/pointer, observed monotonic span, final censoring label, and raw file hash. Service reopening is triggered by containment and discharged by an actual true-to-false service transition. An approved resubmission duty is triggered by an actual denied admission of an approved request and discharged by a Resume transition that requeues the canceled request. Verify is a public precondition, and approved eventual delivery remains a separate task objective. Thus service reopening and resubmission can be active together without conflating them.

`episode-debt.csv` records the maximum concurrent unit debt, observed debt area, and unresolved items. Exposure ends at the final recorded backend audit event, not a presumed exact termination timestamp. Censored rows are not assigned fictitious discharge times. Unequal horizons and policy-dependent containment selection make cross-policy debt-area comparisons descriptive. Preexisting operation DAGs, ordinary failures and all multi-label failure rows remain in the full derived evidence; the compact Git data intentionally omit large event/model-request tables.

## F. Reviewer reproducibility and resource accounting

Historical requests: {reviews["requests"]}; schema-valid: {reviews["schema_valid_all_received"]}; processed: {reviews["processed"]}; unprocessed received: {reviews["requests"] - reviews["processed"]}. All choose suspension. Approved inputs suspended: {reviews["approved_inputs_suspended"]}, including {reviews["approved_inputs_suspended_and_processed"]} processed. JSON parsing therefore does not explain the repeated suspension decisions. Raw free-text reasons are evidence for exploratory hypotheses about input interpretation, not blinded causal annotation.

New replay: {replay["attempted"]} attempts, {replay["received"]} received, {replay["unknown"]} unknown, {replay["strict_json"]} schema-valid, {replay["known_tokens"]:,} known tokens. There is one request per historical prompt, concurrency capped at eight, zero generation retries, a finite wall-time envelope, and minimum-zero endpoint cleanup. Primary weights are pinned to `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Prompt messages, temperature and token budget are unchanged; serving alias is new. All replies again suspend. The 66 original larger-model prompts are evaluated by the new 9B model and are identified as cross-model prompt replay.

Endpoint setup contributes two additional native tool/continuation calls and 814 known tokens; these are setup only. The old program's 41,732 call attempts and 309,714,800 known reported tokens remain a separate ledger with three unknown responses. Internal TEST alone has 22,423 request intents: 22,159 actor and 264 reviewer. These counts are not interchangeable with complete trajectories, received generations, or scientific assignment counts.

The historical $18 authorization has conservative accounting $17.96725281 and cash billing $0. The new workspace has a separate $28 total cap, workspace usage limit $28, and effective net cash spend limit $0. Actual new-phase conservative accounting is ${finance["guard_accounted_usd"]:.6f}; cash billed at closeout is ${linux_lifecycle["cash_billed_usd"]:.2f}. Reserved envelopes, measured resource bounds, metered costs and invoices are distinct quantities. Financial ledgers preserve failed attempts and append-only reconciliations. No Tinker credits or cash charges were authorized or used.

## G. Supplementary model/external comparisons and recoverability

{model_table}

The supplementary model comparison has a fixed 36-source common-support frame, but complete paired support varies by arm as shown. It is not a full second-model core replication. Revision, architecture, active parameterization, precision, hardware and serving differ; parameter count alone is not a causal treatment. A point interval at zero reflects no observed contrast on selected support and is not population equivalence. Full-assignment bounds retain missing outcomes. No general stronger-model advantage is established.

{external_table}

Each wrapper has 24 controls and 24 faults from 12 base tasks and two context seeds; all 240 registered external conditions execute. Names designate the configured strategy wrappers, not complete replications of separate published systems. Conditional recovery uses complete control-capable pairs. Intervals and paired seed/source evidence are preserved in the original external report. EvoUndo is unavailable and is not assigned an invented zero. A goal-only check is not substituted for the official state/history evaluator. This subset does not establish broad superiority over the published benchmark or reproduce its full study.

{graph_table}

`WITNESSED_SAFE_INITIAL_CONTINUATION` means an actually executed sibling at a certified quiescent initial cut, not recoverability from arbitrary intermediate prefixes. `REALIZED_SAFE_COMPLETION` is an observed endpoint. `FIXED_HISTORY_VIOLATION` retains the effect-history barrier under the immutable synthetic receiver contract. `UNKNOWN` means no executed/certified safe continuation is available for that prefix, not proof of impossibility. The new mechanism probes and prompt replay do not add counterfactual LLM continuation edges. Small earlier formal models and their certificates stay in separate historical artifacts.

## H. Artifact integrity, availability, and license status

Original release SHA-256: `c031afd3c46eab822770cc41e684d87f2a2aa786b64cff70eb79f90572667020`.

Audited local candidate SHA-256: `{candidate["sha256"]}`. Candidate size: {candidate["bytes"]:,} bytes. Original top-level members checked by audit: {candidate["original_top_level_members"]:,}; expanded members including nested archives: {candidate["expanded_members_audited"]:,}. Credential-pattern findings: {candidate["credential_findings"]}. Original payloads changed: {candidate["changed_top_level_files"]}. Archive container metadata/recompression differs, and the derivative adds its own manifest/README. Original source and data bytes are preserved separately. No anonymous/public raw upload, immutable release tag or DOI is represented as completed.

The credential audit rejects unsafe archive paths/links, expands bounded nested archives, and checks token/private-key patterns without logging matched values. Zero matches do not prove universal absence of sensitive information. The full original remains local. A public release needs explicit approval of this concrete candidate and a license choice. No blanket open-source or data license is invented; existing third-party terms continue to apply. Qwen3.5-9B's pinned model repository identifies Apache-2.0; weights are referenced, not redistributed. Official benchmark source and its notices remain preserved in the original archive.

The repository inventory classifies all 2,494 baseline tracked paths and records static dependency edges plus dynamic-path limitations. Catalogs v5/v6 are byte-identical across 289 JSON files, including catalog metadata, but retain distinct historical path roles and remain intact. Three superseded staging documents move byte-identically into history; two regenerable QA contact sheets are removed from Git while their originals remain in the local backup, original archive and base Git objects. Frozen source/gate paths, failed trials, old manuscripts and financial evidence are preserved. No new automated workflows or force-push are introduced. Current publication implementations now live in `research_ops/publication/analysis/`, with immutable registrations and scope documents in `registration/` and `protocols/`. Compatibility import/CLI wrappers preserve older invocations. `claim_evidence_matrix.csv`, the evidence index and data-schema document make the current structure explicit. Pinned legacy paper/runtime paths remain to preserve historical hashes and relative references.

## I. Supported reproduction

From the repository root, saved-data commands have no model/provider calls. They require the separately supplied archive for raw verification and full analyses; a source-only clone can regenerate the current manuscript/figures from compact reports. Dependencies use the existing lock and optional research group. Rendering additionally uses ReportLab; rendered page QA is recorded separately.

```sh
python -m research_ops.publication.program verify-data
python -m research_ops.publication.program reproduce-existing --output /tmp/ac-existing-new
python -m research_ops.publication.program analyze --output /tmp/ac-analysis-new
python -m research_ops.publication.program generate-paper
python -m research_ops.publication.program test
```

Real-PG mechanism demonstration is separate from saved-data analysis:

```sh
python -m research_ops.publication.program demo --output /tmp/ac-boundary-new
```

Cloud/inference runners require explicit `--execute`, separate finite registrations and available credits. They are not invoked by any saved-data command. Completed jobs must not be blindly relaunched. The companion claim registry binds numeric claims to generated JSON/CSV inputs and their hashes. All old unexecuted assignments and absent independent human gates remain explicit; an anonymous finished paper is not a declaration that the original research program is complete.
"""
    (out / "MANUSCRIPT.md").write_text(main)
    (out / "APPENDIX.md").write_text(appendix)
    claims = {
        "C01_enrollment": {
            "source": "analysis/report.json",
            "pointer": "/cohorts",
            "claim": "Complete registered disposition, not full execution",
        },
        "C02_mismatch": {
            "source": "analysis/report.json",
            "pointer": "/cohorts",
            "claim": "65 individually audited local/history mismatch cases",
        },
        "C03_actuator": {
            "source": "../v12/controlled-actuator/report.json",
            "pointer": "/contrasts",
            "claim": "Controlled imposed delay, no neural-only causal interpretation",
        },
        "C04_restoration": {
            "source": "checks/report.json",
            "pointer": "/independently_reconstructed_duties",
            "claim": "617 induced duty witnesses, 34 observed discharges",
        },
        "C05_review": {
            "source": "analysis/report.json",
            "pointer": "/reviewers",
            "claim": "264 historical suspend decisions;85 approved under benchmark rule",
        },
        "C06_ordering": {
            "source": "analysis/rq4-refined-ordering.csv",
            "pointer": "episode_key",
            "claim": "All34 admission audits precede protection; no exact original read/commit timestamp",
        },
        "C07_boundary": {
            "source": "boundary/report.json",
            "pointer": "",
            "claim": "72 passed engineered probes on reused DEV sources, not independent workload",
        },
        "C08_replay": {
            "source": "replay/report.json",
            "pointer": "",
            "claim": "264 new9B prompt replays, not live trajectories",
        },
        "C09_linux": {
            "source": "linux/report.json",
            "pointer": "/steps",
            "claim": "Actual terminal checks; not independent human review",
        },
        "C11_model_comparison": {
            "source": "../v12/model-comparison/report.json",
            "pointer": "/contrasts",
            "claim": "Supplementary common-support comparison; no model-scale-only causal effect",
        },
        "C10_data": {
            "source": "data-candidate.json",
            "pointer": "",
            "claim": "Local audited candidate, not public upload",
        },
    }
    for c in claims.values():
        c["source_sha256"] = hashlib.sha256((data / c["source"]).read_bytes()).hexdigest()
    (out / "CLAIM_REGISTRY.json").write_text(json.dumps(claims, indent=2) + "\n")
    (out / "BUILD.json").write_text(
        json.dumps(
            dict(
                anonymous=True,
                data_manifest_sha256=hashlib.sha256(
                    (data / "MANIFEST.json").read_bytes()
                ).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                manuscript_words=len(main.split()),
                appendix_words=len(appendix.split()),
                paper_complete=True,
                original_research_matrix_complete=False,
            ),
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            dict(
                manuscript_words=len(main.split()),
                appendix_words=len(appendix.split()),
                anonymous=True,
            )
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    build(a.data, a.output)
