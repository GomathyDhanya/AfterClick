# AfterClick v12: experimental appendix

## A. Contract, history and recoverability definitions

Let s(t) include local application data, delegated capabilities, browser/client state, pending jobs, model-visible history and elapsed time. Let h(t) be the independently observed effect prefix. Joint success requires all legitimate obligations, required restoration and an allowed complete effect history. Current local repair is a separate property: it does not delete a previous external delivery.

Existential recoverability asks whether an admitted continuation and some admitted scheduler continuation can satisfy the contract. Robust recoverability asks whether an observation-based policy succeeds for every admitted scheduler continuation. A realized successful trajectory is one witness, not a robust policy. Failure to find a continuation is UNKNOWN unless a declared exhaustive transition model supplies a certificate of impossibility.

G1 contains actual observed transitions and explicit identity/order joins. G2 contains actually executed sibling-policy continuations from certified equivalent initial cuts. G3 contains separately bounded formal edges. The complex application graphs contain no G3 edges. Their intermediate reachability is UNKNOWN except where a persisted forbidden physical effect establishes an immutable history violation. A successful transport acknowledgment supplies a conservative time by which the receiver's effect is known to have committed; it is not the exact SQL COMMIT instant. A receipt audit timestamp alone is not promoted into an exact frontier.

The 256-state legacy solver and the independently declared 141-state six-tick game remain separate. In the temporal example a robust policy exists at tick zero; at tick one one declared schedule is infeasible and another is feasible. These are mathematical claims about those transition models, not empirical percentages of live recoverability.

## B. Task inventory and measured complexity

The complete 288-row catalog is `research_ops/completion_v12/final_package/TASK_CATALOG.csv`; every row links to its immutable contract. Each contract includes public instruction/policy, private evaluator obligations, reference metadata and structural metrics. Historical authoring markers are retained verbatim and overridden by the frozen operational registry and executed qualification evidence.

| Level | Business operations | TEST dependency depth | Conditional branching count | External duties | Required observation classes |
|---|---|---|---|---|---|
| L1 | 8 | 5-7 | 0 | 1 | 3 |
| L2 | 13 | 7-12 | 2 | 1 | 5 |
| L3 | 21 | 11-20 | 2 | 2 | 5 |

Depth and branching are the implemented structural measures, not estimates of human reasoning effort. L1 intentionally includes simpler workflows. Six public vocabularies and 24 layouts limit independent task diversity even though all contract identifiers, obligations, initial classifications and source hashes are explicit. No identical full layout crosses DEV and TEST; shared construction operators are disclosed.

| Family | Actual synthetic external mechanism | Examples of remaining duties |
|---|---|---|
| Access migration | Delegated read | Reconcile authority and restore named grants/assets |
| Cross-team approval | Service commitment | Role signoff, ordered handoff and restoration |
| Customer release | Customer notice | Scope release, receipt and service restoration |
| Incident response | Incident notification | Dependency ordering and collaborator preservation |
| Resource orchestration | Nonrefundable unit consumption | Quota conservation, scoped allocation and restoration |
| Retention/export | Data export | Classification-dependent scope and receipt reconciliation |

Both applications use distinct business representations. Their common audit/effect infrastructure is intentionally shared. The HTTP services are real separate services in the experiment, but all business consequences are synthetic fixtures.

## C. Source certificates and observation boundary

A source cut hashes the quiescent initial database/application/audit state, public projection, seeded scheduler configuration and client state. The browser stops polling, waits for no active refreshes or pending request, and records DOM, focus, choices and viewport. Fresh schemas reconstruct each branch; snapshots are never an action for live recovery. Within a batch, a source certificate is established and sibling equality is checked before that sibling's inference. Certificates do not prove identical GPU cache state, shared-server queueing or wall-clock scheduling. Resumed jobs retain their own before-inference certificates and require explicit cross-job equality checks before an analysis treats them as matched initial states.

