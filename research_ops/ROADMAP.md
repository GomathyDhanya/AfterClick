# AfterClick implementation roadmap — experiment-conditioned tasks

Status legend: PLANNED until fresh run artifacts prove a gate. Prior archived results are historical evidence, not proof a newly modified revision works.

## P0 — Verify starting state; repair evidence drift
**Why first:** `artifacts/adaptive-tests.log` records 122 tests passed; `docs/PROGRESS.md` certifies an earlier 88; both current archived live replay reports are invalid. No learning claims can rest on them.

Tasks:
- Read complete instructions; inspect `git status`, current HEAD, code vs archived manifest hashes. Build fresh baseline on real PostgreSQL and Chromium. Reproduce `bash scripts/check.sh`, `python -m afterclick.replay.demo`, and `python -m afterclick.evaluation.pilot`, adapting commands to the current environment; retain artifacts.
- Inspect `artifacts/adaptive-live/report.json`, `artifacts/adaptive-live-second/report.json`, per-call journals, and transport failure records. Determine whether failures stem from provider HTTP/timeout, JSON schema, token budget reservation, client timeouts, or state mismatch; do not invent root cause.
- Reconcile `docs/COMPLETION_GATES.md`, `docs/PROGRESS.md`, and `docs/ADAPTIVE_REPLAY.md` with current code and archive. Publish status for each gate: coded, test-passed, live-valid, comparative-evidence, or blocked.
- Pin deterministic baseline artifacts and reproduce the reported oracle and demo in fresh isolated schemas.

Output: `P0_EVIDENCE_AUDIT.md`, failure taxonomy, current implementation/evidence matrix, command transcript, next experiment.
Gate: all currently tested baseline checks pass (or failures are documented), report validity provenance is independently auditable, and scientific claims are aligned with evidence.

## P1 — Stable Modal actor + clean adapter
**Hypothesis:** a fixed `Qwen/Qwen3.5-9B` endpoint can supply syntactically valid, bounded browser decisions through the existing Gateway under a per-run spend cap.

Tasks:
- Following `MODAL_SETUP.md`, deploy a private dedicated Modal endpoint only after user approves cost ceiling; lock model ID, endpoint, tool schema, decode settings, and effective deployment parameters; keep `min-containers=0,max-containers=1`.
- Add an OpenAI-compatible `ModalPolicy` adapter next to the current `GeminiPolicy` without destroying Gemini historical replay. Implement budget/timeout accounting, one-call journal, provenance, strict schema parsing, and errors. Use `Decision` and `Gateway`, not arbitrary code execution. No automatic uncontrolled retries.
- Unit/mock tests: valid JSON, non-JSON output, truncated responses, unexpected actions, inconsistent usage, HTTP 429/5xx, transport uncertainty, cold start, budget exceeded, and no hidden fields in request. Disambiguate failed model request from failed browser action.
- Smoke 20 *non-side-effecting* decisions using known UI observations, measuring schema success, latency, average tokens, uncertainty, and spend. Test vision only in a separate ablation if text-only is insufficient. Observe exact model endpoint compatibility through `/v1/models`.

Output: adapter module, tests, a locked `model_config.json`, request journal, `P1_MODEL_SMOKE.md`.
Gate: at least 19/20 valid parseable decisions in the smoke set (pilot threshold; revise with justification if needed), no data leak, and cost instrumentation verified. If invalid, repair schema/tool protocol before expansion. A failed pilot is not silently re-run with a different model.

## P2 — Valid live counterfactual replay
**Hypothesis:** the live policy can complete legitimate goals, while execute/suppress and lost-ack branches remain reconstructable under fixed scheduler controls.

Tasks:
- Preserve all twelve branch families already described in `docs/ADAPTIVE_REPLAY.md`. Begin with a single workflow × seed × 12 branches. Scale to 3 workflows × 3 seeds only after first case is valid.
- Validate all checkpoints, six placebos, read-null outcomes, true server commit in lost-ack, and distinct fixed/adaptive continuation. Log mode, policy error, causal-validity certificate and legitimate goal separately.
- Retry provider transport errors only by restarting an entirely new case/run with a fresh run ID and full accounting; do not hide previous invalid run. Keep 12-branch replay as **planted intervention** evidence.
- Add concurrency during bounded deliberation only after deterministic pilot works; use explicit schedule interventions, not uncontrolled sleeps.

Output: `P2_REPLAY_VALIDITY.md`, nine-case pilot matrix, replay certificates, exact failure reasons, cost.
Gate: at least 9 fully valid 12-branch *live* cases across all three families for pilot progression; all observer-leak tests pass. Fewer valid cases requires fixing replay, not data generation. Nine cases are engineering evidence, not ML statistics.

## P3 — Diverse real effects and natural agent failures
**Hypothesis:** recovering a field differs measurably from preventing external disclosure, irreversible delivery, duplicate capture, and independent collaborator decisions.

