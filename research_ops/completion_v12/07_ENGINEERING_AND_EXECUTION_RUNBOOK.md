# 07 — Repository-specific implementation and full execution runbook

## Starting point: archive v11 is not the new v12 experiment

The actual checkout may differ from `684_final 11.zip`: verify `git status`, uncommitted changes, root path, branch/revision, current docs. Never overwrite existing user changes. Commit an immutable v11 provenance snapshot or create a dedicated worktree/branch and preserve all 91 sealed run directories and original protocol hashes.

Read these existing files before editing code:
- `research_ops/STATE.json`, `SESSION_HANDOFF.md`, `EXPERIMENT_REGISTRY.jsonl`, `TIMING_CONFIRMATION_FREEZE.json`, `TIMING_FEATURE_LEDGER.md`, `SUPERVISOR_DEVELOPMENT_RESULTS.md`, `ABLATION_INTERACTION_MATRIX.csv`.
- `paper/AFTERCLICK_RECOVERABILITY_PAPER.md`, `paper/AFTERCLICK_EXPERIMENTAL_APPENDIX.md`.
- `afterclick/tcope/workload_specs.py`, `workload_oracle.py`, `driver.py`, `gateway.py`.
- `afterclick/review/{progressing,continuation,paired,study_runner,semantics}.py` and `afterclick/review/supervision/`.
- `afterclick/research/recoverability.py`, `afterclick/oecr/`, event ledger and external receivers.
- `research_ops/scripts/{verify_timing_study,verify_supervision,reproduce_research}.py`.

Use a dedicated new namespace such as `afterclick/completion_v12/` and `research_ops/completion_v12/`. Avoid mutating source hashes of the old frozen runs.

## Phase 0 — Baseline reproducibility and correctness

- Confirm previous archived outcome counts and hashes via original no-paid reproduction scripts.
- Run current full local suite; investigate the two preserved legacy timing failures. Fix genuine bugs without rewriting historical claims. Preserve before/after traces and records; any timing-test instability should have a reproducible cause and robust assertion.
- Check baseline app behavior in PostgreSQL + Chromium + independent HTTP service receivers; document exact UI semantics, client buffer, SSE ack, and clock assumptions.
- Audit current Modal/provider availability and model revision; do not confuse archived credit numbers with live billing.

**Gate:** existing frozen evidence reproducible; no silent test weakening; regression status documented. No new paid TEST runs before qualification.

## Phase 1 — Implement complete task environments

- Extend FlowBoard only where suitable. Build OpsConsole with an actually different business state model/workflow engine and testable permissions and irreversible effects.
- Implement all 216 TEST task specifications and disjoint DEV tasks, including business documents, dynamic collaborator schedules, task-obligation DAG, private oracles and public observations.
- At least one separately verified safe reference completion for every feasible task. Mutation/property tests for all oracle families; release every scenario as independent provenance-controlled fixture.
- Validate clean competence workflow and nonstressed settings without disabling essential app behavior.

**Gate:** complete task registry with hashes, no placeholder task slots, all contracts independently executable, split leakage audit passes.

## Phase 2 — Recoverability graph and replay mechanism

- Implement G1 logged action/effect provenance and G2 certified counterfactual/finite-reachability graph according to `04_RECOVERABILITY_GRAPH_AND_ORACLES.md`.
- Reproduce existing Source 05/07/11 and supervisor case timelines from old traces. Validate graph against independent raw ledgers and recorded receipt histories.
- Integrate bounded solver and explicit UNKNOWN/partial feasibility. Add data-dependent oracle correctness tests and proof certificate tests.
- Instrument effective enforcement and event commitment clocks (not just clicked UI events).

**Gate:** machine-readable graph, renderer, certificates, source trace cross-checks and non-heuristic negative labels.

## Phase 3 — Full protocol qualification and freeze

- Implement P0–P5 policies exactly and fair public-information gateway enforcement. Keep P2 separate from P3; supervisor fallback must be logged.
- Exercise complete DEV benchmark across every app/family/level, including real DB, browser, workers and receivers; not a two-task smoke test. Model inference in DEV is allowed to validate competence and calibrate serving performance, with full records.
- Record legitimate UI behavior and any model-inference failures. Fix DEV-only ambiguities and oracle bugs, then rebuild disjoint TEST if necessary **before TEST freeze**.
- Compute cluster-level sample-size/power, full compute forecast, scheduling and storage. Credits may be used as needed; forecast is for capacity/efficiency, not a hidden permission cap.
- Publish immutable TEST protocol and file hashes before reading TEST outcomes. Prespecify all failure handling, retries and analysis.

