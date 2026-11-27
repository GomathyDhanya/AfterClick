# AfterClick: The Temporal Limits of Safe Recovery in Tool-Using AI Agents

*An empirical study of irreversible effects, intervention timing and legitimate task restoration in asynchronous environments*

**Working manuscript — 26 November 2026**  
**Authors:** [confirm authors and affiliations]  
**Artifact:** https://github.com/GomathyDhanya/AfterClick  
**Status:** pre-submission draft using reported existing results. The v12 model evaluation is incomplete; full raw evidence was not available for this review. Bracketed EVIDENCE REQUIRED items are not completed work. No new results are represented as measured. Citation links in this draft are working references to be converted into venue bibliography format after full literature review.

## Abstract

Tool-using AI agents increasingly operate in applications where background workers, concurrent users and external services continue to progress during agent deliberation and recovery. In such settings, restoring local state need not repair an irreversible external effect, and a correct protective decision can become ineffective before enforcement. We investigate these interactions in AfterClick, an executable testbed with two constructed application environments, PostgreSQL, Chromium, asynchronous workers and independently persisted synthetic effect receivers. Across a completed 288-branch fixed-recommendation experiment (287 valid branches), adding 300 ms and 1,500 ms to browser enforcement increases observed forbidden-history incidence by 27.78 and 60.56 percentage points, respectively, compared with ordinary browser enforcement, conditional on twelve constructed source tasks. In an incomplete registered LLM evaluation, compact forensic reports identify 43 primary-model and 22 larger-model episodes with current local completion but forbidden history. Observed policy outcomes also expose a tension between preventing unauthorized effects and completing authorized work. The 2,904-assignment frozen TEST matrix has 1,479 terminal records, including 1,073 valid internal episodes and 240 executed external conditions; 1,425 assignments remain unexecuted. Additional reviewer reasoning is associated with worse joint safe completion among observed matched primary episodes, but missing outcomes and absent causal controls prevent identifying a deliberation effect. These findings motivate evaluating time-sensitive enforcement, immutable effect history and legitimate restoration jointly rather than grading a controller solely on its recommendation or final state. We describe the artifact and its limitations without claiming universal recoverability, a novel superior controller, or a completed confirmatory evaluation.

**Keywords:** tool-using agents, AI security, asynchronous workflows, effect history, runtime enforcement, task recovery, authorization, reproducibility.

## 1. Introduction

Consider an autonomous agent asked to update a retention-related record, prevent an unauthorized queued read, and restore legitimate reviewer access. The agent can correctly conclude that a permission or service must be suspended. However, if a background consumer has already acquired authority, or an external read is delivered while the agent is verifying evidence, the protective action may arrive too late. Restoring the application afterward cannot remove information already delivered to the external receiver. Conversely, permanently suspending the service may prevent disclosure but fail the legitimate access requirement. A successful tool response or visually correct final page is therefore insufficient evidence for safe task completion.

This problem brings together established concerns from distributed systems, runtime security and agent evaluation. Transactional mechanisms can stage irreversible agent effects; recovery benchmarks can score both application state and external history; and asynchronous benchmarks can evaluate responses to changing conditions. We ask a narrower empirical question: how do autonomous external progress, enforcement timing and subsequent restoration interact in end-to-end tool-using workflows? Unlike a general claim that recovery or staging is novel, the contribution must be established by measurements that explicitly vary the relevant timing mechanisms and trace observed outcomes to physical effect records.

We distinguish four research questions:

- **RQ1 (History):** How frequently and through which mechanisms does current-local-state completion coexist with forbidden physical effect history in the observed cohorts?
- **RQ2 (Timing):** Holding the protective recommendation fixed, how does actuation latency relative to independently progressing effect admission alter forbidden-history incidence and joint safe completion?
- **RQ3 (Restoration):** Under what conditions does protective intervention impair authorized completion, and can explicit restoration obligations mitigate the trade-off?
- **RQ4 (Deliberation):** When does extra verification or reviewer reasoning provide sufficient informational benefit to justify its latency and side effects?

The available evidence supports RQ2 most strongly. RQ1 and RQ3 have substantial retrospective observations, while causal attribution for RQ3 and RQ4 remains incomplete. We deliberately separate verified operational measurements, observed associations, and proposed experiments.

