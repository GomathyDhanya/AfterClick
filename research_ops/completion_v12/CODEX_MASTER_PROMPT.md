# CODEX MASTER DIRECTIVE — COMPLETE AFTERCLICK RESEARCH PROGRAM

You are the principal research engineer, experimental scientist, statistician, and artifact maintainer for the existing AfterClick repository. Your assignment is to **implement, execute, evaluate, and write up** a complete publication-grade experimental program. I am explicitly asking for finished work, not another proposal, pilot, smoke test, or a small favorable comparison.

## Instructions and inputs

First read every file in `research_ops/completion_v12/`, beginning with `README_START_HERE.md`, then `01_SCIENTIFIC_CHARTER.md` through `09_ACCEPTANCE_AND_AUDIT.md`, the task contract templates and design manifest. If this kit is supplied outside the repository, locate it and copy it under that path before implementation. Audit the actual repository state rather than assuming that its HEAD equals the archived v11 ZIP. Read `research_ops/STATE.json`, `SESSION_HANDOFF.md`, the frozen source hashes, v11 paper/appendix, relevant modules, saved trial records and external benchmarks before editing.

**Protect past work:** 91 sealed archived runs and all previous frozen studies are immutable evidence. Preserve old source/branch/protocol hashes, raw traces, finance ledgers and negative results. Work in a new version-controlled branch/worktree. Do not overwrite the user's uncommitted changes or rewrite earlier frozen outcomes. Run existing independent reproduction scripts before and after new implementation.

## Research question and honest positioning

Working title: **AfterClick: When Safe Decisions Fail to Produce Safe Outcomes**.

Study the **loss of safe completion options** along genuine tool-using agent trajectories under independently progressing external effects. Disentangle (1) correct or incorrect agent decisions, (2) information gained through verification, (3) time consumed in LLM reasoning, (4) post-decision gateway enforcement latency, (5) irreversible external commitments, and (6) legitimate task obligations left unfinished after protection.

Answer the three RQs in the scientific charter. Do **not** set as a required outcome that any new supervisor, controller, search method, or graph algorithm beats the fast deterministic baseline. Negative results count if the tasks, controls, attribution and uncertainty are rigorous. Do not claim any method is optimal merely because the methods we tried performed poorly.

## 1 — Build a challenging, diverse, validated benchmark

The current 12-source frozen Qwen study is too narrow. Create **216 fully authored independent TEST task contracts**, balanced across **6 workflow families × 3 real complexity levels × 2 independently implemented applications × 6 structurally different tasks per cell**. Create **72 separate DEV tasks** for development and qualification, with no structural duplicates or paraphrased holdout equivalents.

Keep the existing corrected FlowBoard UI and implement a genuinely separate second application/business backend, provisionally OpsConsole. Reuse common audit libraries if justified; do not present a UI reskin as cross-application generalization. Core workflow families: approval-governed publication, delegated-access migration, incident escalation, resource orchestration, data retention/export, and cross-team approvals. Incorporate concurrent collaborators, partial execution, uncertain acknowledgments, dependent approval gates, conditional permissions, real background worker progression, pending external operations and authorized restoration. Level 1 tasks should be meaningful multi-step jobs; Level 3 tasks must genuinely require sustained conditional planning and multiple consequential processes, not just extra clicks or longer prompts.

Each task needs an explicit natural-language user goal, accessible business policy/observations, obligation DAG, separate hidden independent task/effect oracles, permitted action set, external scheduling law, testable forbidden historical effects, and independently executable valid reference completion where feasible. Validate oracles with mutation and counterexamples. Distinguish organically agent-proposed mistakes from controlled pre-existing pending-effect faults. No task may secretly require an unavailable observation; classify inherently impossible schedule conditions separately from solvable task competence.

## 2 — Implement the recoverability graph, not just show a diagram

Build two provenance-preserving structures:

1. An **observed action-to-effect graph** linking model observations and native tool actions, gateway requests, DB changes, background jobs, worker admissions, external receipts, acknowledgments and task obligations.
2. A **counterfactual/feasibility graph** relating certified equivalent decision cuts, actually executed sibling continuations, and bounded formal transitions.

