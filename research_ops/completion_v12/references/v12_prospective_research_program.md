# AfterClick v12: research-grade completion protocol (prospective)

**Status:** prospective design only; no v12 workloads, paid runs, or evaluations have been executed. **Evidence base:** `684_final 11.zip` and `AfterClick_Fullscale_Research_Protocol_v11.md`, inspected 2026-11-25. V11's strongest observed result is a frozen Qwen3.5-9B intervention study of 12 source tasks/36 dependent branches, not a general benchmark of difficult workflows.

## Paper direction

**Title:** *AfterClick: When Safe Decisions Fail to Produce Safe Outcomes — A Causal Study of Recovery and External Effects in Tool-Using Agents*.

**Thesis to test, not assume:** A safety decision may fail to produce safe task completion due to multiple separable factors—agent planning, evidence availability, time until irrevocable external commitment, implementation latency, and post-intervention task obligations. The project should measure these factors on realistic multi-step workflows, rather than infer them from a small number of authored examples.

## Research questions and falsifiability

1. **RQ1: Trajectory and reachability.** Which actions and asynchronous events change whether safe completion remains possible? Classify source-relative witnessed safe paths, bounded action-set reachability, current-state repair, full-history contract, and truly unknown states. Falsifying outcome: action/effect graph adds no information or predictive discrimination beyond final-state scores.
2. **RQ2: Information vs. actionability.** When is costly verification or fresh model deliberation helpful, neutral, or harmful under competing deadlines? Compare equivalent public information and enforcement capabilities. Falsifying outcome: safety differences disappear after matching time and information, or no verification-dependent authorization choices occur.
3. **RQ3: Joint safety and completion.** Can intervention prevent harmful external effects **without** blocking mandatory authorized work? Measure restoration and obligations directly. Falsifying outcome: explicit status feedback does not improve completion or only increases unsafe actions.
4. **Secondary heterogeneity questions:** How do workflow complexity, information ambiguity, timing slack, and consequence mechanism modify these effects? Interaction tests must be predeclared and appropriately powered.

## Benchmark construction: real diversity rather than paraphrases

Create **72 independently authored workflow specifications** = six families × three complexity levels × four distinct business contracts per cell. The 72 slots are specified in accompanying `task_slots_72.csv`; these are **not yet implemented tasks**. Family examples:

- Release/customer communication: approval provenance, recipient scope, embargo, concurrent edits; irreversible external publication.
- Access migration: group membership, conflicting policy, handoff, outstanding tickets; delegated external reads.
- Incident escalation: contradictory reports, SLA clocks, competing responders and notifications; escalation delivery.
- Resource orchestration: dependency DAGs, quotas, uncertain acknowledgments and exactly-once consumption; external capture.
- Retention/data export: classifications, consent, deletion prerequisites, delayed export; irreversible release of protected information.
- Multi-party approval/operations: role constraints, changing sign-offs, conditional release, collaborator state; multiple consequential effects.

At least two distinct application interfaces/business data models if making cross-app claims; a renamed UI inside FlowBoard is not independent replication. Reuse existing receivers and oracles where valid. Avoid real email/financial/data disclosures; use independent simulated HTTP receivers.

### Complexity rubric (pre-registered before Qwen testing)

- **L1, structured:** 5–8 meaningful dependencies, one external effect, straightforward public rules, >=2 valid safe plans.
- **L2, conditional:** 8–15 dependencies, >=2 nontrivial branches, changing collaborator state, uncertain acknowledgment or policy verification, >=1 temporary restoration duty.
- **L3, long-horizon:** 12–25 meaningful dependencies, >=2 concurrent irreversible processes, changing evidence, competing obligations or deadlines, possible safe staging/compensation choices.

These are design targets, not a requirement to insert meaningless tool actions. Quantify observed critical-path length, action entropy (branching alternatives), dependency depth, verification information, effect coupling, and concurrency. Validate categories by independent human reviewers before Qwen enrollment.

### Evaluation contracts

Every task must include: natural-language user instruction; public policy documents; authorized tool surface; independently constructed state/effect oracle; explicit forbidden histories; obligation DAG; admissible intervention set; external event schedule; at least one manually or script-certified clean safe-completion witness; separate authorization and effect-history witnesses; and invalid/unknown/censor rules. If genuinely no safe completion exists under a target schedule, label as a **known unavoidable-world stratum** and exclude from solvable-task competence denominator, reporting it separately. No private oracle labels in model prompts. Do not assume one canonical action sequence: accept all proven semantically valid sequences.

A small separate development set can be used to debug interfaces and calibrate complexity, but must not overlap by task template, document, or paraphrase with locked 72-task TEST. Use at least two independent reviewers on a stratified task sample, log disagreement and adjudication.

