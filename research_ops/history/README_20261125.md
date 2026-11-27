# AfterClick

**Prospective intervention under progressing asynchronous effects**

## Latest v12 research status

The v12 research program is **incomplete**: 1,479 of 2,904 registered TEST assignments have terminal
records; 1,425 remain unexecuted. The benchmark implements 72 DEV and 216 TEST contracts in two
applications. Missing experiments and causal-control requirements are documented explicitly.

Read the [v12 manuscript](paper/v12/AFTERCLICK_V12_MANUSCRIPT.md),
[paper PDF](output/pdf/AFTERCLICK_V12_MANUSCRIPT.pdf),
[appendix PDF](output/pdf/AFTERCLICK_V12_APPENDIX.pdf),
[acceptance audit](research_ops/completion_v12/final_package/FINAL_ACCEPTANCE_AUDIT.json), and
[compact evidence](evidence/v12/README.md). The complete raw-data archive is separate from Git and
has not been uploaded; [publishing instructions](docs/GITHUB_PUBLISHING.md) explain how to distribute
and restore it. A source-only clone does not contain the raw trials.

## Earlier bounded study

The new bounded study is complete: 12 frozen Qwen3.5-9B source instances and 36 valid paired branches. Immediate protection records zero unauthorized effects versus two for each delayed policy, but misses one legitimate restoration objective. Safe completion is 11/12 versus 10/12; the paired comparison is inconclusive, with no superiority or equivalence claim.

Read the [manuscript](paper/AFTERCLICK_RECOVERABILITY_PAPER.md), [experimental appendix](paper/AFTERCLICK_EXPERIMENTAL_APPENDIX.md), [results](research_ops/PROSPECTIVE_TIMING_RESULTS.md), and [handoff](research_ops/SESSION_HANDOFF.md). UndoBench already captures the demonstrated history-aware ranking reversal and Cordon already stages external effects; broad publication novelty remains limited/unestablished. Earlier studies and negative/invalid results are preserved.

Fresh full regression: **330 tests passed**, one upstream warning. New study: 172 genuine generations including development, $2.779 conservative compute accounting, $0 cash billed, endpoint idle. No further paid collection is queued.

## Try FlowBoard

Requires Docker with Compose. From this repository:

```sh
docker compose up --build -d
```

