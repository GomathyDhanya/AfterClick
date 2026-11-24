# AfterClick: The Opportunity Cost of Executable Counterfactuals for Tool-Using LLM Agents

**Additive real-agent study. Development and locked confirmation are recorded separately. This draft is incomplete until the final result tables are populated. Earlier AfterClick papers and frozen outcomes remain unchanged.**

## Abstract

Executable counterfactual continuations can compare how an agent behaves after alternative interventions, but executing those continuations consumes time. In asynchronous environments, external jobs may cross a prevention frontier during that computation. We build an auditable Chromium/PostgreSQL testbed with real Qwen3.5-9B native-tool continuations, independent fake external receivers, permission tickets, resource accounting and concurrent edits. We distinguish exact causal reconstruction for evaluation from public-belief forecasts used online: the latter never receive the actual hidden schedule or oracle judgments. We compare static authorization, immediate protection, fixed live lookahead, a deadline-aware allocation heuristic and a real-delay placebo. A preliminary interface study improves safe completion from1/4 to4/4 on four paired development sources, but does not establish population performance. A diverse development baseline completes7/8 legitimate goals and5/8 safely. Final comparison results and uncertainty are pending below. We do not assume that executable lookahead or the proposed heuristic is novel or superior; the study is designed to expose when a simpler protective action already resolves the decision.

## 1. Introduction

Consider an agent asked to cancel a queued notice while updating a task and posting a comment. It may correctly update the text, reason about alternative continuations and eventually click Cancel. Those actions can all appear successful while an independent receiver has already observed the notice. A final application field saying canceled does not undo that history. Access systems create a subtler variant: a permission grant may be sampled into a capability ticket before the external read occurs. Revoking permission after the snapshot but before the read is already too late for that capability.

Counterfactual planning appears attractive because the controller could test whether blocking or substituting an action leaves a path to legitimate completion. However, the main world is not a paused simulator. Preparing an isolated forecast, invoking the model and executing its tools all take time. The controller must decide whether to gather that evidence, act immediately or preserve the option to reason later. The relevant trade-off is not only prediction accuracy; it is whether the decision can still be implemented when the forecast returns.

This paper studies that interaction with actual model continuations. It also tests a deliberately strong simple alternative: immediately exercise an explicitly authorized protective operation, then let the same agent continue its legitimate work. If that rule matches a more complex selector, the result limits the case for additional online reasoning rather than motivating a larger model or a parameter sweep.

The contribution is an execution and measurement study, conditional on the results. We provide distinct controlled causal mechanisms, native conversation checkpoints, independent historical-effect certificates and a separation between exact evaluation twins and online public-belief forecasts. We evaluate safety, legitimate completion, interventions and computation jointly. We make no claim that counterfactual branching, staging, value-of-computation reasoning or runtime shielding was invented here.

## 2. Background and closest related work