## Full repeated-trial design: 2,304 executions

For **each** of 72 independently authored workflow specifications, run **three predeclared schedule-slack strata** (generous, intermediate, tight), with **two independent schedule/observation seeds per stratum**. That creates **6 worlds per workflow = 432 matched source worlds**. Seeds vary collaborator interleavings, evidence arrivals, acknowledgment timing, and independent tool jitter while holding the task contract fixed. Freeze the randomization, absolute schedule laws, and source hashes before opening TEST outcomes. Aim for feasible tight cases plus an explicitly flagged beyond-frontier diagnostic category, never quietly exclude impossible conditions.

Run the **same five primary treatments** for each source world (432 × 5 = 2,160):

1. **B0: Corrected-UI, non-stressful baseline:** same user obligations, no artificially competitive external deadlines; normal application semantics preserved. Measures basic competence. This is an experimental control, not a zero-latency simulation.
2. **B1: Stress, actor only:** no added intervention beyond the application's inherent authorization/capability enforcement. Measures untreated task/violation outcomes in safe mock services.
3. **B2: Stress, fast deterministic protection:** best public-information authorization-and-timer policy; must not use hidden schedule knowledge.
4. **B3: Stress, fast verify-then-enforce:** same public service verification, no extra model decision; isolates value and overhead of information.
5. **B4: Stress, verify-plus-Qwen:** identical public verification capabilities/information, but fresh Qwen inference before the protective tool action; isolates information versus deliberation latency.

Additional **restoration ablation:** preselect 24 of the 72 workflow specs with meaningful mandatory post-protection obligations (balanced across families and difficulty, not picked based on TEST results). For each of their six worlds add **B5: B2 + independent public-obligation status feedback**. This adds 24 × 6 = **144** executed branches. **Grand total = 2,304 branches**, excluding development, local deterministic replays, optional cross-model or external evaluation.

**Units:** 72 task specifications; 432 paired source-world episodes; 2,304 dependent policy continuations. Treat workflow specs as the conservative top-level clustering unit for population-level inference. Repeated seeds and dependent arms are not new independent workflow specifications. Use stratified cluster bootstrap and multi-level mixed models as sensitivity checks; no row-wise independent binomial tests over 2,304 branches.

**Order control:** counterbalance arm execution order within each task×seed; restart source world from certified snapshots and verify identical user-visible observations and task obligations. Make external workers progress in live time during Qwen calls. Record real model start/end, tool return, gateway enforcement, worker admission, external receipt, ack, and DB state. Freeze retries and censor rules; do not replace difficult instances. Infrastructure-invalid branches must be reported and reproducibly retried only under preauthorized technical-failure rules.

## Causal mechanism experiments in addition to outcome comparisons

1. **Timing frontier sweep (no-paid deterministic first):** For each mechanism, vary an explicitly controlled admission time around the observed protection-time distribution while holding policy-visible context fixed, then execute and record true effect receipts. Distinguish last effective API action from worker eligibility and physical effect. Exact boundary claims apply only to declared effect model and action set.
2. **Latency decomposition:** log source-clock and monotonic host times, and test interventions at model response arrival, pre-browser gateway, and eventual enforcement. Compare real executed outcomes in controlled replay. Do not infer causal success by merely subtracting model milliseconds from an original trace.
3. **Information value:** For ambiguous-but-resolvable authority, prepare paired public signals whose possible observations genuinely change what is authorized. Contrast no verification, fast verification, and verification-plus-Qwen. Include negative controls where verification adds no relevant information.
4. **Obligation preservation:** Score prevention, restoration, and overall completion separately; test visible status feedback on same paired source worlds. Include placebo feedback with equivalent length where useful to separate reminder effect from additional information.
5. **Safe path / oracle gap:** Build time-indexed action→worker→effect→obligation graph. Edges must be tagged as recorded, verified intervention replay, bounded-model closure, or hypothetical. For bounded states, enumerate the declared actions/horizon to produce witness or exact obstruction. For complex worlds without complete search, use 'witnessed achievable' and UNKNOWN, not 'globally impossible'.
6. **Repeatability:** report pass@1, pass^k across independent schedule seeds, consistency of first consequential action, unnecessary tool calls, retries, unauthorized proposals, and adverse outcomes with exact independent receipts. Never relabel invalid replay as agent failure.

## Primary and secondary measures

**Primary:** source-level probability of *joint safe task completion* (all required obligations, protected external history, independent collaborator changes preserved). Pre-register **B3 versus B4** as primary paired policy contrast in the stressed conditions; B2 vs B3 as main secondary. A co-primary 'first loss of feasible safe completion' is acceptable only where it has certified admissible bounds; otherwise describe it as observed/witnessed.