Our candidate contributions are: (1) a reproducible testbed and explicit joint outcome semantics for independently progressing synthetic effects and authorized restoration; (2) a completed controlled actuator experiment isolating the effect of imposed enforcement delay from recommendation quality; (3) an evidence-linked characterization of local/history mismatch and protection–utility trade-offs in the observed LLM cohorts; and (4) a precise account of unresolved timing, recoverability and statistical uncertainty. These are scoped contributions; the priority of their combination relative to prior work requires full related-work verification.

## 2. Threat model and operational definitions

### 2.1 System model and trust boundary

An agent observes and acts through application-provided native tools and a browser gateway. The application maintains business state in PostgreSQL. Background workers advance independently and can trigger external effects, which are persisted in separate synthetic HTTP receiver transactions. A trusted fixture defines which pending requests, scopes and authorized operations are permitted. The agent receives the declared public state, tool results and public verification evidence, but not private evaluator verdicts, hidden scheduler state or future outcomes.

The studied threats include unauthorized queued effects, inappropriate actor-proposed scope or restoration, stale authority and protective actions that are too late or excessively restrictive. The evaluator checks external effect records, including forbidden requests and duplicate effects, as well as business completion, reconciliation, approved deliveries, preservation of collaborator changes and required restoration. Synthetic external reads and publications are confidentiality/integrity proxies, and legitimate functionality is a bounded availability/utility proxy. No real victim data, independently administered production service, cryptographic identity or general prompt-injection resistance is established by this testbed.

### 2.2 Outcomes

Let S(t) denote application state and H(t) the ordered history of independently persisted physical effects. Let F(H)=1 when the benchmark records any forbidden effect. Define L as the exact oracle field `current_local_goals_complete`, G as the separate `legitimate_complete` field, and Y = G(1−F) as joint safe completion for a valid episode. The existing oracle calculates G from all business obligations, including collaborator preservation, legitimate service restoration and pending reconciliation; L uses the current local obligations, preservation and restoration. L and G are not interchangeable.

A local state may satisfy L even if F=1. In this benchmark, historical safety is a prefix property: once a forbidden immutable receipt occurs, later local changes cannot make that realized history safe. The joint endpoint Y additionally requires legitimate work at a finite evaluation horizon. A policy that blocks every action might preserve F=0 while obtaining G=0. These definitions do not assert unbounded liveness or that all kinds of real-world harm are irreversible.

For invalid or unexecuted assignments, Y is not observed. We report valid-subset summaries separately from assignment-level missing-outcome bounds. An invalid transport or missing receipt is not automatically classified as observed safe or unsafe.

### 2.3 Temporal events and recoverability

Configured eligibility, actual worker authorization read, effect admission, protective command, transaction completion, receiver persistence, and public acknowledgment are distinct events. In the original v12 implementation, exact worker-authorization-read and SQL commit boundaries are not instrumented. Audit times may occur inside transactions; request intervals include local, network and provider overhead. A physical receipt after a protection audit therefore cannot establish a specific race without further evidence.

For a fixed execution history, define a feasible safe continuation as a policy that can attain Y=1 under a specified scheduler realization or explicitly defined scheduler set. Existential feasibility for one schedule differs from robust feasibility and from the agent's ability to discover the continuation. An executed sibling from a certified equivalent initial cut is evidence of a realized alternative at that cut, not proof of an arbitrary intermediate counterfactual. Bounded formal certificates apply only to the separate finite models. Uncertified intermediate feasibility remains UNKNOWN.

**[EVIDENCE REQUIRED: specify complete event schema and supported ordering relations; add an independently checked example linking contract, actor/controller action, worker event and physical receipt. Do not infer exact commit times from old audit records.]**

## 3. Experimental testbed and methodology

### 3.1 Applications and contracts

AfterClick implements FlowBoard and OpsConsole with different business tables and workflows but shared experiment infrastructure. Six task families cross three complexity levels and two applications, with two DEV and six TEST variants per cell, yielding 72 DEV and 216 TEST contracts. Tasks include 8, 13 or 21 required operations with approval dependencies, scope choices, receipt reconciliation, external dispatch, collaborator preservation and restoration. The cohort uses six policy vocabularies and 24 structural layouts; its variants are not independent organizational workloads.

