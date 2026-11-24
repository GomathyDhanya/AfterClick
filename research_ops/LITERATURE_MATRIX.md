# Primary-source identity and overlap audit

Checked 2026-11-22 by opening the primary abstract/official documentation pages linked below.
Scope: source identity and abstract-level overlap only. Full-method, baseline and novelty clearance
remain pending P10. The proposed deltas are hypotheses inferred for comparison, not proven absences
from prior work. DOI for each arXiv record is https://doi.org/10.48550/arXiv.<identifier>.

| Primary source | Verified overlap | Proposed AfterClick delta requiring evidence |
|---|---|---|
| [ReplayRCA: Measuring Post-hoc Diagnosis and Live Oversight of Agent Failures by Counterfactual Replay](https://arxiv.org/abs/2610.41025) | Single-action replacement and continued execution, paired placebo, live oversight before irreversible actions. | Temporal recovery-frontier discovery and matched-budget supervision must add value beyond replacement/oversight. |
| [Causal Agent Replay: Counterfactual Attribution for LLM-Agent Failures](https://arxiv.org/abs/2606.08275) | Intervention-based forward replay under a stochastic policy, attribution and confidence intervals. | Discover minimal lawful schedule contrasts and evaluate prospective time-dependent risk; replay itself is prior art. |
| [UndoBench: Separating Task Competence from Recovery Capability in Tool-Using AI Agents](https://arxiv.org/abs/2610.05622) | Paired fault trials, effect-history/state oracles and phase-dependent recovery under lost acknowledgement. | Notification demo and idempotent retry are insufficient novelty; need distinct frontier-search or calibrated learning evidence. |
| [AgentRewind: Recoverable Execution for Long-Horizon LLM Agents](https://arxiv.org/abs/2608.14380) | Runtime checkpoints coordinate controlled environment and agent context for recovery. | Historical external observations and compensation-preserving invariants need explicit comparison, not generic rollback claims. |
| [Idempotency Is Not Recovery: A Fault-Injection Study of Language-Model Agent Tool Actions](https://arxiv.org/abs/2611.23353) | Fault injection, separate target oracle, action ledger, idempotency and reconciliation; captured-response evidence distinguished. | Additional temporal-boundary search/learning claim remains untested; do not present cached calls as independent live policy samples. |
| [Agents' Last Doubt: Knowing When to Act and When to Step Back in Tool-Using Agents](https://arxiv.org/abs/2610.24194) | Counterfactual legal-action outcomes train a controller balancing completion, cost and irreversible errors. | Boundary-focused temporal data must beat equally budgeted generic alternatives and simple visible-feature controls. |
| [Localizing Emergent Failures in Agentic AI: Recovering Minimal Repair Families via Counterfactual Replay](https://arxiv.org/abs/2608.29228) | Graph-constrained joint replay finds bounded inclusion-minimal repair sets. | Schedule-boundary witnesses differ as a target, but minimality/search-efficiency claims need precise head-to-head positioning. |
| [Planarian: Managing Agent State with Statepoints](https://arxiv.org/abs/2609.35366) | Consistent local/remote statepoints, fork/rollback, recorded compensations for remote changes. | Focus on irreversible receipt history and conditional collaborator preservation; no claim of inventing compensation or branching. |
| [Mnemosyne: Agentic Transaction Processing for Validating and Repairing AI-generated Workflows](https://arxiv.org/abs/2607.00269) | Deterministic admission, append-only evidence, dependency-safe compensation and bounded reactive repair. | Need comparative evidence for learned temporal intervention beyond established admission and repair primitives. |
| [Illuminating search spaces by mapping elites](https://arxiv.org/abs/1504.04909) | MAP-Elites maps high-performing candidates across chosen behavioral dimensions. | A temporal-frontier objective/minimizer may be an application; novelty requires equal-budget distinct-mechanism gains. |
| [Microsoft Compensating Transaction pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction) | Business-specific compensation must account for concurrent changes; simple restoration may be inadequate. | CAS-preserved compensation is a foundation, not sufficient standalone algorithmic novelty. |

No claims of acceptance, novelty, empirical superiority or exhaustive literature coverage result
from this audit. Numeric claims from abstracts were not imported into AfterClick's own results.
No model/provider/Modal pricing or endpoint compatibility was verified in P0.

## Operational sources checked 2026-11-23 UTC

[Qwen3.5-4B pinned repository](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a)
verifies license/config/template; [Modal4B catalog](https://modal.com/library/qwen/qwen3-5-4b),
[Dedicated Endpoints](https://modal.com/docs/guide/dedicated-endpoints),
[cold starts](https://modal.com/docs/guide/cold-start), [pricing](https://modal.com/pricing)
support deployment/API and planning assumptions. These are operational documentation, not evidence
for scientific novelty or4Bstartup superiority. Raw snapshots in p1d-20261123-4b-readiness/raw.
No new literature-comparison claim was made in this infrastructure phase.

## 2026-11-23T06:14:26.547561+00:00 — schema diagnosis evidence boundary
Operational primary references previously checked this session: [SGLang structured outputs](https://github.com/sgl-project/sglang/blob/main/docs/docs/advanced_features/structured_outputs.mdx), [sampling parameters](https://github.com/sgl-project/sglang/blob/main/docs/docs/basic_usage/sampling_params.mdx), [XGrammar grammar API](https://xgrammar.mlc.ai/docs/latest/api/python/grammar.html). They describe schema interfaces, not proof that the installed decoder permits every branch of our schema. Live11validoutputs support requestacceptance; repeatedfillsleavebranchreachability/planningunresolved. No new novelty clearance or scientific literature claim.

## 2026-11-23 — current primary-source comparison

Entries below distinguish verified overlap from a proposed delta. No head-to-head replication of
these systems was run. Numbers from their papers are not imported into our results. This is a
focused comparison, not an exhaustive novelty search.

| Primary source | Verified overlap | AfterClick delta and limitation | Reading depth |
| --- | --- | --- | --- |
| [Causal Agent Replay, v1](https://arxiv.org/html/2606.08275v1) | Step interventions, stochastic continuation and replay fidelity. | Our labels concern admissible temporal recovery; no improved attribution estimator. | Full HTML, formulation/limitations |
| [UndoBench, v1](https://arxiv.org/html/2610.05622v1) | Paired faults, effect-history/state oracles and phase-specific recovery. | Adjacent timing witnesses and acquisition comparisons are the proposed addition; our application breadth is much smaller. | Full HTML, design/boundaries/appendix headings |
| [SURE-Act, v1](https://arxiv.org/abs/2610.24194) | Counterfactual outcomes train action/escalation control. | We test recovery-time targets with small local predictors; integration alone is not new. | Primary abstract |
| [Mnemosyne, v3](https://arxiv.org/abs/2607.00269v3) | Executable admission contracts and evidence-preserving compensation. | Our finite closure is a bounded test oracle, not a new transaction runtime. | Primary abstract |
| [Planarian, v1](https://arxiv.org/abs/2609.35366v1) | Local/remote statepoints, compensation and branching. | AfterClick reconstructs experiments but never uses snapshots as live recovery. | Primary abstract |
| [ACRFence, v1](https://arxiv.org/html/2603.20625v1) | External effects survive local restore; replay identity matters. | Our lost-ack guard uses standard idempotency; no new exactly-once protocol. | Full HTML, threat/mitigation sections |
| [Can You Undo It?, v1](https://arxiv.org/html/2611.22075v1) | Declared recovery classes, conservative gates and conditional recovery tests. | Timing/observation/data-budget experiments are candidates for a narrower delta, not a first recovery taxonomy. | Full HTML, abstract/design |
| [Irreversibility Budget, v1](https://arxiv.org/html/2609.00275v1) | Runtime accounting of residual irreversible exposure. | Our suppression budget is per-stream and simpler; no fleet-level contribution. | Full HTML, abstract/formulation |
| [REVERSAL-BENCH, v1](https://arxiv.org/abs/2609.17745v1) | Recoverability oracles and interventions near irreversible states. | Our application-side receipts and temporal targets differ; reversibility benchmarking itself is established. | Primary abstract |
| [Leave no Trace](https://arxiv.org/abs/1711.06782) | Reset-value prediction and uncertainty-aware aborts. | We study declared distributed capabilities rather than learned physical reset policies. | Primary abstract |
| [Delta Debugging](https://www.st.cs.uni-saarland.de/papers/tse2002/) | Minimal failing inputs and passing/failing differences. | Integer bisection/minimization is inherited, not novel. | Author publication page/abstract |
| [CHESS](https://www.microsoft.com/en-us/research/publication/finding-and-reproducing-heisenbugs-in-concurrent-programs/) | Systematic deterministic concurrency testing. | Our fixed timing axis is narrower than general schedule exploration. | Author/publisher page |
| [Sagas](https://www.cs.princeton.edu/techreports/1987/070.pdf) | Application-specific compensating transactions. | Compensation is a foundation; our claim is not a new transaction concept. | Indexed primary abstract; direct PDF returned403 |

Observed literature overlap substantially weakens a broad novelty claim. The best current position
is a small, auditable temporal benchmark with explicit counterexamples and mixed/negative comparisons.
Whether its particular combination is a publishable research contribution remains unestablished.


Final source recheck 2026-11-23T17:51:12.114175+00:00: UndoBench full HTML (https://arxiv.org/html/2610.05622v1), CAR full HTML (https://arxiv.org/html/2606.08275v1), and SURE-Act primary abstract (https://arxiv.org/abs/2610.24194) remain available and support the recorded overlap. No claim of superiority or absence of their techniques follows from this review.


## 2026-11-23T20:06:10.697972+00:00 — native interaction and observability extension

Date checked2026-11-23. Fresh primary comparison supplements the earlier recovery/replay matrix.

| Primary source | Reading depth / known overlap | Candidate delta and limit |
| --- | --- | --- |
| [Howard1966 Information Value Theory](https://ieeexplore.ieee.org/abstract/document/4082064/authors) | primary indexedabstract; directfetch blocked | jointly weighing information and consequences is established; do not claim VOI novelty |
| [Kaelbling/Littman/Cassandra1998](https://www.cassandra.org/arc/papers/aij98.pdf), DOI10.1016/S0004-3702(98)00023-X | author-hosted indexedprimaryabstract; fullPDF toolsizeblocked | POMDP action/information planning established; our fixed3action heuristic is not an optimal solver |
| [Probabilistic shields](https://arxiv.org/abs/1807.06096) | primaryabstract checked | probabilistic formal safety/control established; explicit asynchronous cancellation/evidence clocks are benchmark focus, no precedenceclaim |
| [Partial-observability shielding](https://arxiv.org/abs/2204.00755) | primaryabstract checked | partial-observation safe control and learning gains established; new tiny staticcue workload is not demonstrated superior |
| [UndoBench](https://arxiv.org/html/2610.05622v1) | earlier fullHTML plussource recheck | boundary-specific recovery and dualoracles already overlap strongly; our timing/inspection dataset and negative acquisition controls are candidate empiricaldelta |
| [SURE-Act](https://arxiv.org/abs/2610.24194) | primaryabstract | counterfactual action control already established; no head-to-head superioritytested |

Native tools and structured JSON are existing endpoint features, not research novelty. OldCAR,
ACRFence/Mnemosyne/Planarian/sagas/concurrency comparisons remain relevant. An absence claim cannot
follow from abstract-only review. Publication uniqueness remains unresolved.

### 2026-11-23 — model-in-the-loop sprint, primary-source refresh

Checked primary arXiv HTML and abstracts today. These are author-reported results, not independently reproduced implementations. No published system is claimed reproduced by this sprint.

| Work / primary source | Closest overlap | Remaining possible delta and decisive test |
| --- | --- | --- |
| [Cordon, 2606.17573v1](https://arxiv.org/html/2606.17573v1), Chen et al., June 2026 | Task-level transactions, shadow mutations, staged outward effects, lineage and validation before release. | Merely staging or speculating is not new. A delta would require a measured time-sensitive continuation advantage over a credible staging/admission baseline. |
| [SURE-Act / Agents' Last Doubt, 2610.24194v1](https://arxiv.org/html/2610.24194v1), Liu et al., October 2026 | Executes legal alternatives from checkpoints, freezes continuation policy, learns action selection. Its paper explicitly discusses unstable rollout labels and repeated-intervention limitations. | Strongest conceptual overlap. Executable continuation comparison alone is not novel. Need useful temporal-effect information, real enforceable alternatives and matched-budget gains; none established yet. |
| [UndoBench, 2610.05622v1](https://arxiv.org/html/2610.05622v1), Sah et al., October 2026 | Separates nominal competence from recovery, paired fault/control trials, state and external-effect histories, phase-dependent faults and idempotency. | Basic competence gate and dual oracles are prior methodology. A different clock or another lost-ACK example is insufficient novelty. |
| [CASEL, 2610.36570v1](https://arxiv.org/html/2610.36570v1), Zhang et al., October 2026 | Chooses execute/verify/sandbox/approval using consequence and reversibility; intervention effectiveness in its evaluation is assumed in simulation. | Actual measured live-agent continuations could test a missing empirical premise, but cannot establish a superior routing algorithm without comparisons. |
| [AgentBoundary, 2609.33658v1](https://arxiv.org/html/2609.33658v1), Yang et al., September 2026 | Independently varies apparent risk and permission, diagnoses unsafe compliance and over-refusal alongside competence. | Our authorized/restricted task pairs are a smaller development audit, not a new broad benchmark. Native independent SQL receipts strengthen verification only within this controlled application. |

Provisional novelty verdict: **not established**. COPE is a research candidate with strong prior overlap, not a new name sufficient for a contribution. Gate further paid work on actual pilot behavior; use only simplified baselines clearly labeled as such.

## 2026-11-24 — temporal live-continuation study refresh

Primary sources checked again; paper claims are author reports, not independently reproduced systems. Full method sections inspected for Cordon (§4.5–4.6), SURE-Act (§3.2), UndoBench (boundary/zero-privilege limitations), AgentBoundary (construction/evaluation), CASEL (§VIII); earlier abstracts are not treated as priority proofs.

| Primary source | Exact overlap | Candidate delta / limiting evidence |
| --- | --- | --- |
| [Cordon](https://arxiv.org/html/2606.17573v1) | Staged outbox, validation before release, distinct local promotion/external effects, conservative ambiguous-dispatch recovery. | Our stage baseline is a small browser-service approximation. No novel transaction or staging claim; external jobs already active outside the controller make intervention timing experimentally salient. |
| [SURE-Act](https://arxiv.org/html/2610.24194v1) | Separate cloned states for candidate actions followed by the same frozen agent; action outcome ranking and stochastic-label limitations. | Exact continuation branching is prior art. New study measures real forecasting delay against continuing external jobs and isolates exact evaluator clones from public-belief online forecasts. Incremental efficacy still unproven. |
| [UndoBench](https://arxiv.org/html/2610.05622v1) | Competence conditioning, phase-dependent recovery, effect-history/state oracles and idempotency. Zero-privilege limitations explicitly qualify baseline interpretation. | Our ACK fault is application completion visibility, not an equal wire-level lost-ACK reproduction. A smaller benchmark cannot claim broad benchmark superiority. |
| [AgentBoundary](https://arxiv.org/html/2609.33658v1) | Permission-sensitive executable counterfactual tasks and joint unsafe-compliance/authorized-completion measurement. | Joint safety/competence is established; present instance/schedule confirmation is narrower than its broad task benchmark. |
| [CASEL](https://arxiv.org/html/2610.36570v1) | Reversibility/consequence-dependent routing among execution and interventions. Evaluation assumes intervention effectiveness. | Actual Gateway intervention outcomes and latency can test that empirical assumption; no superior risk-allocation claim without an observed advantage. |
| [Zilberstein & Russell, Optimal composition of real-time systems](https://people.eecs.berkeley.edu/~russell/papers/aij-anytime.pdf), DOI10.1016/0004-3702(94)00074-3 | Full introductory formulation and anytime performance-profile sections: decision quality competes with time-dependent utility and computation allocation. | Thinking costs time is established. Our small heuristic is not optimal metareasoning; only live-agent boundary measurements can be a bounded empirical delta. |
| [Russell & Wefald, Principles of Metareasoning](https://doi.org/10.1016/0004-3702(91)90015-C) | Computational actions are valued by their consequences for external decisions. Primary archival first-page scan inspected; do not claim full-paper audit from that one-page scan. | TCOPE inherits value-of-computation motivation. No claim that our proxy estimates calibrated expected computational utility. |

Related POMDP, shielding, Saga and schedule-testing entries above remain foundations. No absence/firstness claim follows from this finite review. Strong immediate staging is the decisive simple comparator; equal naming or integration is not conceptual novelty.

## 2026-11-24T06:14:12.740600+00:00 — Additive study checkpoint

### Final synthesis, 2026-11-24
No new conceptual priority is established by t-series results. Current primary-source links/overlap above remain the basis; no unperformed head-to-head reproduction is implied. Strong staging wins economically in exploratory development; locked confirmation fails client-state reconstruction. The candidate delta is a small auditable live timing/replay failure characterization, not a new transaction/branching/metareasoning concept or confirmed superior control algorithm. See FINAL_NOVELTY_VERDICT.md and paper/TCOPE_PAPER.md for the claim-evidence matrix and uncertainty.

## 2026-11-24 OECR final review

Primary sources, inspected technical sections, exact overlap and remaining distinctions are recorded in NOVELTY_MATRIX.md (Safe to Resume?, AgentRewind, SURE-Act, Cordon, UndoBench, Chandy–Lamport, Russell–Wefald). Independent u5/u7 evidence supports a limited empirical systems study, not new snapshot/replay/staging concepts or demonstrated cross-framework superiority. Manuscript §12 supplies the claim–evidence matrix.