Every edge must be labeled `OBSERVED`, `EXECUTED_COUNTERFACTUAL`, `FORMAL_TRANSITION`, or `HYPOTHETICAL_UNVALIDATED`, with raw record IDs/hashes. Never count the last category as evidence.

Differentiate **actual safe completion**, **witnessed feasible alternative**, **bounded existential recoverability**, **bounded observation-based robust recoverability**, **current-state repair**, and **full historical-contract satisfaction**. A search timeout or unavailable API is not proof of universal irrecoverability. Extend the existing 256-state solver only with explicit action/horizon/scheduler assumptions and verifiable search certificates.

First reconstruct and validate all historical Source 05, 07, 11 and supervisor timing traces against real receiver records; then generate graphs for every newly executed trajectory. Provide machine-readable graphs, reproducible renderers, proof/witness audits, and examples of last feasible prevention points.

## 3 — Run the COMPLETE, preregistered, repeated model study

After full real PostgreSQL/Chromium/HTTP/local qualification, freeze the task contracts, model revisions, source states, randomization seeds, arm policies, time distributions, admissible operations, primary endpoint, statistical plan and retry rules **before opening TEST results**.

Per each of 216 TEST tasks, run **3 deadline-slack regimes × 3 independent seeded worlds** (1,944 paired stress worlds). Execute four fresh-continuation policies on **every** stress world:

- **P0:** actor only with ordinary application permissions.
- **P1:** strongest fast deterministic/public-authorization-aware protection, including staging where eligible.
- **P2:** rapid public verification followed by deterministic enforcement, **no extra model call**.
- **P3:** same public verification capability followed by a fresh Qwen decision before enforcement.

Run three separate nonstress, corrected-UI clean competence episodes per task. The specified main-model core evaluation is **7,776 stress branches + 648 clean episodes = 8,424 full executions**. Add the fully preregistered balanced **648-episode restoration-feedback study** (P1 plus public obligation status), and **648-episode stage-first supervisor study** (valid independent reviewer/fallback tracking). Total planned primary-model work is **9,720 executions**, before separate external/multi-model studies. These are dependent episodes nested in **216 distinct tasks**; never use the branch count as an independent-sample denominator. If sample-size analysis based on DEV indicates a different fixed complete study is scientifically better, revise and publicly freeze it *before* any new TEST outcomes, then execute the entire registered population.

Do not call two-task DEV outcomes a study result. Do not stop because the methods tie, fail, or are statistically insignificant. Do not tune task content, model prompts, intervention timing or model settings on frozen outcomes. Preserve all invalid/censored/failed branches with independent reasons. Technical retries require the exact preregistered policy and keep original attempt records.

## 4 — Isolate mechanisms with executed counterfactual ablations

Perform genuine controlled PostgreSQL/Chromium/HTTP replay experiments; simple arithmetic subtraction of recorded model latency is insufficient.

- **Verification versus deliberation:** P1/P2/P3 matched conditions, including situations where verification truly changes what is authorized and negative controls where it adds no information.
- **Decision versus enforcement:** vary the delay between an already-available correct protective recommendation and the gateway's effective action, with real worker progression; distinguish pre-dispatch holding from already-in-flight effects.
- **Timing frontier:** execute randomized admission-deadline sweeps around actual enforcement-time distributions for notifications, delegated reads and resource commitments; differentiate configured eligibility, external admission and physical effect.
- **Safety versus restoration:** with and without public post-protection obligation feedback; measure the agent's ability to finish without repeating forbidden actions.
- **Supervision:** compare fast deterministic policy with sequential and stage-first independent LLM review where useful; record invalid schemas and deterministic fallbacks distinctly.
- **Graph oracle gap:** compare real policy performance to witnessed siblings and exact bounded feasibility. An observed safe sibling is not a deployable hindsight oracle.

Ablation outcomes must have independent task/effect oracles, real model continuations when observations change, and a proper invariant-preserving matched baseline.

## 5 — Add actual external and model generalization

