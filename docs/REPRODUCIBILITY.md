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
uv run python -m afterclick.evaluation.pilot --output artifacts/oracle-pilot
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

No API/model credentials are required for tests, the scripted demo or the backend oracle pilot.
The dirty checkout also contains an opt-in Gemini runner and a planning-kit Modal smoke script;
neither is authorized by these reproduction commands. Historical Gemini pilots are invalid.
Tinker API/model inspection, cost estimation, smoke configuration and explicit authorization remain
future work.

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
them. The original v0 report predates the first commit and retains a null Git revision. New
committed runs record exact revisions; clean-clone validation requires and preserves a clean tree. Local experiments do not run an application container: `application_image_digest`
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

No arbitrary in-flight JS snapshot, validated live adaptive LLM continuation, general network-loss schedule,
long-running collaborator policy, multi-worker crash recovery test, or multi-seed benchmark is
implemented. Browser HTTP and SSE arrival order are not fully controlled; checkpoints await the
specified UI/commit barriers and exclude only declared transport telemetry. Full image pinning,
dependency upgrades, research-table migrations, and independently audited oracle coverage remain
future work. See `DECISIONS.md` for the npm development-tool advisory and `PROGRESS.md` for checks.

## Clean-clone Linux reproduction

From a clean committed tree, run `bash scripts/validate-isolated.sh`. It clones the exact revision
into a temporary directory, builds a Linux validation image, starts a separate ephemeral PostgreSQL
instance without host ports, and runs the frontend build, all tests, browser demo and oracle pilot.
It captures raw logs and artifacts under `artifacts/isolated-*`, then stops only that validation
Compose project. The source clone is retained for inspection. This is isolation on the same Docker
host, not an independently operated remote machine. Remote GitHub CI has not run here.

The container need not contain the Docker CLI; manifests explicitly record unavailable image metadata
as empty, while source hashes and Git revision remain available. The host build log records resolved
base-image digests. No digest is fabricated. Model credentials are not mounted.

## Fresh P0 audit (2026-11-22)

Run `p0-20261122-audit` retains the protocol, amendments, command logs, JUnit, source/lock
hashes and failed environment/clock diagnostics under `artifacts/research_runs/`. The local
database initially was stopped; only Compose `db` was started. PostgreSQL 17.7 and Chromium
159.0.8154.6 were used with Python 3.11.14, Node 24.12.0 and uv 0.13.9. The suite passed
122/122 tests. The extra 34 cases are enumerated in `raw/analysis-v2/tests_delta.json`.

`scripts/check.sh` accepts `AFTERCLICK_TEST_REPORT` to retain fresh JUnit without replacing an
earlier report. With `.bootstrap/bin` on PATH, the audit used the normal check script. To
regenerate the saved analysis into a fresh directory, without database writes/model calls:

```sh
.venv/bin/python research_ops/scripts/analyze_p0.py \
  artifacts/research_runs/p0-20261122-audit --output /tmp/afterclick-p0-review-1
```

The destination must not already exist. Counts and certificates are regenerated; raw run data
remain unchanged. No scientific figure/CI was estimated from fixed development fixtures;
the actual demo explorer is retained. See `research_ops/STATE.json` for the mandatory human gate.

## P1 provider integration

The project environment/locks remain unchanged. Modal CLI 1.6.4 is isolated via
`.bootstrap/bin/uv tool install modal==1.6.4 --python .venv/bin/python`; on this host its
executable is `/Users/gomathydhanya/.local/bin/modal`. Authentication lives outside Git.
No terminal setup or global Python package installation is required for the application.

Free checks: `.venv/bin/pytest tests/agent -q`; `.venv/bin/pytest -q`. HTTP-mock replay through
the adapter on actual PostgreSQL/Chromium uses a fresh output directory:

```sh
.venv/bin/python research_ops/scripts/p1_mock_replay.py --output artifacts/p1-mock-review
```