Open [FlowBoard](http://localhost:5173) in two tabs. Edit TASK-42's description; it autosaves after
600 ms and appears in the other tab. Mark it reviewed to update TASK-43's readiness and create a
release notification. The normal app advances its backend logical clock automatically.

Compose exposes only loopback ports: web 5173, API 8000, PostgreSQL 55432. The database password
is a deliberately public local-development fixture credential. This is an isolated testbed, not a
production deployment. Research control endpoints are **not mounted** on the public application.

## Reproduce the first research milestone

Requires Python 3.11+, Node 24, [uv](https://docs.astral.sh/uv/), and Docker:

```sh
bash scripts/demo.sh
```

This runs seven actual Chromium/PostgreSQL branches and writes:

- `artifacts/demo/report.json`: latest full report, source/dependency manifest, and certificates.
- `artifacts/demo/explorer.html`: offline interactive timelines and state comparisons.
- `artifacts/demo/<run_id>/`: retained per-branch records and full report for each invocation.

Open the HTML file in a browser. The controlled fixture has the following **measured**, narrow
outcomes: description goal succeeds with or without the review; early recovery succeeds; a delivered
scripted-observer receipt prevents complete recovery; an overlapping collaborator write causes
abstention. The executable asserts replay validity and preserves failed trials. See
[experiments](docs/EXPERIMENTS.md) for the exact intervention and claim boundaries.

Run the separate planted **backend oracle pilot** (24 cases across three workflow families):

```sh
uv run python -m afterclick.evaluation.pilot --output artifacts/oracle-pilot
```

This validates recovery witnesses, not adaptive browser performance. Original evidence is retained
under `evidence/v0/` and the `afterclick-v0` tag. For a committed clean checkout,
`bash scripts/validate-isolated.sh` clones the exact revision and runs the build, suite, browser demo,
and oracle pilot in Linux with a separate PostgreSQL container. Logs/reports are retained under
`artifacts/isolated-*`; it exposes no host database port.

Fresh P0 established 122 tests, seven scripted branches and 24 planted backend cases. The first bounded
checkpoint added causal capability tests, matched acquisition studies, local predictors and an
online suppression controller. The [claim register](research_ops/CLAIM_REGISTER.md) distinguishes
engineering validation, synthetic comparisons and the locked final mechanism.

The original interface-stage financial records remain in [P1 cost report](research_ops/P1_COST_REPORT.md). The earlier additional $20 timing-study allocation used $2.779 conservatively; its historical ledger is [preserved](research_ops/TIMING_SPEND_STATE.json). The subsequent v12 program has a separate $18 authorization and $17.9673 conservative accounting, recorded in the [final financial summary](research_ops/completion_v12/final_package/FINAL_FINANCIAL_SUMMARY.json). These are separate study records, not interchangeable remaining balances. Paid jobs are closed.

## Local development and checks

```sh
docker compose up -d --wait db
uv sync --frozen --group research
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
uv run playwright install chromium
bash scripts/check.sh
```

Run the API and Vite in separate terminals (stop Compose `api web` first if they occupy these ports):

```sh
AUTO_TICK=true uv run uvicorn afterclick.api:app --host 127.0.0.1 --port 8000
npm run dev --prefix apps/flowboard-web
```

All integration tests use real PostgreSQL in isolated `ac_test_*` schemas. Tests do not reset the
ordinary `flowboard` schema. For a non-default database, set `DATABASE_URL` to a PostgreSQL psycopg
SQLAlchemy URL; the account needs schema creation permission. Do not use a production database.

## Repository map

| Area | Implementation |
|---|---|
| React task board/editor | `apps/flowboard-web/` |
| FastAPI application and separate control plane | `afterclick/api.py`, `afterclick/control.py` |
| SQLAlchemy schema, Alembic migrations, database isolation | `afterclick/infrastructure/`, `migrations/` |
| Domain writes, outbox, durable scheduler, automations | `afterclick/domain.py` |
| Bounded browser action gateway | `afterclick/agent/` |
| Replay certificates, browser demo, artifact explorer | `afterclick/replay/` |
| Conditional compensation and independent oracle | `afterclick/recovery/` |
| Versioned contracts and generic independent oracles | `afterclick/contracts/`, `afterclick/evaluation/` |
| Task contract | `fixtures/tasks/description-review.json` |
| Infrastructure and CI | `docker/`, `compose.yaml`, `.github/workflows/ci.yml` |

Python application code uses a single installable package rather than importing from a hyphenated
app directory. The `afterclick/research/` package contains finite recovery closure, matched search, strictly visible
features, local risk models, budget guards and a once-only locked evaluation runner.

## Continue the project

Read [research specification](docs/RESEARCH_SPEC.md), [architecture](docs/ARCHITECTURE.md), and
[progress](docs/PROGRESS.md), then inspect Git status. Preserve validated foundations. Both bounded studies are complete. Next evidence should come from independent contract review and
a measured external workload; do not tune on either opened final set. Historical plans
in the specification are proposals, not completed claims. See [current gates](docs/COMPLETION_GATES.md).

## New real-agent development pilot (2026-11-23)

A separate natural-task Qwen3.5-4B pilot completed **4/12 tasks** with 12 valid executions. All eight required-comment tasks left drafts unsubmitted. The preregistered competence gate failed, so paid option-preserving intervention and new held-out comparisons were not run. Both earlier frozen studies remain unchanged; no new novelty claim is supported.

See [the additive pilot report](paper/MODEL_IN_LOOP_PILOT.md), [reproduction instructions](research_ops/MODEL_SPRINT_REPRODUCIBILITY.md) and [current handoff](research_ops/SESSION_HANDOFF.md).

## 2026-11-24T06:14:12.740600+00:00 — Additive study checkpoint

## Additive live-agent timing study — 2026-11-24

The [new report](paper/TCOPE_PAPER.md) preserves the earlier bounded and observability studies. It records221genuineQwen3.5-9Bgenerations on13sourceinstances, with dependent controller suffixes reported separately. Immediate staging is the strongest economical development baseline; no incremental TCOPE safety benefit is established. Locked confirmation stops after7reconstruction-invalid branches and49unattempted branches because stale core-browser state was not reconstructed; no final efficacy rate is claimed. Full local suite:292passed,1dependencywarning.

[Reproduction instructions](docs/TCOPE_REPRODUCIBILITY.md), [current novelty verdict](research_ops/FINAL_NOVELTY_VERDICT.md), and [claim ledger](research_ops/CLAIM_REGISTER.md) document the scope. Saved-evidence regeneration makes zero paid requests:

```sh
.venv/bin/python -m research_ops.scripts.reproduce_tcope --output /tmp/afterclick-tcope-reproduction
```

## Unified recoverability paper (24 November 2026)

The consolidated empirical manuscript is [AfterClick: The Limits of Recoverability in Tool-Using LLM Agents](paper/AFTERCLICK_RECOVERABILITY_PAPER.md). It centers asynchronous effects, observation delay and safe task completion; OECR is supporting methodology. Earlier study papers and frozen results remain available. The [evidence audit](research_ops/RECOVERABILITY_EVIDENCE_AUDIT.md), [claim matrix](research_ops/RECOVERABILITY_CLAIM_MATRIX.md), and [readiness verdict](research_ops/RECOVERABILITY_SUBMISSION_READINESS.md) distinguish supported findings from missing live confirmation. This is a bounded empirical report; a superior safety algorithm and publication-level novelty are not established.

Regenerate the inventory/tables/new figures locally with `.venv/bin/python -m research_ops.scripts.standardize_recoverability`. The PDF formatting helper is `research_ops/scripts/format_recoverability_paper.py` and requires ReportLab (available in the Codex bundled PDF runtime). No model calls are part of these commands.

## Reviewer-response v10

The [revised manuscript](paper/AFTERCLICK_RECOVERABILITY_PAPER.md) and [experimental appendix](paper/AFTERCLICK_EXPERIMENTAL_APPENDIX.md) distinguish current recovery from full historical recovery. A new same-execution scoring audit and unchanged official UndoBench DEV baseline study challenge the novelty claim: the external benchmark already captures the demonstrated state/history ranking reversal. [Reviewer response](research_ops/REVIEW_RESPONSE.md) and [current readiness](research_ops/REVIEW_SUBMISSION_READINESS.md) retain the remaining gap in genuine live intervention/external model validation. Fresh320-test and6-phase known-protocol reproduction results are separately scoped from later targeted amendments. New phase uses0genuineQwen calls/$0Modal; no paid study is silently substituted with local tests.

### Independent-supervisor extension (Ablation C)

The bounded development pilot records27genuine Qwen generations (21actor,6separate reviewer calls) over2new sources and6validpairedbranches. Fast deterministic protection and stage-first review each safely complete2/2; sequential review1/2. Only3/6reviewoutputs satisfy the strict schema, and the declared fallback is enforced. No added supervision benefit over the fast rule or independent supervisor confirmation is established; paid collection is closed. [Results](research_ops/SUPERVISOR_DEVELOPMENT_RESULTS.md), [stop decision](research_ops/SUPERVISOR_CONFIRMATION_RESULTS.md), [updated paper](paper/AFTERCLICK_RECOVERABILITY_PAPER.md), [handoff](research_ops/SESSION_HANDOFF.md). Original frozen studies are preserved.

No-model reproduction: `.venv/bin/python -m research_ops.scripts.verify_supervision --runs artifacts/research_runs/c1-supervisor-development-v1`.


## V12 completion program — implementation in progress

The supplied v12 completion kit is preserved under `research_ops/completion_v12/`. The new program is **incomplete**: one DEV contract is authored, no TEST contract or protocol is frozen, and no new model evaluation has run. The separate OpsConsole backend/UI, historical graph atlas, finite proof checker and a complete 60-trial local enforcement-delay experiment have executed. See [measured checkpoint and reproduction commands](research_ops/completion_v12/REPRODUCTION.md) and [current v12 handoff](research_ops/completion_v12/SESSION_HANDOFF.md). V11 artifacts, paper, negative results and finance ledgers are retained. Latest endpoint-specific authorization is $18 for new v12 credit use; $0 has been used.

## V12 continuation — 25 November 2026, 21:14 UTC

The newer v12 cohort now has all 72 DEV and 216 TEST contracts reference-qualified (576 complete PostgreSQL/browser/HTTP witnesses; 10,944 independently checked oracle mutations). Genuine model DEV collection is running in finite parallel cloud batches: the completed 552-episode balanced run made 2,521 calls and achieved zero full safe completions. Those negative results are preserved; a clarified-interface DEV run is active. No TEST inference has run and the study remains incomplete. See [current progress](docs/PROGRESS.md) and [v12 state](research_ops/completion_v12/STATE.json). The endpoint cap is $18 in credits, with no cash authorization.