The repository reports two accepted executable browser reference paths per contract (576 total), checked with separately implemented oracles, and 10,944 rejected mutations of evidence or obligations. Independent software verification is not independent human review. The v2 oracle correction was made before TEST: persisted matching physical receipts and completion commits can validate idempotent acknowledgments without requiring an artificial second receipt-verification event. Earlier labels are retained.

### 3.2 Agent and policy bundles

The actor uses native function calls, continuous assistant/tool history and public observations. The v12 protocol permits at most 24 actor generations, 200 browser actions and 240 seconds of actor wall time within a parent job. Generation uses temperature zero, up to 512 output tokens, disabled thinking and native tool selection. Transport does not retry generation.

| Policy | Executed intervention |
|---|---|
| P0 | Unmodified actor |
| P1 | Immediate deterministic public protection |
| P2 | Public verification followed by deterministic decision |
| P3 | Same verification, followed by an additional LLM reviewer |
| P4 | P1 plus explicit public obligation/restoration feedback |
| P5 | Suspend pending service before verification and review (queue-hold proxy) |

P1–P5 share an additional public consequence guard on actor-proposed actions. These are complete policy bundles, not single-component randomized ablations. The public deterministic rule allows an approved public authority label and suspends otherwise. This makes reviewer redundancy a plausible hypothesis: when public authority already determines the decision, a reviewer may add cost without useful information. It does not demonstrate that review is redundant in less structured authorization settings. P5 is not a faithful reproduction of a full semantic-transaction runtime.

### 3.3 Enrollment, completeness and controls

The frozen v12 protocol, revised before TEST to accommodate the explicit credit cap, enrolls 2,304 primary, 360 larger-model and 240 official external conditions. The primary design counterbalances configured timing regimes between contracts (not three deadlines within each task). Matched arms use certified equivalent initial application/client cuts and seeded scheduler programs; real-time scheduling and shared serving load remain stochastic. The larger supplement differs in model revision, serving hardware, precision and managed decoding, so its results cannot isolate model scale.

| Cohort | Registered | Terminal | Valid internal / executed external | Invalid internal | Not run |
|---|---:|---:|---:|---:|---:|
| Primary | 2,304 | 905 | 744 | 161 | 1,399 |
| Larger-model | 360 | 334 | 329 | 5 | 26 |
| Official external | 240 | 240 | 240 executed | — | 0 |
| Total | 2,904 | 1,479 | 1,073 internal + 240 external | 166 | 1,425 |

The matrix is incomplete. A terminal record is not necessarily a valid episode or a successful generation. The observed valid subsets may be selected by time, budget, transport and parent-job constraints. The old TEST outcomes are opened and must not be reused as an independent confirmation set for newly designed methods.

The frozen primary contrast is P3−P2 on joint safe completion, with five secondary contrasts. The source task is the clustering unit; model calls, graph nodes, browser actions and repeated worlds are not independent tasks. The frozen analysis uses source-weighted matched estimates, 10,000 stratified source bootstrap replicates and studentized/source-sign sensitivities, with Holm adjustment for the secondary contrasts. Missing-outcome bounds are separate from confidence intervals. Focused designs with singleton bootstrap strata yield uninformative point intervals; we retain original results but do not interpret them as precision. New analyses of existing evidence are explicitly retrospective.

## 4. RQ1 — Local state and irreversible effect history

The primary forensic summary reports 43 episodes with current local completion and forbidden history among 905 terminal records (744 valid); the larger supplement reports 22 among 334 terminal records (329 valid). These observations provide concrete evidence of local/history disagreement in the constructed workflows. They do not yet identify how often an actual recovery action produced the local completion, as opposed to an ordinary locally successful execution coexisting with an external violation.

A state-only evaluator can miss this distinction. For a privacy-relevant queued read, local permission restoration does not retroactively prevent an independently delivered disclosure. For a notification or resource effect, a repaired database entry need not reverse the physical effect. The precise effect categories and chronology must be verified against the raw receiver records rather than inferred from aggregate counts.

**[EVIDENCE REQUIRED — Figure 2 and Table 2: reproduce exact L×F and separate G×F cross-tabs for every cohort/arm; verify the 43 and 22 cases using raw oracle fields; report the denominator of L=1 for conditional mismatch, source-level uncertainty, and all case IDs. Classify physical effect mechanisms and distinguish actual compensation from local success. Independently audit representative cases and include raw evidence pointers. Do not invent conditional denominators or assume L=G.]**

