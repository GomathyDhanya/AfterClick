# AfterClick — Implementation and Research Completion Roadmap

**Basis:** `684_final(1).zip`, `docs/PROGRESS.md`, `docs/ARCHITECTURE.md`, `docs/EXPERIMENTS.md`, and `AfterClick_Independent_Audit.md` (17 November 2026).  
**Current milestone:** One controlled seven-branch scripted FlowBoard demonstration; 39 tests reported passing in repository logs, not independently re-executed in the audit environment.  
**Target:** Validated causal audit, evolutionary minimal-boundary discovery, a learned recovery-risk critic, an integrated safety shield, and comparative research results.  
**Scope constraint:** Preserve existing React/PostgreSQL/FastAPI/Playwright architecture; no rebuild. Do not spend Tinker credits without explicit authorization.

## Definition of done

AfterClick is complete as a research prototype only when: (1) replay and recovery oracles pass adversarial validity tests across multiple independent workflows; (2) adaptive LLM agent trajectories are collected and counterfactually replayed; (3) a constrained evolutionary search discovers verified boundary pairs more efficiently than search baselines or results are honestly reported as negative; (4) a leak-free recovery-risk dataset and structured prediction baseline exist; (5) boundary-trained critic is compared at matched budgets with success/failure and random-counterfactual training; (6) integrated shield is evaluated on unseen workflows with task success, irreversible-effect harm, collateral preservation, false recovery claims, cost, and statistical uncertainty; (7) all graphs and paper figures are generated from immutable experiment results.

The proposed novelty is **minimal recovery-boundary supervision and its effect on out-of-distribution prediction and actual protection**, not invention of genetic algorithms, counterfactual replay, action necessity, or rollback.

## Gate 0 — Reproducibility and audit hygiene (Week 1, parallel with Gate 1)

- Create clean Git commit and release tag; freeze current fixture run and hashes as baseline. Preserve the seven-branch demo as `v0` evidence.
- Run the actual command sequence from `docs/REPRODUCIBILITY.md` on a Docker-enabled development/CI machine: `docker compose up -d --wait db`; `uv sync --frozen`; `npm ci --prefix apps/flowboard-web`; `npm run build --prefix apps/flowboard-web`; `uv run playwright install chromium`; `bash scripts/check.sh`; `bash scripts/demo.sh`.
- Capture exact environment metadata and CI evidence; record failed runs, not just successes.
- Exclude `.venv`, `.bootstrap`, `node_modules`, caches, machine-specific material, credentials and `.git` history from distributable source archive. Keep minimal source and separate evidence bundles.
- Run `npm audit` and Python dependency audit; assess known dev-tool advisories and pin images by digest. Do not claim production security.
- Add `docs/NOVELTY_MATRIX.md`, `docs/THREAT_MODEL.md`, `docs/PREREGISTRATION.md`, `docs/COMPLETION_GATES.md`.

**Pass:** clean source clone, successful tests and v0 demo on supported machine; exact revision in run manifest; no hardcoded local paths or secrets; archival raw results retained.

## Gate 1 — Eliminate known validity defects (Week 1)

**A. Replay certificate** — `afterclick/replay/demo.py::validity_certificate`: include `conflict` in pre-action checkpoint-equivalence checks, while allowing its deliberate *post-checkpoint* collaborator intervention. Add a negative test that mutates the conflict branch's pre-action fixture and requires `valid=False`. Check all seven branches in the demo certificate.

**B. Same-value concurrent edit** — `apps/flowboard-web/src/main.tsx::save` 409 handling: value equality is insufficient to infer no intervening write. Add server-exposed *non-identifying* field revision tokens, incremented even for same-value independently committed writes; require conditional compare-and-swap (CAS) for rebases. Keep backend field ownership authoritative. Add two-browser tests where collaborator writes the base value with new ownership, and ensure the pending agent draft is preserved with visible conflict.

**C. Reliability regressions** — test duplicate `operation_id` with same/different payload; lost ACK followed by retry; pending autosave at navigation; SSE reconnect and monotone versions; outstanding requests produce `UNKNOWN`, not `VERIFIED`.

**Pass:** all previously passing tests plus new negative tests; baseline demo still reproduces; intentionally corrupted checkpoint fails closed; no silent overwrites.

## Gate 2 — General contracts and truly independent effect/recovery oracles (Weeks 2–3)