Actor inputs contain only permitted public state and actual tool results. Native assistant tool-call IDs and corresponding tool messages persist across the episode. The first message supplies static record definitions; subsequent tool responses supply complete current dynamic state and batch results. Reviewers receive the public browser projection, not oracle judgments. Public P4 obligation feedback is generated from visible service and record state. Hidden expected choices, evaluator results and scheduler programs never feed either model.

## D. Oracle alternatives and independent verification

The operational v2 grader recognizes two acknowledgment paths: an explicit receipt-verification event, or an actual completion commit backed by the already persisted matching physical receipt. Neither path invents a new event or deletes an old one. Real counterexamples from FlowBoard and OpsConsole are retained in the test fixtures. Removing the receipt or actual reconciliation commit causes rejection.

Two full reference witnesses per contract produce 576 accepted paths. The separate checker implementation rejects 10,944 altered obligations/evidence sets. The final continuous-native 252-episode DEV cohort independently re-scores with zero disagreements. Its 47 corrected labels and original result files remain separately linked and hashed. Independent implementation does not imply independent human review or proof of completeness of the business specification.

## E. Runtime, limits and serving

The frozen actor limit is 24 calls, 200 browser actions and 240 seconds per episode, followed by 1.5 seconds of observation-only settlement. Parent jobs also have finite elapsed-time and global call ceilings. A parent deadline can therefore censor an episode before its individual limit; that is an infrastructure/time-budget limitation, not proof of agent inability or fundamental irrecoverability. Every such case remains in the registered denominator as UNKNOWN. A genuine non-completing 24-call trajectory is a valid observed failure, not an invalid run.

The primary endpoint serves Qwen/Qwen3.5-9B at revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. The larger endpoint serves Qwen/Qwen3.6-35B-A3B-FP8 at revision `c653bba46dfa06e9658dcc0b0dc87fe4685f14a2`. Exact endpoint identities and native serving metadata are in the freeze and paid raw preflights. The managed larger stack includes DFLASH with pinned draft revision. An attempted custom eager redeployment failed locally before deployment and was never used for experimental calls. It remains archived as an unsuccessful attempt.

The CPU worker uses Python 3.11, real PostgreSQL, Chromium and pinned package versions. It runs at most two containers, each with eight requested CPU cores, 16 GiB memory and at most 16 concurrent worlds. The serving endpoint has minimum zero and maximum one container. Temperature is zero, maximum output 512 tokens, automatic native-tool choice and thinking disabled. API generation retries are disabled. No inference call is silently reissued after a transport-uncertain outcome.

## F. Controlled actuator experiment

Twelve L3 DEV sources cover six families and both applications. Each has two seeded worlds, three configured pending-admission offsets and four actuator conditions. The recommendation is fixed and correct before the actuator delay begins. All 288 branches execute; one browser action times out and is retained invalid. The continuation is the full reference task, not an immediate safety-only stop.

Compared with ordinary browser enforcement, 300 ms added delay increases forbidden-history incidence by 27.78 percentage points (source bootstrap 95% interval 23.61-31.94); 1,500 ms increases it by 60.56 points (55.83-64.72). The latter full-assignment missing-outcome range is 59.72-61.11 points. Direct HTTP minus ordinary browser is -2.78 points (-9.72 to 4.17). These intervals condition on 12 constructed sources and six mechanisms. They are not broad population estimates.

Workers and controller changes do not share a single atomic authorization boundary. Separate state reads/writes can race, and an admitted ticket may persist after a later suspension. A receiver effect after an audit protection event therefore does not by itself prove LLM delay or a particular last preventable frontier. Contributing ordering is reported with raw evidence; exact admission-read causality is labeled unresolved.

## G. Frozen estimators and interval diagnostics