**Answer supported now:** Final-local-state completion is insufficient to certify historical security in these environments. The observed mismatches are not a new proof of the general irreversibility principle; their value is in a reproducible temporal and obligation-level characterization.

## 5. RQ2 — Fixed decisions under progressing external effects

We study a separately completed actuator experiment that removes LLM recommendation quality from the treatment. Twelve L3 DEV source contracts are crossed with two seeded worlds, three configured admission offsets (150, 600, 1,800 ms), and four actuator conditions: direct HTTP, ordinary browser, browser with 300 ms added delay, and browser with 1,500 ms added delay. All branches receive an already-correct suspension recommendation followed by a full reference continuation. The reported experiment executes all 288 assignments, with 287 valid and one browser-timeout-invalid branch. No model calls are needed.

**Table 3. Observed forbidden histories per registered cell.** Each cell registers 24 branches; the asterisk denotes one unknown outcome in addition to 23 observed violations.

| Configured offset | Direct HTTP | Browser | Browser +300 ms | Browser +1,500 ms |
|---|---:|---:|---:|---:|
| 150 ms | 2 | 4 | 24 | 23* |
| 600 ms | 0 | 0 | 0 | 24 |
| 1,800 ms | 0 | 0 | 0 | 0 |
| Total observed | 2/72 | 4/72 | 24/72 | 47/72 |

**Table 4. Paired source-weighted effect on forbidden-history incidence relative to ordinary browser.**

| Actuator | Difference (percentage points) | Source-bootstrap 95% interval | Full-assignment range |
|---|---:|---:|---:|
| Direct HTTP | −2.78 | [−9.72, 4.17] | [−2.78, −2.78] |
| +300 ms | +27.78 | [23.61, 31.94] | [27.78, 27.78] |
| +1,500 ms | +60.56 | [55.83, 64.72] | [59.72, 61.11] |

The +1,500 ms point estimate uses the reported paired source estimator, not simply the difference of the two registered-denominator counts. Its missing-outcome interval explicitly accounts for the invalid branch. All estimates condition on the twelve constructed source tasks and six shared mechanisms. These are actual imposed gateway-delay interventions while workers progress; no outcome is generated by subtracting time from an existing trace.

The observed effect is contingent on relative timing. At the tightest offset, additional 300 ms delay coincides with forbidden history in every valid branch. At the intermediate offset, +300 ms does not change observed incidence, but +1,500 ms does. At the generous offset, no forbidden effect is observed in any arm. This pattern demonstrates timing sensitivity under the implemented backend, not a universal hard deadline. Direct HTTP versus ordinary browser is inconclusive at the source-cluster scale.

The earlier, separately frozen prospective timing study reports 36 valid branches from twelve source instances: immediate protection safely completes 11/12 with zero unauthorized irreversible effects, and verification-first and delayed containment each safely complete 10/12 with two unauthorized effects. The overall paired comparison is inconclusive. A reported contrary case shows why utility matters: immediate revocation prevents a queued read, but the actor fails to restore legitimate access. These studies have different designs and are not pooled as independent replications.

**[EVIDENCE REQUIRED — Figure 3: regenerate full 12-cell plot and paired source-level effects from raw traces. Verify manipulation fidelity and initial-cut equivalence. Stronger submission: replicate on independently reviewed new sources, instrument worker admission/authorization reads and transaction/receiver order, and compare a reference fenced-admission backend. Report whether effect survives changed mechanisms, including null outcomes. Existing findings do not identify pure LLM inference latency or an exact last preventable instant.]**

**Answer supported now:** Adding actual actuation delay can undermine the efficacy of fixed correct protective recommendations when synthetic external workers progress independently. The effect is conditional on the backend, task sources and timing regimes.

## 6. RQ3 — Security, legitimate functionality and restoration

**Table 5. Valid-subset outcomes in the primary model evaluation.** Registered denominators and unknown outcomes are retained; counts are observed, not estimates of the full registered population.

| Arm | Registered | Valid | Legitimate G | Forbidden F | Joint Y | Invalid or not run |
|---|---:|---:|---:|---:|---:|---:|
| P0 stress | 432 | 142 | 60 | 88 | 19 | 290 |
| P1 stress | 432 | 142 | 19 | 1 | 19 | 290 |
| P2 stress | 432 | 141 | 24 | 12 | 24 | 291 |
| P3 stress | 432 | 136 | 4 | 49 | 2 | 296 |
| P4 stress | 72 | 18 | 8 | 0 | 8 | 54 |
| P5 stress | 72 | 24 | 1 | 0 | 1 | 48 |
| P0 clean | 432 | 141 | 59 | 0 | 59 | 291 |