Implement a task-contract schema with explicit: seeded initial state, goal predicates, allowed effects, forbidden historical effects, preservation constraints, evaluation horizon, supported compensations, and actor roles. No hardcoded `TASK-42` logic in the generic oracle.

Expand to at least 4 independent workflow *families* for the development program, then target 6+ for final transfer studies:
1. Description / review / dependent readiness (existing).
2. Priority / escalation / internal notification.
3. Assignment / ownership / collaborator reactions.
4. Status / project summary / prerequisite dependency.
5. Comments and activity records (secondary).
6. Multi-task edits and overlapping concurrent updates (secondary).

For each family, create intentionally known positive, null, conflicting, historical-irreversible, and unknown/censored fixtures. Write expected outcomes separately from planner implementation. Introduce semantically distinct event IDs, record/field revisions and authorized-effect predicates.

Define **two target variables**: (i) *historical irreversible effect arrival*, which is absorbing within the declared capability model and supports survival prediction; (ii) *current safe recovery deficit/class*, which may be non-monotone and needs time-indexed state/cost prediction. Never collapse planner timeout or conflict to proven irreversibility.

**Pass:** independent oracle detects planted mutations and injected false recovery claims across each family, including `UNKNOWN` and `CENSORED`. No oracle imports the recovery planner or model. Test fixtures are versioned.

## Gate 3 — Causal differences and adaptive agent continuation (Weeks 3–5)

- Preserve existing bounded `Gateway` and quiescent-prefix reconstruction.
- Add a browser-agent adapter with one fixed API-hosted LLM, bounded Playwright tool schema, fixed prompts, stable run manifests, token/cost metrics, and no backend/oracle access. Run scripted and LLM policies in separate modes.
- Support two counterfactual continuations: (A) original-action/fixed scripted sequence where semantically valid; (B) suppress-and-let-LLM-replan. Do not assume the same action index retains semantics after earlier interventions.
- Compare branches by semantic resource/field events plus state oracles, not solely shared `action_id`. Maintain typed edges: provenance, happens-before, data dependency, intervention-supported causal evidence.
- Run placebo and null-action controls on every family. Revalidate snapshots before each branch; retain invalid branches and denominators. Keep separate browser clock and backend logical scheduler.
- Add an explicit `FeedbackIntervention` (committed-success vs lost ACK) for selected writes. Do not attempt arbitrary JS heap snapshots in MVP; reconstruct from a reproducible prefix.
- For independent collaborators use identical external schedules; for reactive collaborators explicitly model different downstream decisions as part of causal mediation.

**Pass:** at least 3 workflow families, multiple seeds, matched placebo replays, valid semantic branch comparisons, successful adaptive replanning, measured LLM API consumption, zero oracle leakage. No final necessity claim without paired uncertainty analysis.

## Gate 4 — Recovery baselines and verification (Weeks 4–6)

Extend compensation primitives for review/readiness, priority/escalations, assignment/notifications, status/summary, and pending jobs. Preserve immutable history and independent edits. Require atomic version/field-revision predicates. Build baseline methods: no recovery; LLM undo (optional); snapshot-restoration *offline comparison only*; simple reverse operation; provenance/dependency-based conditional compensation; and counterfactual-informed constrained recovery.

Use a small exact enumerative oracle on bounded fixtures as a reference. In larger instances a planner timeout maps to `UNKNOWN` and does not prove `UNRECOVERABLE`. Log compensation feasibility, conflicts, delivered notifications, and unresolved pending requests. Never use snapshot restore as a live action in collaborative workspace.

**Pass:** no legitimate-edit destruction on planted independent/same-field conflicts; false `VERIFIED_RECOVERABLE` count zero across planted oracle tests; all known external deliveries represented as historical irreversibles; correct partial/unknown outcomes.

## Gate 5 — Search algorithm and verified boundary archive (Weeks 6–8)

Construct constrained `ScenarioGenome`: autosave delay, worker delay, ACK loss/delay, SSE delay, collaborator timing/policy, retry policy, schedule seed. Validate causal event ordering and fixed application rules before execution. Search must not invent impossible event histories or change workflow business logic silently.

Implement equal-budget discovery baselines: uniform random; coverage-guided; standard genetic algorithm; standard MAP-Elites; boundary-targeted MAP-Elites; boundary-targeted MAP-Elites + bounded delta minimization.