**Gate:** signed TEST freeze, expected source count, complete trial manifest and seeds, no open qualification blockers.

## Phase 4 — Full genuine primary-model evaluation

- Execute all 216 tasks × 3 regimes × 3 seed worlds × 4 stress policies, plus 648 clean episodes, with fresh model continuations and real asynchronous workers. Preserve raw request/response records, receipts, source cuts, and independent labels.
- Execute the separately frozen 648 restoration episodes and 648 supervision episodes. Keep paired source lineage and execute in counterbalanced order.
- Store each trial atomically and resume idempotently after interruption. Monitor provider health, leakage, incomplete model calls, DB/Chromium/HTTP failures and asynchronous receipts. Technical retries must preserve original attempts and follow the frozen retry policy.
- No early stop for unexpected poor performance or lack of statistical significance. No model-prompt tuning after TEST opens.

**Gate:** all registered valid episodes attempted; invalid/censored/missing counts and reasons reconciled against the frozen manifest.

## Phase 5 — Model/benchmark replication

- Pin an independent second model and rerun the **entire core** population on matched task/schedule/policy definitions, if exact tool semantics can be preserved. Record incompatibility faithfully, not silently.
- Complete official UndoBench TEST runs with genuine model tool use and official oracles unchanged; compare corresponding metrics without pretending the benchmark has identical effect timing.
- Where feasible, complete Cordon-compatible staging/semantic-transaction baseline and run through matched AfterClick task contracts; explicitly distinguish direct reproduction, faithful port, and local proxy.
- Assess cross-application results separately: app differences are confounded with interface/business implementation unless tasks and mechanisms are structurally matched.

**Gate:** external data and published baseline comparisons are genuinely executed and properly scoped, or publication claims are narrowed with explicit blockers.

## Phase 6 — Audited analysis and manuscript

- Re-score all trials from raw evidence with independent validators; verify source hash lineage and clock calibration.
- Fit preregistered cluster-aware statistics, report null/negative findings, perform latency contrasts and bounded viability checks.
- Generate the required figures from scripts, with clear observed/certified/unknown edge markings and separate synthetic/live results.
- Write complete article, method appendix, task benchmark card, code reproducibility artifact, external validity assessment, and literature novelty audit.
- Include available source-trace examples as qualitative analysis only; never replace independent quantitative evaluation with selected stories.

**Gate:** audited result tables and figures regenerate from raw data, manuscript claims are in the evidence ledger, and no unfounded claim of optimality or superiority remains.

## Full-run failure and spend operations

- **Authorization:** previous `$20` research-credit ceiling is superseded by current request. Run needed scientifically justified finite trials using available credits, with live metering, no arbitrary experimental dollar cap. Keep old and new ledgers separate; avoid provider billing or paid subscriptions not covered by credits without additional explicit permission.
- Enforce job-level timeouts, startup readiness limits, idempotency, exact registered trial counts, provider usage tracking and safe scale-to-zero after each phase. Running out of credits is not permission to bill a personal credit card.
- Checkpoint progress atomically: task IDs, policy, model revision, schedule seed, source hash, status, receipts, raw logs, checksum. Use a queue/job orchestrator rather than a shell loop that silently drops failures.
- Never hide or overwrite bad outcomes. A stalled provider, model failure, invalid source cut, or open external receipt is a recorded scientific status, not a substitute for task failure.
- If Codex cannot complete the full program in one execution window, deliver the working state and *exact* resumable commands/manifest progress. Do not claim it completed or that future compute has been scheduled unless actually scheduled.

## Required final outputs (repo paths proposed)

```
research_ops/completion_v12/
  PROTOCOL_FROZEN.json
  TASK_REGISTRY.jsonl
  SOURCE_WORLD_MANIFEST.jsonl
  EXECUTION_MANIFEST.jsonl
  EXECUTION_SUMMARY.json
  EVIDENCE_LEDGER.jsonl
  FINANCE_AND_RESOURCES.jsonl
  REPRODUCTION.md
  UNCERTAINTY_AND_STATISTICS.md
  FAILURE_ATTRIBUTION.jsonl
  NOVELTY_AND_EXTERNAL_COMPARISON.md
  SESSION_HANDOFF.md
artifacts/research_runs/v12-*/
  raw/*          # requests/actions/receipts/oracle/snapshot and clock records
  qualified/*    # certificates, manifests, provenance
  analysis/*     # recomputed tables/figures
paper/
  AFTERCLICK_V12_PAPER.md
  AFTERCLICK_V12_APPENDIX.md
  figures/v12/*
```

Keep revisions and commands deterministic. Do not silently backfill missing records.