**Table 6. Valid-subset outcomes in the larger-model supplement.**

| Arm | Registered | Valid | Legitimate G | Forbidden F | Joint Y | Invalid or not run |
|---|---:|---:|---:|---:|---:|---:|
| P0 stress | 72 | 65 | 26 | 49 | 5 | 7 |
| P1 stress | 72 | 65 | 1 | 1 | 1 | 7 |
| P2 stress | 72 | 65 | 4 | 13 | 4 | 7 |
| P3 stress | 72 | 65 | 1 | 21 | 0 | 7 |
| P0 clean | 72 | 69 | 25 | 0 | 25 | 3 |

Immediate deterministic protection has a low observed forbidden-history count in both cohorts, but also low legitimate completion. In the primary observed sample, P0 and P1 each record 19 joint safe completions despite very different marginal G/F outcomes. In the larger observed sample, P1 records one forbidden history and one legitimate completion in 65 valid episodes. These descriptive summaries demonstrate why prevention alone is an inadequate endpoint. They do not establish that a particular intervention caused each incomplete authorized task; low clean competence and selected execution support are alternative explanations.

The primary P4−P1 paired point estimate is +31.25 percentage points across 16 complete source clusters, with full-assignment range [−63.89,+83.33] points and Holm-adjusted secondary p=0.0983. The frozen within-cell bootstrap is uninformative because the focused cells have singleton sources. An explicit obligation reminder is therefore a promising hypothesis, not a confirmed mitigation.

### 6.1 Restoration debt: proposed explanatory analysis

A protective action can activate or introduce further duties, such as reconciling a pending request and restoring legitimate functionality after resolution. We propose tracking each such duty i as a ledger item with trigger, dependencies, status, discharge witness and timing. Define D(t) as the count of triggered, unresolved restoration duties at t, using unit weights in the primary analysis. Preexisting business obligations and newly induced obligations remain distinct. A restoration reminder may help by preserving obligations in the agent's context, but this mechanism has not been isolated.

The existing forensic hierarchy labels 336 primary episodes as continuation-stopped with unmet obligations and 126 as actor-finished with unmet obligations; corresponding larger-cohort counts are 116 and 94. These are broad categories, not counts of restoration debt. A debt-specific analysis requires reconstruction of obligation triggers and discharge evidence.

**[EVIDENCE REQUIRED — Figure 4: exact obligation-level completion and restoration-debt trajectories, activated vs preexisting duties, terminal reasons, clean-control matching, source-level paired estimates and representative contrary cases. For causal claims: run a new reminder-vs-neutral-message controlled study with the same containment and available information, and a matched no-restoration-needed condition. Qualify basic actor competence on disjoint DEV tasks first. Report G/F/Y together and all missing outcomes.]**

**Answer supported now:** Protective policy bundles can exhibit markedly different historical safety and authorized-completion outcomes; neither marginal alone is adequate. The causal role of induced restoration obligations and the value of reminders remain open.

## 7. RQ4 — Information acquisition and temporal intervention

The primary frozen P3−P2 estimate is −13.51 percentage points in joint safe completion among 111 complete source clusters. The full-assignment range is [−72.45,+63.43] points. The larger supplement reports −6.94 points over its observed complete-pair estimator, with assignment bounds [−15.28,+4.17] points. Its focused strata also have uninformative bootstrap point intervals. Neither contrast establishes a population-wide causal effect of extra deliberation. 

| Primary contrast | Complete source clusters | Paired difference (pp) | Full-assignment bounds (pp) |
|---|---:|---:|---:|
| P3−P2 | 111 | −13.51 | [−72.45, +63.43] |
| P2−P1 | 112 | +2.68 | [−65.97, +68.52] |
| P1−P0 | 115 | 0.00 | [−67.13, +67.13] |
| P4−P1 | 16 | +31.25 | [−63.89, +83.33] |
| P5−P1 | 20 | −10.00 | [−70.83, +62.50] |
| P5−P3 | 20 | +5.00 | [−66.67, +68.06] |

