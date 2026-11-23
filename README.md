# AfterClick

**Temporal recovery contracts and the limits of boundary-focused learning**

A working PostgreSQL/Chromium research system with an evidence-backed mixed/negative study.
The final suite passes **239 tests**. One hybrid live-policy replay has 12/12 valid branches;
102 planted backend cases cover four recovery obligations. These do not measure organic mistakes.

Matched search favors coverage over the targeted local explorer. Boundary data improve a fixed
boosted tree, but the stronger no-learning mixture remains better. Learned and simple timer shields
tie at matched task completion and intervention burden. Broad superiority and publication novelty
remain unestablished.

Read [the paper draft](paper/PAPER.md), [reproduction guide](paper/REPRODUCE.md),
[current evidence](research_ops/START_HERE.md), and [session handoff](research_ops/SESSION_HANDOFF.md).
The source and local evidence package preserve unsuccessful attempts. Nothing was pushed or published.

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

Fresh P0 established 122 tests, seven scripted branches and 24 planted backend cases. The present
checkpoint adds causal capability tests, matched acquisition studies, local predictors and an
online suppression controller. The [claim register](research_ops/CLAIM_REGISTER.md) distinguishes
engineering validation, synthetic comparisons and the locked final mechanism.

The new live pilots used about $0.72 conservative guard accounting. Conservative remaining credit
is $27.48 with $0 billed. The user endpoint is preserved at min0 with zero containers verified;
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
[progress](docs/PROGRESS.md), then inspect Git status. Preserve validated foundations. The bounded study is complete. Further scientific work should use a newly frozen, independently
implemented workload/schedule distribution; do not tune on the opened final set. Historical plans
in the specification are proposals, not completed claims. See [current gates](docs/COMPLETION_GATES.md).