Tasks:
- Add two new isolated, fake external systems at minimum: (i) webhook consumer with signed delivery/receipt and a pending-cancel boundary; (ii) export/publication sink with snapshot consumption or access by another actor. Optionally a mock payment authorize/capture/refund sink (refund is compensation, not erasure).
- Keep prior notification pathway. Explicitly identify what event is irreversible for each contract; distinguish reversible, compensatable, irreversibly observed, and unverified. Test that external sink receipts cannot be erased by changing internal state.
- Add assignment and comment/project changes as distinct *workflow types* only when they yield different dependency structures; count mechanisms separately from workflows.
- Generate user tasks that tempt but do not instruct an extraneous action. Run organic trajectories; compare the natural extra-action rate to planted-action studies. Record task success and organic failure occurrence as separate sampling properties.
- Add collaborators with non-overlapping and same-field changes; guard against ABA and same-value collisions.

Output: isolated mocks, contracts, oracle tests, causally verified mechanisms table, organic agent trajectory pilot.
Gate: >=3 truly distinct externally realized consequence mechanisms with independent evidence and planted known-positive/known-negative cases, plus nonzero naturally generated mistake cases **or** a documented strategy to enrich without pretending these are natural rates.

## P4 — Independent oracle and causal-label hardening
**Hypothesis:** recovery labels can be grounded without the recovery planner and without hidden future information leaking into predictors.

Tasks:
- Define explicit `event_time`, `right_censored`, `recovery_attempt_at`, `recovery_class`, `residual_forbidden_effects`, `preserved_legitimate_writes`, `causal_validity` in a versioned dataset schema.
- Hand-construct and property-test positives, nulls, late deliveries, conflicts, canceled jobs, duplicate calls, missing receipts, and alleged success with residual harm. Check contradictory receipts and censored runs.
- Compare planner output with independent oracle; oracle must not call planner result to decide correctness. Use exact state enumeration on bounded toy setups to sanity-check feasible recovery paths; declare any scope limits.
- Instrument actual data read/write dependencies if desired, separate from provenance correlation; absence of dynamic read sets must remain a labeled limitation.

Output: hardening tests, schema, negative/uncertain cases, oracle agreement/disagreement report.
Gate: no incorrectly certified `COMPLETE` recovery in planted adversarial tests; unknown/censored/conflicting outcomes remain distinguishable and auditable.

## P5 — Recovery-frontier discovery (the search paper candidate)
**Question C1:** Can targeted, diversity-preserving search discover a greater number of **distinct, verified** recovery-boundary mechanisms per equal evaluation cost than strong generic search baselines?

Tasks:
- Implement `afterclick/evolution/{genome,validator,random_search,coverage_search,genetic_search,map_elites,boundary_pairs,minimizer,archive}.py` only after P4 passes.
- Genome may alter legal delays, acknowledgement loss, retry policy, task workflow, collaborator interleaving, dispatch order, delivery latency, and bounded app state. Do NOT evolve arbitrary business-rule changes. Each proposal gets an immutable genome hash and validity record.
- Implement a recovery-frontier target: find near-minimal pairs varying the fewest allowed schedule dimensions while independently verifying recoverable vs irreversible or full vs partial recovery at a declared observation/recovery horizon.
- Establish equal-budget initial comparison: random, stratified/coverage search, standard genetic search, and MAP-Elites or targeted MAP-Elites. Pilot 50 expensive candidate evaluations per method per seed ×3 seeds, then set final budget from variance and cost. Count invalid proposals as evaluations in a separate failure accounting.
- Measure unique mechanisms (a prespecified taxonomy), verified boundary pairs/100 evaluations, archive coverage, minimal pair distance, wall-clock, and cost. Report duplicate rediscovery. A blinded held-out mechanism assessment should validate taxonomy.

Output: runnable algorithms, archive in JSONL, unique pair witnesses, Pareto/coverage graphs, `P5_C1_REPORT.md`.
Gate: C1 is supported only if equal-budget paired comparisons and uncertainty favor proposed search on genuine distinct boundary outcomes. If no advantage, retain negative result and proceed with random/coverage data for downstream study rather than falsely claiming search novelty.

## P6 — Leakage-free dataset and conditional temporal targets
**Question:** Can information available **before** an action predict its distribution of irreversible consequences across plausible future schedules?

Tasks:
- Construct `dataset_v1` with observable task, public UI, proposed action, declared metadata, action category, fixture family, model response, label-validated outcome. Hidden scheduler parameters, future worker/receipt state and oracle output are labels/analysis ONLY.
- Keep action-observation-identical schedule twins in the *same cluster*. Label them as repeated stochastic futures/conditional hazard estimates—not contradictory deterministic binary labels.
- Split by effect mechanism and workflow family, not row; group descendants, minimal variants, and near-duplicate prompts. Freeze 1 entirely unseen mechanism/family as a final holdout, 1 for validation, rest training. Avoid selection on holdout.
- Right-censor first external irreversible event at horizon. Model recovery feasibility at selected time separately; do not assume `recovery_class` monotonic or absorbing.
- Compare calibration to the empirical schedule-mixture frequencies; stress-test OOD and sensitive dependence on public task descriptions.