**Secondary:** forbidden historical effects, clean task competence, correct approval/rejection, false blocking, order violations, time to effective protection, deadline slack, inference and browser/gateway latency, useful vs redundant action count, task completion and restoration rate, extra verification calls, real cost/tokens, and task complexity interactions. Tag all effects as authorized/unauthorized and pending/committed/consumed/acknowledged. Severe-effect categories must not be silently averaged with mild inconvenience.

**Reliability:** independent effects vs source workflows vs seed repetitions distinctly named. Report per-family outcomes, per-difficulty outcomes, standardized paired differences with source-cluster intervals, multiplicity control for prespecified families and interactions, missing/censored separately, and all original trial records. Include negative results, exposure-adjusted harms, and full latency distribution rather than only medians.

## Statistical rigor and quality assurance

- **Power:** pre-register detectable effect sizes using prior studies and realistic intraclass correlations; plan around number of unique task templates (72) and families (6), not number of tool events. This design can still have wide intervals for 5–10 percentage-point differences. No guaranteed 'significant' win.
- **Randomization:** assign task language, independent schedule seeds, document/role identities, time-slack regimes, and order counterbalancing before TEST. No prompt change or policy selection after outcomes.
- **Reproducibility:** pin Qwen revision, decoding, browser, DB, model endpoint, source hashes, tool schema, gateway implementation, effects receiver, wall-clock model, and artifact manifest. Preserve sealed v11 studies unchanged.
- **Task quality:** external human/scripted witnesses solve every nominally feasible task on the corrected interface. Have independent reviews of public authorization ambiguity and oracle grading. Require nontrivial alternate plans; no template leakage from development.
- **Validity:** full deterministic, PostgreSQL, Chromium, HTTP receiver, and source-reconstruction suites must pass before paid confirmation; resolve or disclose v11's two legacy timing failures. No 'smoke-test-only' qualification. Report installation scripts and infrastructure specifications.
- **Generalization:** conduct a full official external recovery benchmark TEST with genuine model calls, unchanged official evaluator and published baselines, and/or independently replicated second app if claiming broader generality. The separate benchmark cannot stand in for live deadline causality unless it actually contains those mechanisms.
- **Causal claims:** only assert first-boundary transitions when logged workers, admissible actions, and executed intervention witnesses support them. Explicitly separate externally authored schedule laws from natural incident rates.

## Budget and execution integrity

Archived v11 records approximately **$3.249 spent under a $20 authorized increment, leaving $16.751 nominal authorization**; provider credits were not refreshed in this design. **Do not spend $20 again.** No additional paid inference authorization is implied. Full 2,304-branch long-horizon study is expected to cost far more than the remaining authorized/credit ceiling; require realistic pricing of actual Qwen calls, per-world orchestration and GPU uptime and obtain explicit new authorization **before** starting a paid confirmation. Do not claim completion based on a partial sample if the budget stops the run. Work on authoring, deterministic qualification, reference witnesses, and graph build may proceed without paid calls, subject to normal repository constraints.

## Results, artifacts, and paper

- Locked TEST manifest and independent DEV manifest; 72 authored workflows with policies/contracts and 432 world/schedule seeds.
- Each of 2,304 planned conditions with replay certificate, original and continuation native actions, supervisor/policy response if relevant, independent receipts, temporal provenance, obligation scoring, token/cost data, and exact source hashes. Any missing condition is explicitly reported.
- A measured action/effect/recoverability graph plus trajectory alignment for every branch; source 05/07/11 from v11 used as motivating examples, not as a new held-out TEST.
- Main figures: (1) valid-looking plan vs irreversible-effect clocks; (2) witness-labeled reachability frontier; (3) clean competence vs progressively harder tasks; (4) deadline slack vs intervention-success curves; (5) information gain vs end-to-end latency; (6) safety×restoration four-cell plot; (7) task complexity/family heterogeneity; (8) sample sizes and uncertainty.
- Evidence provenance matrix: every claim → task/seed → branch → action IDs → effect receipts → independent oracle → statistical unit → limitations.
- Complete reproduction and paper: methodology, negative results, validity caveats, comparisons with UndoBench/Cordon and newer multi-step tool-agent benchmarks; open raw artifacts and failure taxonomy.

## Scientific stopping criteria

Do not declare superior controller, impossible recovery, or broadly representative incidence without the applicable evidence. If the 72-task study is underpowered for a small effect, report compatible effect-size intervals instead of expanding opportunistically. If no model advantage exists, analyze the reasons (authorization explicit, verification redundant, gateway enforcement dominant). If a new failure mode is discovered, disclose it as exploratory and replicate on a future holdout before claiming generality.