The new `afterclick.evaluation.modal_smoke` defaults to preparation only; `--live` additionally
requires exact paid approval/configuration and proxy environment credentials. Cache/recorded/mock
origins are recorded separately. Unknown completions freeze the persisted journal on restart.
The completed experiment's lifecycle helper refuses reuse once finalization.json is present.

P1 raw data are in `artifacts/research_runs/p1a-20261122-local`, `p1b-20261122-readiness`, and
`p1c-qwen35-9b-smoke-v1`. The last is infrastructure-inconclusive, with no model decisions.
Never rerun its deployment as an ordinary reproduction command. Read `research_ops/STATE.json`
and `SESSION_HANDOFF.md`; a new paid attempt requires a new approval. Active endpoint list is
empty; current usage cap remains $2 and the effective default net spend limit is $0.

V2 final evidence: `artifacts/research_runs/p1c-qwen35-9b-smoke-v2`; free regeneration:
`.venv/bin/python research_ops/scripts/analyze_p1_diagnostic.py artifacts/research_runs/p1c-qwen35-9b-smoke-v2`.
Current full suite200passed, raw local validation in `p1d-20261123-4b-readiness`.
4B proposal `p1c-qwen35-4b-diagnostic-v1` is unexecuted/unapproved; dryrun defaults0network.
Read NEXT_EXPERIMENT.md; exact protocol-hashed approval is required before --execute.

## Current checkpoint — 2026-11-23 UTC
Full suite212passed; project/lock environment unchanged. RealPG isolatedac_* and Chromium required
for `.venv/bin/pytest -q`. Paid existing4Bv2/v3 failed gates and are closed; do not rerun their
controllers as reproduction. User-owned endpoint exists idlemin0/max1/buffer0/idle2; never stop/delete.
Raw request/response, task judgments and cleanup are archived under their distinct run IDs.

Offline48-case local mechanism evidence regeneration (fresh destination):
```sh
.venv/bin/python research_ops/scripts/analyze_mechanisms.py artifacts/research_runs/p2-20261123-distinct-mechanisms-v1 --output /tmp/afterclick-p2-review
```
This reads saved data only, recomputes48primary certificates plus3predeclared receipt follow-ups,
and emits counts/per-seed CSV,summaryJSON,receipt timelineSVG. It creates no model/GPU/DB resources.
Primary48-case and recorded-input audit runners refuse reuse; new executions need new registrations.
Current artifacts are sealed with checksums.json; verify checksums before analysis. Failed/invalid
traces and earlier narroweranalysis remain. No task/model/shield training or held-out evaluation.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

Current bounded study: `paper/REPRODUCE.md` is the complete procedure. Install optional scientific
dependencies using `uv sync --frozen --group research`; the check script now includes that group.
Final full suite: 239 passed in 172.43s, one warning. Scientific source hashes (60 paths) still match
P6/FROZEN.json after confirmation. Six figures/five tables regenerate from saved data. The local
bounded reproduction CLI is dry-run by default and cannot launch paid workloads. Its orchestration
was dry-run/guard tested; it was not redundantly rerun through all six phases.
Numerical study uses finite models plus separately denominated fresh SQL witnesses, not thousands
of live browser trajectories. No publish/push or public artifact release is authorized.


## 2026-11-23T20:06:10.697972+00:00 — native interaction and observability extension

New extension: paper/OBSERVABILITY_REPRODUCE.md. 260tests pass; original207 frozen paths unchanged, new132 frozen paths match. Native default selection glue mock-tested; old JSON replay retained. New bounded2phase local reproduction actually completed: obs-check-20261123. All numerical metrics identical excluding elapsed_seconds. Run verify_observability.py and render_observability.py --output FRESH_PATH to check saved outputs. These commands have no network/model inference. The reproduction --execute uses real isolated localPG, fixed known protocols/seeds, and is not independent confirmation. No further paid reuse of i1 is permitted.