The primary P3-P2 contrast enrolls all 216 source tasks; the recorded complete-pair estimate has 111 source clusters, with missing assignments retained in bounds. Five secondary contrasts receive Holm adjustment. Source-level estimates, studentized tests, task-sign sensitivity, stratified bootstrap intervals and full-assignment bounds are preserved exactly as produced by the frozen analysis. An unpenalized mixed logistic model is reported unidentifiable under separated or absent arms; no finite coefficient is manufactured.

The preselected 36-task focused studies and larger-model supplement have one source per application/family/level cell. A within-cell bootstrap cannot resample singleton cells. The frozen numerical point interval is retained as a diagnostic and is not presented as meaningful uncertainty. A post-freeze diagnostic derives a t interval from the already frozen source standard error/test and reports a six-family bootstrap sensitivity. This corrects reporting without changing outcomes, enrollment, prompts, oracle, policies or the frozen estimator. It does not create independent task diversity.

Power analysis uses 72 DEV sources and source-correlated scenarios, not independent calls. Only one matched stress world per source exists in the final DEV cohort, so an intra-source correlation is not empirically identified there. Sensitivity values 0/.5/1 are assumed scenarios. Small-effect power is limited and no equivalence claim follows from a zero-success or nonsignificant contrast.

## H. Official external benchmark

The unchanged UndoBench checkout is pinned at `4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e`, SDK 1.0.0, benchmark 1.0.1, protocol V4. The canonical engine, prompts, public tools, tasks and dual evaluator are preserved. A bounded native agent uses the same generation transport, with at most ten calls per condition. Available wrappers are naive, checkpoint, saga, idempotency and vbr. EvoUndo is unavailable and receives no invented score. These wrappers are not renamed as AfterClick P0-P5.

TEST enrolls 12 official tasks, two context seeds, five wrappers and both CONTROL/FAULT conditions: 240 assignments. Context seeds 42/43 do not constitute independent randomized fault programs. Competence controls and fault conditions are paired. Conditional recovery is reported only on control-capable support, with explicit support denominators; goal-only completion, forbidden effects and duplicate effects remain separate. External uncertainty is clustered by the 12 upstream tasks and is supplementary.

Two earlier external launch failures were local import/interpreter mistakes before any HTTP generation. Their unstarted registrations remain. The corrected pre-TEST external DEV phase genuinely executes all 20 fixed cases with 42 model calls. It is not counted as TEST.

## I. Negative results, invalidity and protocol deviations

All early engineering cohorts remain, including required-native-tool formatting failures, incomplete actors, bootstrap corruption, failed reference attempts and serving/readiness failures. DEV changes ceased before TEST. Original v11 frozen runs, negative evidence and financial history remain preserved. A failed full legacy timing regression is documented with its raw autosave branch; an unchanged targeted recheck passes. The final ten relevant v12 tests and twelve scripted native orchestration cases pass. Scripted outputs are never counted as model calls.

Finite serving cold starts, parent deadlines, current serving load, singleton bootstrap cells, constructed task diversity, unrecorded exact SQL commit/read instants and limited larger-model support are material limitations. The release audit must list every remaining unexecuted assignment explicitly. A reconciled NOT_RUN record does not count as an executed trial or establish a scientific endpoint.

## J. Reproduction and provenance

Saved-data commands require no paid inference. Re-run the frozen analysis against all reconciled run roots, independently re-score snapshots, build and verify graph references, regenerate scientific figures and render this appendix with the bundled workspace Python. Live experiments additionally need the dedicated endpoints, fresh credits, PostgreSQL and Chromium. A closed paid job cannot be relaunched; only genuinely never-started assignments may enter a newly registered finite job. Raw invalid cases must never be overwritten to obtain a green summary.

The reproducibility package includes source, task contracts, freeze hashes, reference evidence, all retained model traces, raw receiver/application snapshots, analysis reports, per-trajectory vector timelines, renderer source, environment manifests and separate old/new financial records. Hash manifests verify content, not scientific truth. No API secret or provider profile is required for saved-data reanalysis.