A pair is admitted only if: same task and proposed action; independently validated pre-action state (except declared intervention); comparable horizon; valid replays; verified recovery contrast; task outcome equivalence where required; and known observability class. Minimize only as a *local minimum* under declared edit operators unless exhaustive search proves global minimality. Record all rejected candidates and search cost.

Use a cheap deterministic simulator/replay screening stage, then recheck promising pairs with real browser and adaptive LLM continuations. Prefer MAP-Elites archive axes based on mechanism, affected subsystem class, recovery-horizon bucket, and cascade topology. Do not use harms as the only diversity axis.

**Pass:** reproducible archive with verified boundary pairs across >=3 mechanisms, search learning curves, equal-budget baseline results, minimization witnesses, and complete provenance. If no advantage over random, report negative result and reconsider novelty; do not manufacture a difference.

## Gate 6 — Leak-proof dataset and structured ML baseline (Weeks 8–9)

Create training records with `task_family`, `workflow_family`, `fixture`, `run_id`, `branch_id`, `checkpoint_id`, `observation_hash`, `proposed_action`, `trusted_visible_metadata`, `unobservable_schedule_id` (held outside model inputs), `necessity_estimate`, `unauthorized_effects`, `historical_irreversible_event_time`, `recovery_deficit(t)`, `oracle_label`, `label_certainty`, `censoring_status`, and `pair_type` (`observable` / `latent`).

Split by full workflow family before generation/selection to avoid variant leakage; all descendants of a task and both sides of boundary pairs remain in the same split. Include at least one unseen automation family in evaluation. Do not place future event traces or hidden worker schedules in inputs.

Train CatBoost/XGBoost tabular classifiers and a discrete-time hazard/survival baseline with proper right censoring; risk scores should be calibrated. Latent pairs with identical visible inputs supply probabilistic risk, not contradictory deterministic ranking loss.

**Pass:** executable leakage validator, datacard and negative/censored statistics; trained structured baseline with time-dependent AUROC/Brier, calibration, risk–coverage; held-out split reported separately.

## Gate 7 — Tinker model and contrastive ablations (Weeks 9–10)

Only proceed if Gate 6 has enough diverse, verified, learnable examples. Check current Tinker API support and model catalog at execution time. Prepare SFT representation and a tiny smoke experiment, document sample-token costs, and **obtain explicit user permission before spending any credit** (`AGENTS.md`). Do not assume Tinker supports custom pairwise/survival losses without verification. Use SFT for discrete risk/time labels first; test custom ranking only where supported.

At equal sample and compute budgets, compare: prompted critic; structured baseline; LM trained on ordinary success/failure; LM trained on random counterfactuals; LM trained on boundary pairs without time labels; full boundary/time-labeled critic. Calibrate probabilities post hoc on validation, not test. Run >=3 training seeds if budget permits, or report exploratory status.

**Pass:** reproducible checkpoints and costs; clean held-out prediction comparison; OOD transfer analysis; uncertainty/censoring correctness; meaningful ablation result or honest null result.

## Gate 8 — Integrated Recovery Shield (Weeks 10–11)

Implement `ALLOW`, `INSPECT`, `SKIP_AND_REPLAN`, `REQUEST_APPROVAL`, and `STAGE` only where a server-enforced staging boundary exists. Use existing task scope as deterministic front-line authorization; learned risk is advisory for marginal calls. Maintain per-action pending-effect monitoring, cancellation for not-yet-dispatched jobs, and graph-informed compensation if harm occurs.

Evaluate preventive shield only on pre-action observable inputs. Do not run an offline counterfactual on the live production site or invent a staging guarantee on arbitrary websites. The integrated defense should optionally abstain on high uncertainty.

**Pass:** end-to-end LLM task continuation; the shield reduces harmful effects on verified held-out scenarios at matched completion/intervention budgets; no forbidden state or hidden oracle reaches policy; zero false complete-recovery certificates in planted tests.

## Gate 9 — Comparative experiments and statistical validation (Weeks 11–13)

Preregister before final runs: primary hypotheses (search discovery, model risk prediction, end-to-end harm reduction), practical goal noninferiority margin, family-level splits, fixed scenarios/seeds, budget limits, exclusion of replay failures, confidence intervals, and multiple-test correction.

Recommended pilot 12 tasks / 3 seeds, then expand toward 24–36 task templates across >=6 workflows; choose final N through measured variance and power. Use deterministic screening to limit expensive LLM continuations. Compare at equal expensive evaluation count for search, equal examples/tokens for learning, and matched task-success and action-intervention budgets for shield.

