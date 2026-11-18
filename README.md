# AfterClick

**Contrastive Recovery Boundary Learning for Autonomous Browser Agents**

Working research prototype: a real PostgreSQL/React application, deterministic backend scheduler,
Playwright scripted agent, validated execute/suppress replay, and conditional review compensation.
The full CRBL research program is not complete. No trained model, evolutionary results, or safety
improvement is claimed. No paid inference or Tinker training has been run.

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

## Local development and checks

```sh
docker compose up -d --wait db
uv sync --frozen
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
| Task contract | `fixtures/tasks/description-review.json` |
| Infrastructure and CI | `docker/`, `compose.yaml`, `.github/workflows/ci.yml` |

Python application code uses a single installable package rather than importing from a hyphenated
app directory. Evolution, learning, and evaluation packages will be added when they contain working
implementations, not empty scaffolds.

## Continue the project

Read [research specification](docs/RESEARCH_SPEC.md), [architecture](docs/ARCHITECTURE.md), and
[progress](docs/PROGRESS.md), then inspect Git status. Preserve validated foundations. The next
work expands replay coverage and independent recovery verification before starting evolutionary
boundary discovery. See [the original implementation brief](docs/IMPLEMENTATION_BRIEF.md).