[Cordon](https://arxiv.org/html/2606.17573v1) already stages external effects and separates their release from local promotion. Our stage/verify policy is a small service-specific approximation, not a reproduction of its transaction runtime. [SURE-Act](https://arxiv.org/html/2610.24194v1) already executes candidate actions from cloned states followed by a frozen backbone. Branching and action-outcome comparisons are therefore foundations rather than our novelty. Its discussion of stochastic rollout labels also applies to our single sampled suffixes.

[UndoBench](https://arxiv.org/html/2610.05622v1) separates competence from recovery and evaluates both final state and effect history. Our resource uncertainty is explicitly an application completion-observation fault; it does not reproduce its wire-level lost-acknowledgment setup. [AgentBoundary](https://arxiv.org/html/2609.33658v1) jointly measures authorized completion and unsafe compliance. Our much smaller task suite cannot claim benchmark-scale coverage. [CASEL](https://arxiv.org/html/2610.36570v1) routes scrutiny by consequence and reversibility, with simulated intervention effectiveness. We instead execute the available interventions, but that empirical distinction alone does not establish a better allocation policy.

The general cost of deliberation is longstanding. [Zilberstein and Russell](https://people.eecs.berkeley.edu/~russell/papers/aij-anytime.pdf) study time-dependent utility and computation allocation in real-time systems; [Russell and Wefald](https://doi.org/10.1016/0004-3702(91)90015-C) motivate valuing computations through their effect on external decisions. Runtime [shield synthesis](https://arxiv.org/abs/1501.02573) and [safe RL shielding](https://arxiv.org/abs/1708.08611) already mediate unsafe actions. Our heuristic has no corresponding formal guarantee. Schedule exploration and compensating transactions likewise predate this work. The finite related-work audit is recorded in research_ops/LITERATURE_MATRIX.md; it does not prove a priority or absence claim.

## 3. Problem, assumptions and targets

A source execution contains application state X, pending exogenous work J, immutable external history H, browser-visible observation O, model conversation M and pending native-call identifiers P. The evaluator checkpoints K=(X,J,H,O,M,P,a) at an actual model proposal a. A causal sibling initializes a fresh isolated world from K and applies an intervention before obtaining new model continuations. This is experimental reconstruction, not restoration as a live recovery operation.

For a declared protective operation, let F be the actual ticket/dispatch transition after which it can no longer prevent the relevant historical effect, E the receipt time and A the time evidence becomes publicly available. The scheduled eligibility threshold D is distinct from F: worker scheduling can delay the actual transition. Plots show D as a reference and mark actual transition/receipt events separately. The access workload permits F<E<A. Recoverability is relative to the implemented operators, authority and finite execution horizon. A failed recovery implementation does not establish universal physical impossibility. Compensation and cancellation state cannot erase an already committed external observation.

Safe completion S requires independently verified legitimate goals, preservation of unrelated authorized state and absence of forbidden irreversible effects within the declared observation horizon. We report these components separately. A task can achieve its requested final fields while S=0 because an unauthorized receipt exists. Unresolved future effects are right-censored; invalid reconstruction or inconsistent observers are invalid, not safe or unsafe labels.

A standard partial-observability limitation follows immediately. Two hidden schedules can produce the same decision-time O but different recoverability. Any deterministic function of O then returns the same prediction in both worlds and must err on at least one. Under a two-state observation-equivalent mixture with probability p, the best classification error is min(p,1-p), and the Bayes Brier uncertainty is p(1-p). This is an elementary identifiability argument, not a new theorem. A local service test constructs such a pair with identical public telemetry but different receiver histories.

The online controller receives only natural instructions, allowed visible state, the proposed action, observed latency history and remaining computation budget. Neither it nor its forecasts receive the realized hidden schedule, private task predicate, future job list, source partition or oracle outcome. Exact twins remain available only to the evaluator. Public-belief forecast worlds are sampled independently from a published prior and initialized from public fields; they are not exact predictors of the actual future.

## 4. Execution system and independent environment

The preserved FlowBoard application supports autosaved Description and dropdown edits, explicit comment posting, review state, versioned collaboration and asynchronous automation. The new service panel exposes only real supported browser buttons. Models call native tools with tools/tool_choice:auto; arguments and tool-call IDs are validated and results use matching tool_call_id. Structured JSON remains a historical baseline, never mixed with native tools in these arms. No new reasoning parameter or deployment is introduced. The existing thinking-disabled configuration, model revision and endpoint metadata are frozen per run.

Observable feedback distinguishes a local comment draft, a posted comment, autosaved fields and an agent's own completion claim. A global Committed indicator certifies task-field transport state, not all requested work. Substitutions report requested and performed actions and whether the requested action executed. The model receives no private success correction after claiming completion. Provenance distinguishes organic model choices, recorded prefix calls, imposed controller actions, mock-provider fixtures and deterministic environment events.

The four workload families have different causal behavior. Publication supports cancellation before dispatch. Permission snapshots a ticket that survives later revocation. Mock resource capture conserves an independent3-unit account, with idempotent same-nonce retry and separate new intents. Collaboration changes legitimate fields or text concurrently and tests whether the agent preserves them. Every receiver is isolated loopback HTTP and records immutable SQL evidence. No real messages, permissions, customer records, resource purchases or payments occur.

A monotonic worker advances every approximately20ms while model inference and forecast construction proceed. Polling and verification expose delayed, possibly stale evidence. The actor-visible cache is checkpointed without freezing the underlying worker. Exact branch reconstruction checks the full public observation, copied world, browser draft/cache, native conversation and pending IDs before resuming its own clock. New serial sequences and self-referential job ordering are initialized only in fresh ac_* schemas. A one-second finite post-agent observation suffix preserves right censoring rather than fabricating future receipts.

## 5. Controllers and executable forecasts

All primary policies share the same model, Gateway menu, maximum10 new requests including forecasts, maximum4 interventions, maximum12 turns and per-run global caps. Unused budget is not spent on dummy baseline requests. The base policy is unchanged within each comparison.

Static authorization checks explicit natural-language scope and visible prerequisites. The stage/verify baseline immediately cancels prohibited queued effects or temporarily revokes access when authorized, then continues the model. It also preserves visible collaborator text through an ordinary supported fill substitution. The baseline has the same option-preserving capabilities as the proposed method.

Time-blind lookahead executes up to two candidate belief-world continuations before protection. Fixed-budget lookahead performs the same work after immediate protection. Each candidate has at most two new model turns, so these are explicitly partial-horizon forecasts. The original worker advances during construction, inference and tool execution. A public summary is released before private oracle grading and teardown; those evaluation-only operations do not supply online selection information.

T-COPE is a transparent initial heuristic. It protects first and skips lookahead when explicit scope already resolves the decision. For a remaining uncertain consequential proposal, it allows one forecast only if a conservative public opportunity estimate exceeds expected rollout time and at least four requests remain. Its initial opportunity estimate is max(0,4500ms−visible age); expected rollout time is twice max(1000ms, observed latency history), plus1500ms overhead. It is neither a calibrated hazard model nor an optimal metareasoning policy. Forecast ranking is lexicographic in fewer publicly observed disallowed effects and greater visible task progress. Independent task grades are withheld.

A real-delay placebo waits for a development-frozen duration before protection without invoking forecasts. It separates the cost of waiting from the value of new continuation information. An offline best-observed-arm envelope reports whether any tested arm achieved safe completion on a source; it is not a deployable perfect oracle or a bound on expected optimal performance.

## 6. Experimental design

The historical4B pilot remains4/12 and is not retuned. The new feedback study uses four new paired sources with the same9B model and equal turn limits, comparing legacy and corrected interfaces. A separate five-condition live replay test verifies no-op, original, suppressed, read-substituted and delayed continuations. These engineering studies do not establish controller superiority.

Eight development sources span four families, including authorized consequential work and prohibited queued effects. Their pending jobs, observation faults and collaborator edits are controlled disturbances; we do not estimate deployed organic error prevalence from them. Three development controller cases cover publication, access and resource frontiers. Every declared case is retained regardless of baseline outcome.

Eight new confirmation source contracts were locked before method selection. They use different source identities and natural content with shifted timing parameters, but the same four mechanisms. They are not an unseen-mechanism test. Controller/model/analysis settings and the placebo duration must be frozen before confirmation outcomes are opened. All siblings and derived forecasts remain with their source cluster.

Primary outcomes are safe completion and independently verified unauthorized historical effects, reported jointly with legitimate completion. We retain attempted, valid, invalid, censored, unknown and unattempted counts. Paired exact tests and source-cluster descriptive bootstrap intervals are supplemented by per-arm Wilson intervals. Holm correction applies to three declared primary contrasts; a placebo contrast is secondary. Degenerate all-tied bootstrap intervals do not demonstrate equivalence. One stochastic suffix per arm/source and only eight confirmation sources limit power and population inference. Temperature zero is not a determinism guarantee.

## 7. Results

### 7.1 Interface and baseline evidence

The same9B feedback comparison achieves4/4 safe completions with corrected semantics and1/4 with legacy semantics, using33 genuine generations. Three discordant pairs give two-sided exact p=.25; this is suggestive engineering evidence, not a population guarantee. The combined changes include prompt/tool semantics and context handling, so the result does not isolate one phrase or prove a model-size effect.

Five reconstructed live branches produce six new model generations. A read substitution with ambiguous v2 feedback causes a false completion; suppression produces actual replanning. One evidence-based v3 requested/performed/deferred correction subsequently passes the same feedback case in two calls. The original negative trace remains immutable.

The diverse baseline has8/8 valid executions,7/8 legitimate completions and5/8 safe completions, using40 primary generations plus two separately scored interface-retest calls. Resource cancellation arrives at6603ms after a5500ms frontier, leaving a receipt and a2-unit balance. The access trajectory never revokes before a4500ms ticket; later verification/grant does not prevent the read. A collaboration task overwrites a note using stale content. Authorized publication and capture succeed. No duplicate resource capture is observed; we do not infer an unobserved recovery cascade.

### 7.2 Development controller comparison

Pending completed development aggregate. One repaired time-blind publication branch already completes the requested goals but retains a forbidden receipt, whereas immediate protection on the same checkpoint avoids it. The first attempt of that condition was invalid due to a transport-settling defect and is reported separately. It cannot be silently replaced or counted as an efficacy failure.

### 7.3 Locked confirmation

Pending fixed independent execution. No confirmation outcomes were used to write the method above.

## 8. Timing, ablations and failure analysis

A forecast's wall cost includes isolated-world construction, browser/tool operations and model inference. It must not be reported as model latency alone. The development forecasts can consume much more wall time than their raw HTTP inference latency. We measure the full delay while the primary world advances, then use the frozen delay-only condition to test whether that cost explains missed frontiers. The fixed-budget-after-protection arm isolates whether staging can absorb that delay.

Two execution defects are preserved. Lexical insertion of scheduled jobs violated a self-parent foreign key; fresh-schema copying now orders parents before children. A protective action committed while its public HTTP acknowledgment remained pending beyond the old650ms barrier; a bounded public acknowledgment wait fixes the false abort. A shared-journal snapshot also labeled a completed forecast unknown while a different conversation was in flight. Per-conversation request-ID accounting separates those states; the original global audit shows all41 requests in that batch had known outcomes. These are system defects, not model planning errors.

## 9. Limitations and scientific verdict

The environment uses synthetic controlled services and short tasks in one application. Real LLM continuation does not make these real-world deployments. Timing mixtures are finite, public scope is often explicit, and simple intervention rules may already be close to optimal. The forecast prior is approximate, its progress score is not a calibrated value function, and two-turn suffixes may miss later effects. Exact causal twins have privileged evaluator state; only their public-belief counterpart is deployable. Our implementation's cloning overhead can dominate model latency and may differ substantially from an optimized runtime.

The new confirmation separates source instances and schedule parameters, not unseen mechanisms. Its sample is small and related templates remain correlated. One suffix per arm does not estimate expected policy utility precisely. A best observed arm is optimistic. Finite observation horizons retain unknown futures. Safe task completion does not imply the absence of all imaginable harm outside the declared fake-effect contract.

No new learned predictor or fine-tuning is justified by this small, explicit-scope problem. Earlier search/learning/shield findings remain mixed or negative. If the staged baseline matches T-COPE, the correct conclusion is that extra executable lookahead has no demonstrated incremental safety value here. The literature already establishes the conceptual ingredients. Final novelty verdict remains pending empirical confirmation and may be a bounded systems characterization rather than an algorithmic advance.

## 10. Reproducibility and safe operation

All runs preregister exact commands, source hashes, model/revision, decoding, request/token/concurrency limits, resource price envelope and finite stopping rules. Raw requests, model outputs, native tool IDs, observations, checkpoints, actual intervention actions and independent certificates are retained, including failed and canceled attempts. Runs are sealed after analysis. No secrets are stored. Local checks require real PostgreSQL and Chromium in isolated ac_* schemas. No paid call is part of evidence-only reproduction.

The existing compute-billed endpoint is used under the original standing project ceiling, category budgets, a protected credit reserve, provider usage/cash limits and finite scale-down watchdogs. Every paid batch verifies min0 restoration and idle containers. Approximate account billing and conservative cost guards are distinguished from unavailable isolated invoices. The reproduction appendix and final quantitative tables will be generated from saved evidence before completion.