Primary search: verified distinct mechanisms per 100 expensive evaluations; archive coverage; minimal-pair distance; wall clock; failures. Primary ML: OOD time-dependent AUROC, integrated Brier, calibration, risk–coverage. Primary defense: unauthorized residual and historical effects, goal success, legitimate-edit loss, false verified-clean rate, protective actions per task, runtime/token cost. Use clustered bootstrap by task/workflow; paired confidence intervals; equivalence/noninferiority tests instead of interpreting non-significance as equivalence.

**Pass:** baseline tables, uncertainty, negative cases, held-out analysis, ablations removing recovery-time labels, pair minimization, counterfactual traces, and oracle metadata.

## Gate 10 — Visualization, artifact release, paper (Weeks 13–14)

Build dashboard from saved data (not invented pictures): original/suppressed timelines; trace-to-semantic graph with provenance vs intervention-supported edges; blast-radius lanes (Browser→API→DB→jobs→SSE→other actors); recovery-time heatmaps; MAP-Elites archive; risk calibration / success–harm trade-off. Clicking any node opens raw run and oracle certificate.

Publish a clean source repo, Docker/uv/npm lockfiles, test commands, anonymized/synthetic fixture dataset, valid and invalid trial archive, training/evaluation configs, model/dataset cards, dependency inventory, exact paper plot scripts, and immutable release manifest.

**Pass:** fresh-machine reproduce selected figures and core claims without private data; clearly state limits (single controlled app, modeled observer receipt, narrow backend concurrency and staging capabilities).

## Project organization and ownership

- **Systems/replay lead:** Gates 0–1, 3 infrastructure, deterministic scheduler, browser gateway, integration tests.
- **Contracts/oracle/recovery lead:** Gates 2 and 4, preservation invariants, proof fixtures, recovery comparisons.
- **Evolution/causality lead:** Gate 3 semantic differences, Gate 5 search/minimization, graphs.
- **ML/evaluation lead:** Gates 6–9, Tinker pipeline after approval, statistics, shield integration; all contributors help with Gate 10.

Review a single integration branch weekly, with a red/green gate checklist. No separate feature is complete until tests and evidence artifacts are checked in.

## Explicit stop/go rules

- **No evolution** until generalized oracles and replay-validity tests pass.
- **No learned labels** from `CONFLICT`, `UNKNOWN`, `CENSORED`, or planner timeout as if they proved impossibility.
- **No Tinker spending** until data leakage checks, structured baseline, tiny costed smoke plan and explicit authorization.
- **No claim of ML novelty** unless matched-data boundary supervision beats random-counterfactual supervision on held-out workflows.
- **No claim of safety improvement** unless actual agent rollouts reduce unauthorized effects under matched task-success/intervention budgets.
- **No strong causal claim** from shared `action_id` or temporal ordering alone; use controlled interventions.
- **No automatic live snapshot restoration** in the presence of legitimate concurrent work.

## First three issue cards for a coding agent

**AC-001 (P0): Fix replay certificate coverage.** Modify `afterclick/replay/demo.py::validity_certificate` to validate `conflict` pre-action equivalence and include its checkpoint hash. Add positive and mutated-conflict negative tests under `tests/replay/`; run `bash scripts/check.sh` and demo. Keep all original branch outcome semantics.

**AC-002 (P0): Fix frontend same-value ABA rebase.** Add field-revision tokens server-side and atomic conditional semantics to API; update `apps/flowboard-web/src/main.tsx::save` 409 behavior to compare revisions, not just values. Add two-browser same-value overwrite regression test. Preserve draft and show conflict on an intervening same-value write.

**AC-003 (P0): General contract and oracle.** Introduce explicit generic task/effect contract with a separate oracle and new priority/escalation and status/summary fixtures. Test known recoverable, irreversible, conflict, unknown, censored, and false-planner-success cases. Do not modify the current oracle's result semantics without versioning the existing fixture evidence.

## Final definition of success

A strong publication result is not “we found a dramatic cascade.” It is evidence that (a) the search finds *verified* boundary pairs more efficiently or with greater mechanism coverage, (b) a model trained on these pairs improves *held-out, pre-action* recoverability-risk prediction relative to equal-budget counterfactual training, and (c) an integrated safety controller reduces *real measured* unauthorized/irreversible effects without materially reducing legitimate task completion. If one claim is unsupported, narrow the paper and report it truthfully.
