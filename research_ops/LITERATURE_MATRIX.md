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