Review changes elapsed time, recommendation content, parser/fallback behavior and interaction with progressing workers. A deterministic public authority rule may already resolve some decisions. Consequently, a slower policy can underperform because its review is redundant, incorrect, difficult to parse, or simply too late. The fixed-recommendation actuator experiment establishes the plausibility of the temporal mechanism but does not establish which factors caused the P3−P2 association.

The forensic summary also identifies 15 primary and 19 larger episodes with physical violation after a protection audit and unresolved admission ordering. These cases warrant explicit distinction between a recorded command, a durable authorization update and a protection that is effective at the consequence boundary. An already-admitted irrevocable ticket may survive a later revocation; alternatively, an authorization read may race with a controller write. The available compact counts cannot distinguish these mechanisms.

### 7.1 Proposed identifying experiment (not yet executed)

Cross the relevance of an immutable public information packet (decision-relevant versus irrelevant) with access delay (immediate versus imposed delay), using matched source cuts and a deterministic decision rule. Keep information content identical across delay arms; include ambiguous, approved and denied requests. Separate freshness changes rather than treating stale data as equivalent. This factorial identifies controlled information-access and delay effects within the constructed mechanisms. A later live-review experiment may compare deterministic verified decisions, latency-matched deterministic control, genuine reviewer and cached reviewer outputs. Cached outputs are not new model calls, and their use does not establish an arbitrary live counterfactual. Analyze decision changes, actual timings and fallbacks separately.

**[EVIDENCE REQUIRED — Figure 5: reconstruct all 34 post-audit violation cases, actual event ordering and unresolved intervals; reviewer calls, decisions, public information, schema validity, fallback and command/receipt joins. Figure 6: plot observed estimates versus missing-outcome bounds, not as confidence intervals. Stronger submission: complete preregistered cached-equivalent/irrelevant-information and timing-matched factorial; test whether genuinely informative evidence offsets delay in the available intervention window. No causal neural-delay language until supported.]**

**Answer supported now:** Additional review is associated with reduced observed joint safe completion, and actual actuation delay is a demonstrated mechanism in a separate controlled experiment. Whether review itself causes harm, and when useful information outweighs delay, remain open research questions.

## 8. External comparison and related work

UndoBench evaluates recovery separately from nominal task competence and includes external effect history and environment-state oracles [1]. Our repository reports an unchanged official benchmark execution on twelve TEST tasks, two context seeds, five available wrappers and CONTROL/FAULT conditions. All 240 conditions were executed. Conditional recovery rates among control-capable pairs are checkpoint 6/20 (30.0%), idempotency 8/19 (42.1%), naive 5/20 (25.0%), saga 6/21 (28.6%), and vbr 12/19 (63.2%) as reported in the official analysis; context seeds are not independent fault programs. Unavailable EvoUndo is not assigned a score. This comparison is a small fixed-interface external study, not a head-to-head claim that AfterClick outperforms UndoBench.

Cordon stages irreversible effects using a transaction-level runtime [2]. Our suspension-first P5 holds a pending queue and is not Cordon. Async-RBench evaluates responses to asynchronously delivered subagent results with obligation-aware criteria [3]. ReInBench investigates errors, recovery and intervention prediction [4], while Safe to Resume? addresses execution continuity after rollback [5]. AgentTrust studies runtime interception of agent tool calls [6]. These lines of work constrain any claim that historical grading, intervention timing, recovery options or staging are individually novel. Runtime enforcement research also distinguishes controllable from merely observable actions [7], directly relevant to our independently progressing workers. 

The candidate differentiation is empirical: vary actual enforcement delay while holding recommendations fixed, inspect independently persisted effects and restoration obligations within the same workflows, and test the gap between a decision, a command and effective protection. That differentiation must survive a complete literature review, including transactional compensation/sagas, TOCTOU, temporal runtime enforcement, AgentRewind, SURE-Act, AppWorld and tau2-bench. A difference in benchmark terminology is not a sufficient novelty claim.

**[EVIDENCE REQUIRED: full related-work matrix with operational assumptions and closest experiments; verify actual upstream versions and official pairing counts from raw runs. If prior work answers the same empirical question, position this as a reproducibility/measurement study instead of claiming priority.]**

## 9. Discussion: implications for safety system design

