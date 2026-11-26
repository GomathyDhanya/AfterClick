# AfterClick: The Limits of Recoverability in Tool-Using LLM Agents

*An Empirical Study of Asynchronous Side Effects, Delayed Verification, and Safe Intervention*

Bounded empirical report, 25 November 2026 UTC. Venue and author formatting remain unspecified. Earlier protocols, manuscripts, negative results and failed experiments are preserved separately.

## Abstract

A tool-using agent may lose the ability to prevent an external consequence while it is deciding what to do next. We study prospective protection when background effects continue during real model inference, distinguishing local rollback, current-state recovery, historical obligations and safe task completion. AfterClick combines a collaborative browser application, real PostgreSQL transactions, asynchronous mock consumers and immutable independent receipts. A new frozen comparison uses Qwen3.5-9B on 12 source instances spanning notification, delegated access and resource consumption, with six authorized-effect and six prohibited-effect tasks. Three dependent continuations per source compare immediate protective cancellation or revocation, verification-first intervention, and delayed containment. All 36 branches pass reconstruction and independent scoring checks; 145 new model generations produce 140 native function calls. Immediate protection yields no unauthorized irreversible effects, versus two sources for each delayed policy, but misses one legitimate restoration objective. Safe task completion is therefore 11/12 versus 10/12: an inconclusive paired difference of 8.3 percentage points with a conservative 95% interval of [-41.2, 52.4]. A prohibited delegated-access commitment occurs during actual inference, before the later external read; a separate immediate-protection branch prevents access but Qwen omits restoration. The result is an operationally witnessed safety/utility trade-off, not controller superiority. Earlier search and learning comparisons remain negative against strong simple baselines. UndoBench already captures the demonstrated state/history ranking reversal, and Cordon establishes staged external effects; neither distinction is claimed as new. The contribution is a scoped, reproducible measurement of prospective intervention under progressing effects. Broad publication novelty remains limited.

## 1. Introduction

Consider an agent asked to update an incident note while preventing a queued notification. Editing the note may be reversible. Delivering the notification is different: restoring the application record cannot remove the recipient's observation. The agent can also be too late before any receipt is visible. A consumer may have admitted an external read under delegated authority while the model is still generating its next action; revoking the parent afterward need not recall that admitted request.

The relevant question is prospective: **when does immediate protective intervention improve safety relative to verification-first and delayed recovery, and what legitimate-task completion cost does it impose?** An early cancellation can preserve an opportunity that verification consumes. It can also change the remaining task: temporarily revoked permission must eventually be restored. Counting only forbidden effects rewards a controller that leaves legitimate work unfinished; counting only task fields can reward a completed task with an unauthorized historical effect.

We contribute an executable, scoped evaluation capability and a bounded empirical comparison. Independent workers progress during actual Qwen inference; admitted counterfactual branches preserve their common browser, database and conversation state; an independent event oracle checks both task completion and external histories. The new confirmation identifies two realized safety gains and one legitimate-completion loss. It does not establish a better general controller, a new rollback principle, or a positive population-level safe-completion effect.

Three questions organize the evidence. RQ1 asks which recovery obligations differ after downstream effects. RQ2 asks whether prevention can be lost before its consequence becomes observable. RQ3 asks how immediate protection changes safe completion relative to specified delayed policies. Earlier controlled studies support mechanism checks and challenge algorithmic claims; the new progressing-schedule Qwen comparison is the primary evidence for RQ3. We never pool synthetic rows and live source instances into a single efficacy population.

## 2. Related work and the remaining distinction

Compensation is established distributed-systems practice. [Sagas](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf) describes long-lived transactions with compensating operations; compensation does not generally erase an independent observer's history. [Consistent distributed snapshots](https://lamport.azurewebsites.net/pubs/chandy.pdf) also motivate including pending communication in a reconstructed state. These are foundations, not AfterClick novelty.

