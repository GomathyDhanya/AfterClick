# Mandatory experiment and evidence protocol

## A. Research log paths

All paths relative to the AfterClick repository root. Create them if absent:

```
research_ops/
  PROGRESS.md                  # append-only dated development log
  DECISIONS.md                 # each decision, evidence, alternative, reversal condition
  CLAIM_REGISTER.md            # C1/C2/C3 status: proposed / tested / supported / refuted
  LITERATURE_MATRIX.md         # cited primary sources and precise overlaps/differences
  EXPERIMENT_REGISTRY.jsonl    # one immutable record per planned and completed trial batch
  ISSUES.md                    # failures, severity, owner, fix/test evidence
  NEXT_EXPERIMENT.md           # adaptive next experiment after each batch
artifacts/research_runs/<run_uuid>/
  manifest.json                # git hash, source diff hash, model ID, API base host (no token)
  protocol.json                # hypotheses, settings, seeds, budget, stop rule
  trials.jsonl                 # each executed/invalid/unknown case, one row
  model_calls.jsonl            # parsed/redacted requests, responses, tokens, cost
  oracle_certificates.jsonl    # independent references, verified classifications
  metrics.json                 # summary + per-stratum metrics and denominator
  analysis.md                  # interpretation, uncertainty, confounds
  next_experiment.md           # result-conditioned action
  raw/                         # replay branches, errors, worker logs, receipts
  figures/                     # plot source hash + PNG/SVG
```

Keep machine-readable artifacts append-only or immutable after finalization; do not rewrite failed historical runs. During active runs, flush lines immediately. If the program crashes, emit a failure record with last known state; never delete an interrupted batch.

## B. Canonical manifest fields

Record `schema_version`, `run_id`, `utc_created`, `git_commit`, `git_dirty`, `diff_sha256`, `source_manifest_sha256`, `lockfile_sha256`, `host_platform`, `python_version`, `node_version`, `postgres_version`, `chromium_version`, `contract_ids_and_hashes`, `scheduler_config`, `seed`, `policy_name`, `policy_model`, `model_version_or_revision`, `endpoint_name`, `model_config`, `prompt_sha256`, `parser_sha256`, `backend_version`, `timeout_policy`, `budget_usd`, `priced_resource_seconds`, `recorded_gpu_cost_usd`, `input_tokens`, `output_tokens`, `journal_file_sha256`, and `oracle_schema_version`. Missing values must be explicit `null`, not invented.

## C. Canonical trial fields

At least: `run_id`, `case_id`, `scenario_family`, `effect_mechanism`, `template_id`, `seed`, `observation_hash`, `action_hash`, `schedule_genome_hash`, `branch`, `replay_valid`, `invalid_reasons`, `selected_action_planted`, `organic_action`, `goal_succeeded`, `authorized`, `forbidden_effect_occurred`, `first_irreversible_elapsed_ms`, `event_time_right_censored`, `horizon_ms`, `recovery_attempt_elapsed_ms`, `recovery_class`, `verified_residual_effects`, `collaborator_edits_preserved`, `oracle_reference_hash`, `model_calls`, `input_tokens`, `output_tokens`, `billed_or_estimated_usd`, `execution_wall_ms`, `errors`.

NEVER treat `event_time_right_censored=true` as proof of no future irreversible event. NEVER assign `irreversible=true` because the planner does not know a compensation routine.

## D. Registration before execution

For each experiment, record:
- Exact falsifiable claim and strongest opposing explanation.
- Primary metric and estimand. E.g. C1 unique verified boundary mechanism per 100 *attempted* candidate evaluations; C2 held-out integrated Brier score; C3 forbidden-effect probability among authorized legitimate task distributions at matched intervention budget.
- Candidate and baseline algorithms, hyperparameter search policy, model/prompt versions.
- Units of randomization and evaluation; causal pairing/control/placebo; legal schedule perturbations.
- Censoring/invalid policy and full denominator. Exclude invalids from causal effect estimates but report their frequencies and causes per method; do not select only successful trials without describing selection bias.
- Workflow-family/mechanism split, descendant clustering, held-out sealed set, evaluation horizon, number of seeds and provisional/final power justification.
- Cost caps: expected, maximum, wall/GPU/token/candidate counts. Abort before invoking resources above cap.
- Decision rule for improvement, stopping, retraining, pivot; no posthoc unacknowledged threshold changes.

## E. Analysis rules

- Present raw event rate and independent verification, not only classification accuracy. Show number attempted, valid, invalid, censored, unknown, and naturally arising harm cases separately.
- Aggregate by task family, mechanism, agent seed and schedule seed. Use paired cluster bootstrap with bootstrap unit no finer than independent task/workflow unit; report confidence intervals and no hand-waving significance.
- Report **safety–utility** curves, calibration and abstention/intervention curves. Measure end-to-end realized harm, not predicted labels alone.
- For budget comparisons count *all* candidate evaluations including failed candidates, as well as expensive valid evaluations; give both views clearly.
- Search success can be gamed by repeatedly finding nearly identical notification boundaries. Deduplicate via a preregistered mechanism taxonomy and causal witness equivalence.
- Create negative controls by perturbing irrelevant read actions, source snapshots, and independent collaborator edits. If they appear causal, halt and audit replay.
- Existing scripted receipt is one mechanism across three current workflow families; do not claim otherwise.
- For survival label first irreversible arrival, it is absorbing by definition. Recoverability-at-time is a separate target that can change with intervening edits.
- Avoid reporting model precision as if certainty about a hidden future could exist. When visible inputs are identical, estimate risk under the chosen future-schedule distribution; evaluate distribution shift across different schedule mixtures.

## F. Result-conditioned branching

1. **Replay fails:** Fix transport/parser/reconstruction; do not train. Preserve invalid pilot.
2. **Only one mechanism exists:** Build independent consequence mechanisms; do not count more task forms as generalization.
3. **Search C1 fails:** Keep a strong random/coverage baseline; focus on temporal benchmark/oracle or revise the lawful schedule parameterization. Do not claim evolutionary novelty.
4. **Predictor C2 fails:** Determine whether observability or label noise is limiting, and whether any text/nontext features actually help; report negative finding and pivot.
5. **Shield C3 fails:** Investigate wrong intervention points, unenforceable `STAGE`, cost/success trade-off, calibration drift; do not claim deployment safety.
6. **All positive:** Freeze final method and evaluation; audit literature again and write paper claims bounded by the observed environments.

## G. End-of-experiment analysis template

```
Run ID / Git SHA / Mode / Model / Cost:
Hypothesis and outcome:
Predeclared primary metric / baseline / proposed:
Valid / invalid / unknown / censored denominators:
Effect size and uncertainty:
By-mechanism and OOD breakdown:
Causal validity (placebos, nulls, independent oracle):
Failure examples and confounds:
Does the original hypothesis survive? Why?
Next experiment (ONE), expected discriminating evidence, stopping rule:
Budget estimate and permissions required:
```