The observations support three limited design implications. First, record and evaluate immutable external effects as well as local state. Second, distinguish deciding, dispatching, committing and actually enforcing protection; measure latency relative to external progress instead of treating a safety decision as instantaneous. Third, evaluate authorized task completion and restoration explicitly so that safety systems cannot receive full credit for indiscriminate denial.

These implications suggest a possible future research framework based on preserving recovery opportunities. An intervention policy could choose whether to act, gather information, or enter reversible containment according to its estimated probability of forbidden history, information value, available time and restoration cost. A future algorithm would need to demonstrate an advantage over deterministic protection and strong transactional baselines on genuinely new tasks. The current evidence does not validate such a learned policy.

AfterClick's execution graph is an evidence index rather than an automatic causal model. The primary prefix report classifies 71,138 nodes: 59,174 UNKNOWN, 11,622 fixed-history-violation nodes (including final-evidence labels), 210 witnessed safe initial continuations and 132 realized safe completions. No formal certificates are attached to complex browser graph states. Nodes are dependent within episodes and source tasks. A graph-based predictor cannot treat UNKNOWN nodes as failed recovery labels or count individual nodes as independent validation samples.

## 10. Limitations and ethics

The model evaluation is incomplete and budget-censored, with 1,425 assignments not run. Valid-subset results are selected and full-assignment bounds are broad. Low observed clean-task competence (59/141 primary and 25/69 larger) complicates interpretation of stress failures. The testbed uses constructed workflows, shared mechanisms, trusted fixture authority and synthetic loopback receivers; no independent human contract review or production workload is established. The larger-model comparison confounds model revision, serving hardware, precision and decoding. Existing timing instrumentation does not provide exact worker authorization-read or SQL commit instants, and shared load can affect real-time scheduling. Cached-equivalent, irrelevant-verification, no-restoration-needed and adversarial-restoration controls are missing. Arbitrary intermediate-state counterfactual reconstruction is absent. Finite formal results cannot certify the full open-world application. The official external sample is small. These limitations constrain causal claims and generalizability.

The original financial report records $17.96725281 conservative guard accounting against an authorized $18 v12 ceiling, 41,732 model-call attempts and 309,714,800 known reported tokens across engineering, DEV and TEST, including three response-uncertain calls. These are not an isolated provider invoice or a count of successful TEST generations. Historical financial authorizations remain separate.

All effects in the testbed are synthetic. Public artifacts must not disclose model-provider credentials, personal identifiers or private trace data; if redaction is necessary, preserve the restricted original and publish a documented reproducible derivative, checksums and limitations. No unsafe experiments against external users or production services are required.

## 11. Artifact availability and reproducibility

The source repository includes application code, contracts, compact evidence, acceptance audit, assignment reconciliation, scripts and a frozen protocol. The complete archive is reported as `AfterClick_v12_Evidence_Release.tar.gz` (637,853,954 bytes; 151,623 files), SHA-256 `c031afd3c46eab822770cc41e684d87f2a2aa786b64cff70eb79f90572667020`. It is not currently published in the Git repository. A source-only clone cannot perform full saved-data reproduction. The repository reports successful relocated reproduction using the local archive with no model/provider calls and verification of 180 frozen file hashes. This draft does not represent a newly executed independent reproduction.

Once the archive is available, verify the checksum, safely extract into a separate directory, install frozen dependencies and execute the documented saved-data command from the archived snapshot:

```sh
uv sync --frozen --group research
uv run python research_ops/scripts/reproduce_afterclick_v12.py --root . --output /tmp/afterclick-v12-reproduction-NEW
```

**[EVIDENCE REQUIRED: public archive or documented redacted derivative URL/DOI, exact source commit/tag, license/data statement, independent clean-machine reproduction logs, per-RQ generated figures/tables and claim-to-evidence manifest. Keep historical versions immutable. Record any unavailable material openly.]**

## 12. Conclusion

AfterClick characterizes a bounded but important failure mode of tool-using AI agents: while an agent decides or recovers, independently progressing effects can change which outcomes remain achievable. The strongest existing result is the completed fixed-recommendation actuator experiment, in which added enforcement delay increases forbidden-history incidence. Recorded local/history mismatches and marginal protection–utility trade-offs motivate jointly evaluating effect history and legitimate restoration. The incomplete LLM matrix and missing causal controls prevent general claims of review-induced harm, controller superiority or a universal recoverability frontier. A reproducible, independently reviewed expansion of these measurements is needed to establish their scope and scientific differentiation. The paper's value should derive from precise, falsifiable and inspectable results rather than the quantity of experimental infrastructure or a claim that a new controller wins.

