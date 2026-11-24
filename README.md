# AfterClick

**Temporal recovery contracts and the limits of boundary-focused learning**

A working PostgreSQL/Chromium system with two preserved, bounded studies. Current suite:
**260 tests passed**. Native tool calling completed the previously failed two-field browser task
in one small comparison; JSON remains a baseline and the original frozen replay is unchanged.

The new queued-dispatch study separates loss of cancellation, external access and receipt arrival.
It validates118SQL boundary endpoints, but finds no general learned-controller advantage over strong
rules. Boundary-focused data worsen held-out risk calibration for the preselected trained model.
Verification-delay races are measured directly; larger models and extra inference are not a remedy
for an already-lost control capability.

Read the [new paper](paper/OBSERVABILITY_PAPER.md), [new reproduction guide](paper/OBSERVABILITY_REPRODUCE.md),
[original paper](paper/PAPER.md), [claim register](research_ops/CLAIM_REGISTER.md), and
[current handoff](research_ops/SESSION_HANDOFF.md). All conclusions are bounded by synthetic workload,
static public telemetry, limited mechanisms and independent SQL audits. Publication novelty remains
inconclusive. No results or code were pushed or published.

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

The latest format comparison adds about $0.3245 conservative guard accounting; cumulative standing
mandate guard use is about $1.0445. Conservative observed credit is $27.39 with $0 billed. The user endpoint is preserved at min0 with zero containers verified;
no paid process is active. The latest mandate supplies standing bounded authorization, with an
$8 reserve, but unused budget is not a reason to make more calls. See [cost report](research_ops/P1_COST_REPORT.md).

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