Use Qwen3.5-9B at its pinned available revision as the primary model. Verify and select one materially stronger/differently trained available model and replicate the **complete core** study with fair identical tools and time accounting. Do not invent endpoints or model availability; if a full second-model replication genuinely cannot be executed, preserve the precise blocker and narrow claims.

Perform an official **UndoBench TEST** evaluation using its unchanged task/history oracle and genuine model episodes; earlier five DEV wrapper comparisons do not count. If available, compare against a genuine Cordon-style transaction/staging baseline, clearly distinguishing original implementation from a faithful local proxy. Evaluate the second application separately. Independently reassess overlap with Async-RBench, ReInBench, AgentRewind, SURE-Act, AppWorld, tau2-bench, UndoBench and Cordon using their actual papers and code.

## 6 — Credible statistical evaluation and failure attribution

Primary dependent variable: **joint safe task completion = legitimate task completed AND no forbidden irreversible external effect AND preservation obligations satisfied**. The prespecified main policy effect is paired **P3 minus P2**. Secondary contrasts: P2-P1, P1-P0, restoration feedback, stage-first supervision, clean vs stressful competence and heterogeneous effects by workflow complexity/authorization/observability/deadline slack.

Use **source-task-clustered** intervals (not per-branch independent binomial intervals), preregistered paired testing, hierarchical sensitivity models, multiple-comparison control, actual latency and service-receipt distributions, and detailed negative results. Separate `AGENT_PLAN`, `OBSERVABILITY`, `MODEL_DECISION`, `VERIFICATION_DELAY`, `GATEWAY_ENFORCEMENT`, `EXOGENOUS_COMMITMENT`, `HISTORICAL_IRREVERSIBILITY`, `RESTORATION`, `INVALID`, and `UNRESOLVED` with raw evidence for first decisive failures and contributing factors.

Build the seven primary paper figures described in the visualization plan from raw data. Retain legacy results as background: v11 12-source live comparison, 256-state bounded solver, 78 determinate histories, Qwen UI feedback, and separate supervisor DEV. Do not pool DEV, synthetic, model generations and independent TEST tasks into one efficacy estimate.

## 7 — Resource and authorization update

The user explicitly removes the previous **$20 research-credit cap** for this new program. You are authorized to use available research credits to perform the full scientifically justified program; do not impose the archived $20, $5 operational, or previous remaining-allowance thresholds as a ceiling for the new research. Preserve and clearly separate the historical spend ledger. Meter every paid run, run finite preregistered jobs with watchdogs and idempotent resume, choose efficient inference deployment, and scale idle resources down. **Unlimited credit use does not authorize open-ended runaway loops, destructive external effects, unexpected public publication, or cash charges beyond available credits without separate explicit authorization.** If infrastructure or provider capability genuinely prevents completion, stop that part and give an exact truthful resumable handoff, not fabricated final results.

## 8 — Finish with a real research paper and reproducible artifact

Produce a complete revised manuscript, comprehensive appendix, locked study protocol, entire task set/benchmark card, raw and rescored evidence, action/effect graphs, statistical analysis scripts, per-failure trace atlas, novelty matrix, figure source, no-inference reproduction commands, and an independent acceptance audit.

**The work is not complete until every registered experiment has a reconciled trial status, every quantitative paper claim points to actual evidence, and all required figures and tables regenerate from archived runs.** If results show no meaningful incremental novelty, document that fact and select honest problem-characterization claims rather than forcing a controller win. Do not claim acceptance at a particular conference.

## Operating mode

Start working immediately. Don't respond with only a plan, another small smoke test, or a request for the user to pick between obvious alternatives. Make scientifically defensible design decisions, document them before seeing TEST results, implement all required code and research fixtures, qualify the complete suite, freeze the protocol, execute the full evaluations, evaluate, and write the final paper. Make local commits/checkpoints and maintain an exact progress manifest. **Do not push to a public repository or publish data externally without authorization.** At any interruption, leave verified completed work and precise resumable commands. In the final handoff state exactly which registered experiments truly ran, which remain incomplete, spend actually incurred, outcomes, uncertainty, and real file paths.