[UndoBench](https://arxiv.org/html/2610.05622v1) separates task competence from recovery using paired trials and state/effect-history oracles, including phase-dependent faults and lost acknowledgments. Its official evaluator already catches the state/history ranking reversal reproduced in our unchanged development-subset baseline audit. We explicitly withdraw novelty based on that distinction. The inspected pinned implementation and published protocol organize interventions around specified execution/fault boundaries. Our added evaluation axis is actual elapsed model/tool time while independently scheduled consumers continue between calls. This is a scoped implementation and measurement distinction, not evidence that UndoBench cannot be extended to cover it.

[Cordon](https://arxiv.org/html/2606.17573v1) provides semantic transactions, shadow state, delegated authority tracking and an effect outbox, with containment, task-correctness and latency evaluation. Immediate staging and controlled release are therefore established. Our queued effects can predate the current agent task or already lie outside its staged transaction; the experiment measures cancellation or revocation of those ongoing operations. We do not reproduce Cordon, claim that it violates its own boundary, or establish an advantage over it.

[SURE-Act](https://arxiv.org/html/2610.24194v1) already uses executed counterfactual alternatives for action selection. [AgentRewind](https://arxiv.org/html/2608.14380v1) addresses recovery within a declared execution boundary. [Safe to Resume?](https://arxiv.org/html/2608.29381v1) identifies incomplete and inconsistent restored state. Runtime shields and active observation are likewise established ideas. AfterClick's reconstruction checks support valid measurements; browser reconstruction is not the headline research contribution. The strongest remaining claim is a bounded operational case study, not conceptual priority or a superior learning algorithm.

## 3. Recovery, prevention and task success

Let X_t=(B_t,Q_t,H_t,U_t,O_t) contain business state, queued operations, immutable external history, authorization and independent obligations, and public observations. A contract C declares current obligations G_current, legitimate task goals G_task, independent preservation I, and forbidden historical events Bad_C. A suppressed-action reference retains independent users' work rather than restoring an old global snapshot.

Fix an admissible action set A_C, resource/action budget b, horizon Delta and environmental schedule sigma. **Current-state recoverability** R_current(X_t;b,Delta,sigma) holds iff there exists an admissible procedure pi, of cost at most b and terminating by t+Delta, whose terminal state satisfies G_current and whose continuation preserves I throughout. This is pointwise existence under the declared schedule. A robust, observation-based guarantee instead requires one policy pi measurable from public observation histories to satisfy those obligations for every compatible sigma. Pointwise oracle feasibility does not supply that stronger epistemic guarantee.

**Full historical-contract recoverability** R_full adds that Bad_C is false for the entire existing prefix and continuation history through termination. A forbidden event already present in an immutable prefix defeats R_full even if the current residual later expires. **Prevention feasibility** P_E is the existence of an admissible intervention preventing a specified future occurrence E through a declared horizon while preserving I; robust prevention again quantifies over every compatible schedule. A missing receipt alone proves neither prevention nor recoverability.

Three observed outcomes must remain separate. **Local rollback success** L is equality of a stated business-state projection to its suppressed reference after an actual recovery procedure. **Legitimate task completion** T is satisfaction of the authorized task objectives. **Safe task completion** S requires T, actual current obligations and independent preservation, and no forbidden historical effect through a complete evaluation horizon. An available future repair is insufficient for S. A failed recovery implementation is insufficient to establish that no admissible repair exists.

The historical finite oracle fixes environmental time and exhausts its declared bounded operation orders. It permits owned-state compensation, pending cancellation and principal refund where supported; it excludes waiting, history erasure, foreign-field overwrite, unavailable child revocation and deadline extension. The new live workload permits ordinary visible waiting, cancellation, temporary parent revocation and later restoration. Its resource consumer has no refund API, so delayed containment is not evaluated as successful compensation. No controller may overwrite independent users' state. Full quantifiers, six regression scenarios and raw-label mappings are in the appendix and versioned predicate specification.

## 4. System and asynchronous mechanisms

FlowBoard is a collaborative task application with autosave and PostgreSQL jobs. The agent receives natural-language instructions and ordinary browser observations, proposes native function calls, and acts through an authorized browser Gateway. Tool results reference the corresponding native call identifier. Completion claims are evaluated independently, not self-graded. The earlier JSON-schema policy remains preserved as an interface baseline.

Three mock services provide distinct consequences. A notification consumer admits and delivers a queued publication. An access consumer snapshots parent permission into a delegated request; a later read can proceed even if the parent is subsequently revoked. A resource consumer irreversibly spends a synthetic unit, with missing acknowledgments and idempotent verification where supported. PostgreSQL event histories and separate loopback HTTP receiver rows are immutable under the application API. An independent evaluator cross-checks issuance, receipts, task changes, resource conservation and actor provenance. All data are synthetic; no real messages, disclosures or payments occur.

Timing quantities differ. The configured eligibility threshold q is imposed by the schedule. Actual consumer admission provides an operational witness that cancellation or revocation has lost control; it is not assumed identical to q. The external receiver records physical observation time T_effect. Public acknowledgment may arrive later or remain missing until verification. Verification and intervention consume measured time. The condition t<F<=t+D describes a race under a specified model; it is not a newly discovered theorem. We do not infer an exact minimal physical frontier from a timer value.

A separately versioned progressing worker advances real PostgreSQL operations and loopback consumers while synchronous model inference runs. Before a fork, the experiment establishes a stopped consistent cut and captures database state, browser caches, dirty buffers, queues/timers, public history and model conversation. Each isolated sibling must pass exact source/clone world, observation, client and conversation certificates before workers resume. We reject inconsistent reconstruction. Snapshot insertion initializes experimental siblings; it is never used as a live recovery action. Supported application cuts are not arbitrary process or in-flight HTTP restoration.

## 5. Frozen real-Qwen study

### 5.1 Development and qualification

Local qualification covers cancellation before and after admission, an external receipt during 0.8 seconds of simulated blocking inference, missing acknowledgment, pending autosave, a concurrent legitimate edit, receipt persistence after actual rollback, and deliberately inconsistent reconstruction. The refreshed review suite passes 25 tests; an additional absolute-horizon qualification passes six targeted tests. A full mock-policy run exercises the actual source/fork/Gateway/oracle path. Its first failure, a completion marker incorrectly inserted into typed action history, was repaired before paid use and retained.

The fixed development pilot has two sources: prohibited publication and authorized resource consumption. It makes 27 genuine Qwen generations and produces six valid branches. All policies safely complete both tasks. Workers progress during requests, but no pilot receipt occurs inside a generation interval. This is execution qualification and a tie, not confirmation of efficacy. No model/prompt sweep follows.

### 5.2 Source population and allocation

The independent confirmation is frozen before outcomes: 12 source instances, four per mechanism, with six authorized-effect and six prohibited-effect tasks. Six service workflows each have two different legitimate core goals: description editing or priority updating, with exact comments where required. The prohibition cases include continued legitimate work, including restoring temporarily revoked review access. Independent source seeds, shuffled short/medium/long eligibility windows and counterbalanced arm orders are fixed in the freeze. These are authored synthetic source instances nested in six workflows and three mechanisms, not twelve applications or a natural error-frequency sample.

Prohibited queued jobs are controlled initial environmental conditions. Qwen organically selects all agent proposals and subsequent actions; no unauthorized agent tool call is injected to make a policy lose. The checkpoint is the earliest model-proposed mutating native batch, regardless of whether an opportunity remains. Recorded pending proposals are executed in each sibling and not recounted as new generations. Subsequent decisions are fresh endpoint calls. No failed source is replaced and no outcome selects a more favorable schedule.

Every branch observes at least 15,000 ms of progressing environment time plus its finite post-policy tail, sufficient for the declared queued schedules. An incomplete horizon is censored, not safe. Actual serving and scheduler variability remain measured nuisance variation. Model-visible input excludes branch identity, hidden schedules, future events, private task predicates and oracle judgments; strict public-input tests reject hidden fields.

### 5.3 Policies and model

Immediate protection applies a public instruction-based cancellation or revocation at the cut, then executes the queued proposal and continues Qwen. Verification-first first performs visible service verification, executes the queued proposal and obtains one fresh Qwen decision, then applies protection if still needed. Delayed containment omits the initial verification but likewise executes the queued proposal and one fresh decision before protection. Later Qwen actions remain organic. Explicitly authorized effects are admitted; blanket cancellation is not used.

These are specified policy packages. Verification-first includes a full agent interaction cycle, not just the latency of a read-only RPC. We do not evaluate an optimized verify-then-cancel automaton or every verification strategy. The delayed arm is an additional containment comparison, not a general compensation algorithm. Existing cancellation and parent revocation cannot erase received content, recall an issued child request or refund consumed units.

All arms use the same Qwen/Qwen3.5-9B revision c202236235762e1c871ad0ccb60c8ee5ba337b9a on the existing compute-billed endpoint, API model AfterClick. Requests use native tools with tool_choice=auto, temperature zero, thinking disabled through the qualified serving configuration, 16,384 input-token and 512 output-token reservations, one concurrent request and no generation retries. Decoding at zero temperature does not ensure deterministic serving. Per-arm continuation and shared block budgets are equal and fixed; realized tool counts need not be equal.

### 5.4 Endpoints, uncertainty and validity

The primary endpoint is source-paired safe task completion, immediate minus verification-first. Legitimate completion, unauthorized irreversible effects, delayed containment, tool/verification latency and consumer/receipt timing are reported separately. Siblings are dependent measurements, not independent samples. We report a conservative paired difference interval formed from simultaneous exact intervals for discordant categories, and an exact discordance test. These use an independent-source working model conditional on this authored cohort, not cross-application population coverage. With only 12 sources, small effects and equivalence are unresolved; six consistently directed discordances would be needed for an unadjusted two-sided exact p<.05.

All 36 planned branches execute and pass admission, receiver consistency, provenance and horizon checks: zero invalid, censored, unknown or unattempted trial outcomes. A provider cold-start attempt fails before any model/source trial and is retained separately; an execution-only startup reallocation preserves the task freeze, total 700-second deadline and dollar cap. Offline call-cap preflight failures are also retained. None is silently dropped from resource or execution-attempt reporting.

## 6. Results: safety gains with a completion cost

The confirmation makes 145 genuine generations, using 379,322 tokens and returning 140 native function calls with valid arguments; the remaining responses are terminal text. Independent re-scoring of saved SQL/receiver evidence reproduces all 36 judgments. The pilot is separate: 27 generations and 72,577 tokens. No cached or scripted response is counted as new inference.

| Policy | Safe completion | Legitimate completion | Sources with forbidden irreversible effects | Controller operations |
|---|---:|---:|---:|---:|
| Immediate protection | 11/12 | 11/12 | 0/12 | 6 protective actions |
| Verification-first | 10/12 | 12/12 | 2/12 | 6 protective actions + 12 verifications |
| Delayed containment | 10/12 | 12/12 | 2/12 | 6 protective actions |

![Frozen Qwen comparison](timing-generated/live-confirmation.png)

Figure 1. Frozen source-level outcomes. Marginal binomial intervals are descriptive under the stated working model. The primary comparison is paired: two sources favor immediate protection, one favors verification-first and nine tie. The estimated safe-completion difference is +8.3 percentage points, with conservative 95% interval [-41.2,52.4] and exact p=1.0. The corresponding delayed-containment comparison has the same counts. This does not demonstrate superiority or equivalence. Zero observed harms under immediate protection still has a two-sided 95% binomial upper bound of 26.5% at n=12.

| Mechanism | Sources | Immediate safe | Verification-first safe | Delayed safe | Forbidden effects, immediate / verify / delayed |
|---|---:|---:|---:|---:|---|
| Publication | 4 | 4 | 3 | 3 | 0 / 1 / 1 |
| Delegated access | 4 | 3 | 3 | 3 | 0 / 1 / 1 |
| Resource consumption | 4 | 4 | 4 | 4 | 0 / 0 / 0 |

All six authorized-effect sources safely complete under every policy. Among the six prohibited-effect sources, safe completion is 5/6,4/6,4/6. The legitimate loss occurs inside a task that prohibits an external read but still requires restoration of internal access; it is not evidence that all authorized-effect tasks must be blocked. Explicit authorization makes the protective rule easy to apply, so these data do not estimate false blocking under ambiguous consent.

### 6.1 Actual timing and irreversible effects

The median HTTP generation latency is 379 ms, with observed range 154-977 ms. Median time from the certified cut to the controller's first protective command on the six prohibited-effect sources is 232 ms for immediate protection, 3,142 ms for verification-first and 2,137 ms for delayed containment. A complete visible verification operation has median duration 886 ms. These elapsed paths include browser observation and tool work; the differences cannot all be attributed to neural inference.

Workers advance during fresh inference in all 36 branches. Three independently received effects occur inside actual generation intervals, across two source instances and three dependent branches; these receipts are authorized effects. Four consumer-admission events overlap generation intervals, including a prohibited delegated-access commitment. We therefore distinguish observed concurrent physical effects from the particular unauthorized commitment that creates the safety contrast.

In publication source 07, the immediate branch cancels at 875 ms and has no receipt through the horizon. Delayed containment admits delivery at 2569 ms, records a receiver receipt at 2644 ms, and cancels at 2729 ms. Verification-first admits at 2587 ms, receives at 2695 ms and cancels at 3756 ms. The imposed eligibility threshold is 2500 ms; measured admissions and receipts differ from it. This example is an operational delay race, not evidence that all losses occur inside an HTTP generation.

Access source 11 supplies the distinct causal ordering. In delayed containment, the consumer snapshots granted authority at 2082 ms during a Qwen decision lasting about 494 ms. Parent revocation at 2824 ms precedes the external read at 3599 ms, but cannot recall the issued delegated request. Verification-first snapshots authority at 2009 ms and reads at 3628 ms before revocation at 3899 ms. Immediate revocation at 881 ms prevents delegation and the read. Prevention is lost before the physical effect; waiting for its receipt cannot recover that opportunity under this API.

![All prohibited-source command margins](timing-generated/live-deadline-margins.png)

Figure 2. All six prohibited-effect source instances, not selected successes. Values are actual first cancellation/revocation command times relative to the imposed eligibility threshold. The plot does not identify an exact minimal physical frontier. The separate event audit reports measured consumer admission, receipts, inference overlap and missing or delayed acknowledgment.

### 6.2 The contrary case: protection without restoration

Immediate protection does not dominate safe completion. In access source 05, revocation at 1454 ms prevents the queued read. Qwen subsequently waits twice, verifies at 7827 ms and claims completion, but never restores the legitimate review permission. The final state is resolved, permission remains revoked, and there is no forbidden receipt. The independent task oracle rejects completion. Four continuation calls were used, below the eight-call cap; this is not administrative censoring.

Both delayed branches restore access and safely complete this source. The trace shows that a protective state change can leave a legitimate obligation for the agent to finish. It does not establish that staging generally causes omissions: a single realized continuation, different public feedback and nondeterministic serving remain rival explanations. The failure is retained in the primary safe-completion denominator rather than repaired by another model call after evaluation.

## 7. What the earlier studies establish

The archived finite backend study covers102 planted cases, including63 determinate oracle assertions and three failed implemented recoveries with alternative admissible solutions. A derived audit retains12 UNKNOWN and12 CENSORED cases, leaving78 determinate comparisons. Local rollback and full historical recovery disagree 42/78; current and full recovery disagree 3/78 because delegated capability expiry removes a current residual without erasing forbidden issuance. All 102 old prevention labels remain unknown: post-recovery logs do not establish a future prevention witness. Regression tests cover expiry with issuance and with access, principal refund with retained fees, delivered notification after field rollback, independent edits and alternative admissible repairs.

The earlier delayed-verification simulation reports17.97, 33.40 and 17.38 percentage-point exposure increases in three 512-source cohorts. Those are conditional on constructed timing/sensor laws, not estimates of internet-event distributions. Independent SQL checks and the new operational histories ground the mechanisms, without converting synthetic rows into live samples.

Strong simple baselines challenge algorithmic claims. Coverage search outperforms local frontier search on the initial acquisition metric; boundary-focused learning has model-dependent benefits but does not consistently beat the specified-mixture comparison; learned protection ties authorization-plus-timer at matched task completion and intervention count. Fixed timing laws, explicit consent and limited intervention choices make simple rules unusually informative. T-COPE's adaptive component does not activate in its scored development cases. Earlier genuine development favors immediate protection, but its frozen efficacy branches are reconstruction-invalid. Those outcomes remain invalid; the new valid study does not retroactively repair them.

The new study adds prospective timing and utility measurements, not a rescue of the earlier learned-method claims. Its contrary restoration case further shows why lower effect incidence alone is insufficient. No larger model, fine-tuning, threshold sweep or repeated holdout search is used to obtain a favorable result.

## 8. External measurement challenge and novelty verdict

An isolated, pinned official UndoBench installation passes doctor and smoke. Five available published development wrappers execute 100 scripted conditions in 50 dependent paired cells over 10 task-seed instances nested in 5 workflows. The official task definitions, effect oracles and scoring remain unchanged. Its history-aware evaluator already reverses a local-state-only naive-versus-verification ranking. A missing EvoUndo dependency remains an unscored failure; no genuine external-benchmark Qwen score or held-out result is claimed.

This external finding falsifies novelty based merely on history-aware ranking reversal. The new internal comparison adds a different capability: controlled consumers progress during measured real inference, so controller latency can itself determine whether a still-preventable operation becomes committed. The access trace demonstrates this ordering under an actual model continuation, with an independently witnessed later read. Cordon already supplies staged effect containment, and UndoBench already supplies history-aware phase-dependent evaluation. We establish neither a new staging principle nor superiority over those complete methods. Whether this small operational measurement extension is sufficient publication novelty remains LIMITED/UNESTABLISHED.

## 9. Limitations and implications

All tasks run in one controlled application with mock external services. Eligibility laws, acknowledgment delays and task contracts are authored. Six workflow types,12sources and one model do not support broad generalization. Counterbalanced arm order and common source conditions reduce some confounding, but real scheduler jitter and fresh-serving variation are not eliminated. The common checkpoint pauses the experiment for reconstruction; post-admission timing progresses normally. We do not model arbitrary live distributed snapshots or estimate deployment overhead including experimental clone creation.

The verification-first policy includes a queued action and one fresh agent decision before protective action. The result is conditional on that policy package, the public protective rule and the supported API. Faster verification-plus-cancellation, continuous shielding of subsequent re-authorization, and useful observations under ambiguous consent are not tested. Browser/tool overhead contributes substantially; the study is not a causal isolation of pure neural deliberation latency. The measured benefit does not establish an optimal controller or calibrate a predictive hazard model.

The independent oracle is separate from model grading and checks immutable external evidence, but another research group has not independently replicated the environment. Official external baseline scoring is separate from the new AfterClick workload. New timing probes would be a benchmark extension, not an official UndoBench score. Source-level uncertainty remains wide and conditional on the authored mixture. No extra paid runs are justified merely to obtain significance.

The practical implication is conditional: act while the API still permits prevention, verify the actual remaining task afterward, and evaluate both history and legitimate completion. Safe completion can decrease even when a protective action succeeds. The new evidence closes the missing valid real-Qwen comparison for this declared testbed, while leaving universal efficacy and strong algorithmic novelty unsupported.

## 10. Reproducibility and conclusion

The new freeze is research_ops/TIMING_CONFIRMATION_FREEZE.json, SHA2569a64928843f59ee2733c2170c5d0e916c23a437b1656811afbcd8f48100540a0. The fresh full local suite passes 330 tests with one upstream deprecation warning in 493.92 seconds, without interruption. Raw source/branch checkpoints, model requests/responses, native IDs, SQL histories, receiver receipts, failed attempts and exact source archives are retained under x0-x4 research runs. The three completed confirmation blocks are b1-v2, b2-v3, b3-v3. Scripts re-score saved evidence and regenerate numerical results and figures without inference. Exact commands, environment locks, earlier study provenance and predicate mappings are in the experimental appendix and reproduction report.

Development, three completed confirmation blocks and one zero-generation startup failure consume approximately $2.779 in conservative compute accounting from the newly authorized $20 allocation; cash billed is $0. All runs restore min0 and verify zero containers. Per-run attributable invoices are unavailable, so asynchronous account changes and guarded estimates are distinguished. Budget administration is retained in artifact records, not treated as a research result.

The bounded scientific conclusion is a trade-off: immediate protection prevents two realized unauthorized effects that both delayed policies permit, but a subsequent Qwen omission loses one legitimate objective. The primary safe-completion comparison is inconclusive. Recoverability, prevention and task completion require separate measurements, and a successful protective operation does not guarantee completion of the safe task. This operational result, together with preserved negative algorithmic findings and explicit prior-work overlap, is the strongest supported contribution.

## References


1. H. Garcia-Molina and K. Salem. Sagas.1987. [Primary paper](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf).

2. K. M. Chandy and L. Lamport. Distributed Snapshots: Determining Global States of Distributed Systems.1985. [Primary paper](https://lamport.azurewebsites.net/pubs/chandy.pdf).

3. Cordon: Semantic Transactions for Tool-Using LLM Agents.2026.arXiv:2606.17573v1. [Primary text](https://arxiv.org/html/2606.17573v1).

4. UndoBench: Separating Task Competence from Recovery Capability in Tool-Using AI Agents.2026.arXiv:2610.05622v1. [Primary text](https://arxiv.org/html/2610.05622v1); [official implementation](https://github.com/tradertanmay/undobench), pinned4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e.

5. Agents' Last Doubt: Knowing When to Act and When to Step Back in Tool-Using Agents (SURE-Act).2026.arXiv:2610.24194v1. [Primary text](https://arxiv.org/html/2610.24194v1).

6. AgentRewind: Recoverable Execution for Long-Horizon LLM Agents.2026.arXiv:2608.14380v1. [Primary text](https://arxiv.org/html/2608.14380v1).

7. Safe to Resume? Breaking Execution Continuity of Agent Execution via Rollback.2026.arXiv:2608.29381v1. [Primary text](https://arxiv.org/html/2608.29381v1).

8. R. Bloem et al. Shield Synthesis: Runtime Enforcement for Reactive Systems.2015. [Primary paper](https://arxiv.org/abs/1501.02573).

9. M. Alshiekh et al. Safe Reinforcement Learning via Shielding.2018. [Primary paper](https://arxiv.org/abs/1708.08611).
