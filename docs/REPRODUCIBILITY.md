# Reproducibility

## Environment and exact commands

Validated on macOS x86_64 using Python 3.11.14, Node 24.12.0, npm 11.6.2, uv 0.13.9,
Docker Engine 29.8.1, and Compose 5.5.1. PostgreSQL uses `postgres:17.7`. Python dependencies
are locked in `uv.lock`, frontend dependencies in `apps/flowboard-web/package-lock.json`.
Playwright's downloaded Chromium version is recorded in every experiment manifest.

```sh
docker compose up -d --wait db
uv sync --frozen
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
uv run playwright install chromium
uv run ruff check afterclick tests migrations
uv run ruff format --check afterclick tests migrations
uv run pytest -q --junitxml=artifacts/tests.xml
uv run python -m afterclick.replay.demo --output artifacts/demo
```

On Linux, use `uv run playwright install --with-deps chromium` for required OS libraries.
If `uv` is not already installed, install it following its official instructions. During the initial
session it was bootstrapped into `.bootstrap/bin/uv` with a local Python venv; this ignored directory
is not a project dependency. `PATH="$PWD/.bootstrap/bin:$PATH"` makes the same scripts work locally.

The full app can also be built and launched with `docker compose up --build -d`. The Compose API
uses automatic logical ticks; reproducibility experiments create separate in-process server instances
with ticking disabled. Normal app data is retained in the Docker volume. Do not delete the volume
to reset research trials; each trial has its own schema.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL SQLAlchemy/psycopg connection | Local Compose DB on port 55432 |
| `AUTO_TICK` | Normal app dispatcher wall-clock loop | false; Compose sets true |
| `STATIC_DIR` | Optional built web directory served directly by API | unset |
| `EXPERIMENT_SCHEMA` | Separate control service's existing/created `ac_*` schema | required only for control service |
| `RESEARCH_TOKEN` | Isolated control plane bearer token | required only for control service |

No API/model credentials are required. No paid inference/training command exists. Tinker API/model
inspection, cost estimation, smoke configuration, and explicit authorization remain future work.

## Trial manifest and artifacts

`report.json` contains `run_id`, `data_mode`, task contract, environment/source manifest, all branches,
replay certificate, milestone acceptance booleans, and fixture findings if replay is valid. Each
branch includes checkpoint components, full checkpoint DB state, executed/suppressed action records,
public pre-observations and hashes, recorded write requests, final state, outcome hash, and failure
trace when applicable. Recovery branches also retain pre-recovery state, attempted operations, and
the independent verification certificate.

Conflict branches retain a separate `attempt_certificate` with its verification time and an
incomplete observation horizon, alongside the final-horizon `recovery_certificate`. This prevents
conflating immediate conflict detection with eventual downstream delivery.

Each invocation writes an immutable-by-convention `<run_id>` directory and updates the convenience
`report.json`/`explorer.html` at the output root. Failed branch outputs are saved too. These files are
local artifacts ignored by Git; CI uploads them even when checks fail. Preserve the run directories
when collecting research data. The files are not cryptographically signed or tamper-proof.

The manifest records package versions, Python, browser version, source-file hashes, frontend-build
hashes, Git revision if available, dirty status, and database image digests when Docker can inspect
them. The initial repository has no commit yet, so `git_commit` is null and source hashes identify
the exact code. Local experiments do not run an application container: `application_image_digest`
is explicitly null, never a fabricated digest. CI/containers should record their real image IDs when
experiments are later moved into containerized runners.

Seed 7 is fixed in the initial demo. Job tie-breaking is deterministic and the fixture is separately
identified. The source hash includes fixture and migration code. Browser clock starts at
2026-01-01T00:00:00Z, independent of the user's actual date. All backend timestamps are logical ms.
Horizon is 300 backend ms; recovery starts at 99, 200, or 150 for the conflict branch.

## Validity requirements

1. Create a fresh experimental schema and fresh browser context per branch.
2. Run the same prefix; settle debounce and committed response before checkpointing.
3. Compare every checkpoint component, including pending work and observation history.
4. Execute duplicate placebo continuations for both intervention arms.
5. Retain versions, field ownership, operation IDs, queued work, and semantic history in outcome hashes.
6. Exclude only random SSE consumer receipt identities/counts from replay equality; retain them raw.
7. Require a separate independent recovery certificate. Never infer recovery from planner status.
8. Abort causal interpretation on invalid replay. Demo exits nonzero on failed acceptance checks.

`goal_success` is the fixture's independent server-state oracle. The report deliberately marks
population action necessity `NOT_ESTIMATED`. There are no confidence intervals, statistical
significance tests, learned-risk scores, or comparative baseline results yet.

## Known reproducibility limits

No arbitrary in-flight JS snapshot, adaptive LLM continuation, general network-loss schedule,
long-running collaborator policy, multi-worker crash recovery test, or multi-seed benchmark is
implemented. Browser HTTP and SSE arrival order are not fully controlled; checkpoints await the
specified UI/commit barriers and exclude only declared transport telemetry. Full image pinning,
dependency upgrades, research-table migrations, and independently audited oracle coverage remain
future work. See `DECISIONS.md` for the npm development-tool advisory and `PROGRESS.md` for checks.