Output: dataset manifest and checksums; provenance lineage; zero-leak static checks; train/val/locked-test indices; class balance; audit of identical-visible-input twins.
Gate: no leakage, no pair crossing splits, no unverified labels, sufficient events and censoring to justify learning. If events sparse, redesign *training* sampling and maintain a naturally sampled test distribution separately.

## P7 — Small structured temporal risk predictor; conditional LLM training
**Question C2:** Does training on minimized boundary examples improve held-out calibrated risk compared with equal-cost random/coverage counterfactual examples?

Tasks:
- Implement baselines: prior-probability, static authorization/reversibility rules, logistic regression, XGBoost/CatBoost, discrete-time logistic hazard/survival model. Calibrate on validation only.
- Control for equal trajectories, input tokens and annotation/evaluator calls. Compare (A) ordinary trajectories, (B) random counterfactuals, (C) boundary pairs unminimized, (D) minimized boundary pairs, (E) boundary pairs + time-to-event supervision. Freeze preprocessing and family holdout.
- Evaluate integrated Brier score (if sampling supports it), time-specific Brier, AUROC/AUPRC, expected calibration error, false-negative rate at pre-specified intervention budget, CIs clustered by task/workflow, OOD degradation and uncertainty/abstention.
- Only if structured methods leave a meaningful gap, propose LoRA on an explicitly supported model and training provider. Do not treat deployed Qwen actor as automatically trainable on Modal; preflight support, GPU-cost cap and dataset licenses first. Obtain new explicit approval before any fine-tuning.

Output: model checkpoints, feature list, calibration plots, held-out analyses, `P7_C2_REPORT.md`.
Gate: C2 supported if pre-registered held-out improvement is positive with credible uncertainty and acceptable calibration. If C2 fails, pivot to systems/benchmark contribution; do not claim CRBL learning superiority.

## P8 — Enforceable runtime shield
**Question C3:** Does a learned risk-aware policy reduce **actual** external irreversible harm at a matched task-success or intervention budget?

Tasks:
- Implement `ALLOW / VERIFY / STAGE / REQUIRE_APPROVAL / BLOCK / COMPENSATE` only when effects are truly enforceable. A staged operation must persist in a queue whose release can actually be stopped. A fake sleep is not staging.
- Use public pre-action features and model risk only. Oracle stays in offline evaluation. Compare no protection, static authorization, block-all-irreversible, uniform human approval, learned prevention, learned prevention+selective compensation.
- Match intervention rate, human approval counts, or task-completion coverage before comparing harm. Test naturally generated actions separately from injected interventions. Add robust fail-closed behavior for unavailable predictor, unknown state, or explicit user override boundaries.

Output: shield code/test evidence, per-action audit, harm–success–latency–approval tradeoffs, `P8_C3_REPORT.md`.
Gate: actual verified harm reduction at an explicitly matched utility/intervention operating point. If task success collapses or safeguard only delays rather than prevents, C3 fails.

## P9 — Locked scientific evaluation and statistical analysis
Tasks:
- Before final collection, register hypotheses C1–C3, data splits, primary endpoints, power/variance-based sample sizes, random seeds, spent budget, tests, and multiple-comparison treatment. Re-run evaluation in clean isolated environment, retain raw artifacts.
- Provisional breadth target: >=6 workflow families × >=4 task templates each, multiple natural+planted seeds, at least 3 effect mechanisms. **NOT a claim of statistical adequacy**. Choose final sample sizes after pilot variance estimates.
- C1: equal costly search budget; C2: equal label/token/trajectory budgets; C3: matched utility and approval/intervention budget. Ablations: remove minimization, temporal labels, diversity archive, selective staging, compensation, and visible risk features.
- Report per-mechanism results and paired, cluster-aware bootstrap confidence intervals. Nonsignificance does not prove equivalence or noninferiority.

Output: preregistration frozen hash, complete experiment registry, raw/processed datasets, scripts, figures, statistical report, negative outcomes.
Gate: all figures are derived from registered manifests; all conclusions trace back to valid cases; no holdout tuning.

## P10 — Evidence-backed novelty claim / paper release
Tasks:
- Update a literature comparison with ReplayRCA (2026), Causal Agent Replay (2026), UndoBench (2026), AgentRewind (2026), UNDO/recovery runtime, T-MAP, MAP-Elites, and standard compensating transactions. State overlaps precisely.
- Use `NOVELTY_DECISION.md` to select the narrowest claim supported by C1–C3. Produce a research paper emphasizing measurable innovations, the algorithms' *technical difference*, not just integration.
- Provide code, artifact manifests, seeded regeneration commands, the model/version and cost ledger, independently verified witness datasets, experiment limits, errors, plus a demo video/plots if desired.

Gate: no novelty statement unsupported by a held-out or equal-budget comparison. If no positive method result, publish the reproducible negative result or the verified benchmark/tool (only if empirically valuable) rather than inventing a novelty claim.