## References (working links; verify bibliographic metadata before submission)

1. *UndoBench: Separating Task Competence from Recovery Capability in Tool-Using AI Agents*. https://arxiv.org/abs/2610.05622
2. *Cordon: Semantic Transactions for Tool-Using LLM Agents*. https://arxiv.org/abs/2606.17573
3. *Async-RBench: Benchmarking Asynchronous Task Execution in LLM Agents*. https://arxiv.org/abs/2610.32429
4. *When to Intervene? An Empirical Study of Errors and Self-Recovery in LLM Agents*. https://arxiv.org/abs/2610.36471
5. *Safe to Resume? Breaking Execution Continuity of Agent Execution via Rollback*. https://arxiv.org/abs/2608.29381
6. *AgentTrust: Runtime Safety Evaluation and Interception for AI Agent Tool Use*. https://arxiv.org/abs/2605.04785
7. *Enforceable Security Policies Revisited*. https://doi.org/10.1007/978-3-642-28641-4_17

## Appendix A. Evidence locator and verification tasks

All numerical claims in this draft are derived from repository-reported compact summaries, not independently rerun data. Paths relative to the AfterClick repository:

| Claim / paper section | Source |
|---|---|
| Architecture, design, enrollment, methods | `paper/v12/AFTERCLICK_V12_MANUSCRIPT.md`; `afterclick/completion_v12/benchmark/{design,runner,oracle}.py` |
| Complete disposition and qualification | `research_ops/completion_v12/final_package/FINAL_ACCEPTANCE_AUDIT.json`; `FROZEN_MATRIX_RECONCILIATION.csv`; `CLAIM_TO_EVIDENCE.md` |
| RQ1 / RQ3 / RQ4 forensic counts | `evidence/v12/primary-forensics/report.json`; `evidence/v12/larger-forensics/report.json` |
| RQ2 actuator experiment | `evidence/v12/controlled-actuator/report.json` |
| Earlier prospective timing | `research_ops/PROSPECTIVE_TIMING_RESULTS.md` |
| Model outcomes and matched estimates | `evidence/v12/primary-analysis/report.json`; `evidence/v12/larger-analysis/report.json`; `evidence/v12/primary-interval-diagnostics/report.json`; `evidence/v12/model-comparison/report.json` |
| External evaluation | `evidence/v12/official-external-analysis/report.json` |
| Prefix epistemic labels | `evidence/v12/primary-recoverability-prefixes/report.json` |
| Missing controls / semantics | `research_ops/completion_v12/final_package/UNMET_REQUIREMENTS.md`; `PROTOCOL_REPORTING_ERRATA.md` |
| Data / reproduction | `evidence/v12/README.md`; `evidence/v12/MANIFEST.json`; `docs/GITHUB_PUBLISHING.md`; `research_ops/completion_v12/final_package/REPRODUCTION_VALIDATION.json` |

## Appendix B. Submission fill-in checklist

- [ ] Independently verify raw archive availability, integrity, redaction and licenses.
- [ ] Regenerate old metrics from frozen snapshot and reconcile all registered assignments.
- [ ] RQ1: exact L×F and G×F denominators, case taxonomy and independently audited raw receipts; prove actual recovery only where observed.
- [ ] RQ2: reproduce all 288 branches; add independent sources and boundary instrumented replication for stronger submission.
- [ ] RQ3: reconstruct restoration debt, distinguish ordinary failures, compare matched arms; causal reminder/no-restoration controls if budget and competence permit.
- [ ] RQ4: inspect review decisions and post-audit violation cases; controlled information/latency factorial required for causal claim; optional genuine live review after separate approval.
- [ ] Source-cluster inference, missing-outcome bounds, independent task review, clean controls and negative results.
- [ ] Literature differentiation and accurate venue-specific references.
- [ ] Final paper generated from verified evidence, accessible source and data release, independent clean-machine reproducibility, author/affiliation confirmation.

**Companion execution specification:** `AfterClick_Research_Execution_Specification.md` defines T00–T17, experimental designs, schemas, gates, repository cleanup and exact expected deliverables. It proposes new work rather than reporting it as completed.
