# Implementation progress

Last updated: **November 17, 2026** (America/New_York).

## Current milestone

The initial vertical slice and its first butterfly/recovery-boundary demonstration are implemented
and validated. This is **not** completion of the full AfterClick/CRBL research project. Gates 1–3
pass within the explicitly bounded fixture and capabilities below. Evolution, learning, defense,
and comparative research evaluation have not begun.

## Actually implemented

- Initialized the previously empty repository; preserved both user specifications in `docs/`.
- Docker Compose PostgreSQL/API/web, locked Python and npm dependencies, Alembic migrations,
  test scripts, and a GitHub Actions validation/upload workflow.
- Responsive React/TypeScript board and task editor: description, review, priority, assignee,
  status, comments, activity, pending/committed/failed/conflict states, and debounced autosave.
- Real versioned PostgreSQL writes, atomic outbox/job creation, exact-request idempotency,
  concurrent-version rejection, and independent field ownership.
- Four workflows: dependent readiness, critical escalation, assignment notification, project summary.
- Durable logical scheduler with seeds, pause, eligible-event release, prerequisites, monotone
  outbox publication, transaction rollback, and isolated fixture reset.
- SSE updates, browser receipt acknowledgements, reconnect cursor, two-session synchronization,
  and protection against an older HTTP refresh regressing the displayed task version.
- Separate token-protected experimental control app; no research routes in the public app.
- Bounded Playwright gateway and deterministic scripted agent; observations include current form
  values, not merely DOM text. Unsettled autosaves cannot be silently merged across agent actions.
- Fresh-schema/fresh-browser prefix reconstruction, execute/suppress interventions, two placebo
  pairs, checkpoint and outcome hashes, pending-work evidence, and explicit replay certificates.
- Owned review/readiness compensation, pending-job cancellation, undelivered notice deletion,
  preserved legitimate fields and immutable history, and a separate read-only recovery oracle.
- Seven-branch measured demo, per-run JSON artifacts, and an offline interactive butterfly explorer.
- Architecture, experiment, reproducibility, decision, and continuation documentation.

## Acceptance results

| Gate | Status and actual evidence |
|---|---|
| 1 — Application | Passed for the initial app: real writes, four automations, delayed/lost acknowledgement, duplicate requests, stale writes, two live sessions, SSE reconnect |
| 2 — Replay | Passed for a quiescent deterministic description prefix: equal checkpoints across matched branches and matching execute/suppress placebos |
| 3 — Recovery | Passed for the owned-review primitive: verified early recovery, verified delivered-receipt impossibility, independent overlapping-edit conflict, preserved independent priority edit |
| 4 — Evolution | Not implemented; no discovered/minimized archive or search baselines |
| 5 — ML | Not implemented; no training dataset, structured model, fine-tuned model, or held-out evaluation |
| 6 — Defense | Not implemented; action recording is not a learned shield or staging boundary |
| 7 — Research | Not implemented; no comparative statistics, ablations, generalization results, or paper results |

Latest measured demo:

Run ID: `326c8669ce7643e9a98350b2e676042e`. The recorded source hash was checked against
the final implementation and matched.

- All seven branches executed successfully; all milestone acceptance flags are true.
- Execute and suppress both achieved the committed description goal; fixture goal difference = 0.
- Extra review produced task review, dependent readiness, notice creation, and observer receipt.
- At t=99, recovery is `VERIFIED_RECOVERABLE`; at t=200, `VERIFIED_UNRECOVERABLE`.
- In the conflicting branch, the independent oracle reports `CONFLICT` at t=150. Recovery abstains;
  by t=300 the outstanding notice has arrived, so the final-horizon class is additionally
  `VERIFIED_UNRECOVERABLE`. Both certificates are retained.
- Population necessity is explicitly `NOT_ESTIMATED`. No model or safety improvement is claimed.

## Validation performed

**39 tests passed, 0 failed**, including 8 actual browser/protocol tests, 13 backend/scheduler
integration tests, 9 recovery tests, 3 replay-validity tests, and 6 unit/property tests.

- TypeScript compilation and Vite production build passed.
- Ruff lint and format checks passed for all 29 Python files.
- PostgreSQL, API, and nginx web images built; the Compose application is running on loopback.
- Database/API health and public task retrieval succeeded through nginx.
- Desktop and mobile FlowBoard screenshots were rendered and inspected.
- The offline explorer's early/late/conflict controls and the Docker-hosted FlowBoard passed
  Chromium smoke checks without page errors. The explorer screenshot was visually inspected.
- GitHub Actions is configured but has not run remotely; no remote repository is configured.

One non-failing upstream warning remains: Starlette's test client deprecates its httpx integration
in favor of httpx2. npm audit reports four high-severity development-tool entries through the same
picomatch advisory; see `DECISIONS.md` for scope and why no unsafe forced downgrade was used.

Failures encountered and resolved: ambiguous description accessible name; outbox publication ordering
needed to protect reconnect cursors; autosave action attribution across wait calls; stale refresh
version regression; distinction between conflict-time and final-horizon certificates; macOS binary
`.DS_Store` files accidentally included in source-text hashing. File hashing now uses SHA-256 bytes
and excludes hidden OS metadata; a regression test covers it. The manifest failure log is retained
as `artifacts/demo-manifest-failure.log`. No failed experimental trajectory was converted into a
successful result or silently used as causal evidence.

## Commands actually executed

Initial bootstrap used `python3.11 -m venv .bootstrap` and `.bootstrap/bin/pip install uv`; that
ignored tool venv supplied uv 0.13.9. Docker Desktop was started and the repository initialized.

```sh
.bootstrap/bin/uv sync --python python3.11
docker compose up -d db
npm install --prefix apps/flowboard-web
.venv/bin/python -m playwright install chromium
npm run build --prefix apps/flowboard-web
.venv/bin/pytest tests/unit tests/integration -q
.venv/bin/pytest tests/recovery tests/browser -q
.venv/bin/ruff check afterclick tests migrations --fix
.venv/bin/ruff format afterclick tests migrations
PATH="$PWD/.bootstrap/bin:$PATH" bash scripts/check.sh
.venv/bin/pytest -q --junitxml=artifacts/tests.xml
.venv/bin/python -m afterclick.replay.demo --output artifacts/demo
docker compose up -d --build api web
docker compose up -d --build api
curl --fail --silent http://127.0.0.1:5173/api/health
```

Formatting used Prettier 3.6.2 through npm exec; it is not a runtime dependency. The final test log
is `artifacts/final-tests.log`, XML is `artifacts/tests.xml`, build/check logs are in `artifacts/`, and
demo output is `artifacts/demo-run.log`. Earlier commands that exposed failures were followed by
fixes and the full final suite; see the counts above rather than stale intermediate logs.

## Files created / changed

The entire repository was created in this session. Main source groups:

- `afterclick/api.py`, `control.py`, `domain.py`: services and application/scheduler behavior.
- `afterclick/infrastructure/{schema,db}.py`, `migrations/`: PostgreSQL schema/isolation/history.
- `afterclick/agent/gateway.py`: browser action and observation recorder.
- `afterclick/recovery/{planner,oracle}.py`: compensation and verification.
- `afterclick/replay/{demo,server,viewer}.py`, `explorer.html`: reconstruction and artifact UI.
- `apps/flowboard-web/`: React UI, TypeScript/Vite setup, npm lockfile.
- `tests/{unit,integration,browser,recovery,replay}/`: passing verification suite.
- `fixtures/tasks/description-review.json`: independent task/recovery contract.
- `compose.yaml`, `docker/`, `.github/workflows/ci.yml`, `scripts/`, `pyproject.toml`, `uv.lock`.
- `README.md`, `AGENTS.md`, and the research/engineering documents in `docs/`.

Files are saved but no Git commit has been created. Experiment manifests therefore record null
Git revision, dirty status, and exact implementation/build hashes instead of inventing a commit ID.

## Reproducible demo and current services

```sh
bash scripts/demo.sh
```

If uv is only present in the initial local bootstrap, run:

```sh
PATH="$PWD/.bootstrap/bin:$PATH" bash scripts/demo.sh
```

FlowBoard: http://localhost:5173. Latest report: `artifacts/demo/report.json`. Interactive explorer:
`artifacts/demo/explorer.html`. Unique run directories preserve each subsequent invocation.
The normal board uses its own `flowboard` schema; experiment/test schemas are dropped after their
states have been saved. Docker services are intentionally left running for inspection.

## Scientific and engineering limits

Only one synthetic description/review task is evaluated end to end. The scripted observer's receipt
is a modeled irreversible effect, not proof of human observation. Recovery supports only one owned
review and its readiness effects. General graph attribution, multiple prerequisite families, adaptive
agents, arbitrary in-flight checkpoints, feedback interventions, and recovery optimization are not
implemented. There is no model training, evolutionary discovery, distributional necessity estimate,
calibration, confidence interval, held-out task benchmark, or learned controller.

The database writer is serialized within each experimental world. Client timer controls and explicit
network barriers cover the implemented scenarios, not arbitrary network or OS schedules. Actor IDs
are provenance, not production authentication. JSON artifacts are not cryptographically signed.
The full research dashboard, tracing export, image pinning, and dedicated experiment tables remain
future work. Literature references in the original proposal have not been independently audited.

No paid inference or Tinker training was invoked; **$0 of Tinker credits was spent**.

## Next tasks, in order

1. Extend fixture contracts and oracle tests to additional dependencies, alternate workflow families,
   in-flight navigation/autosave, independent reactive collaborators, and finite-horizon ambiguity.
2. Add persisted checkpoint/replay schemas, explicit semantic state-difference/causal-edge analysis,
   multi-seed runs, and adaptive-policy support while keeping oracle data out of observations.
3. Implement Gate 4: valid scenario genomes, equal-budget random baseline, pyribs MAP-Elites,
   verified boundary-pair emitter, and bounded minimization; retain unknown/invalid cases.
4. Build leakage-tested observable/latent datasets and a structured critic before Tinker work.
5. Inspect current Tinker API/model availability, prepare a tiny training config and cost estimate,
   and obtain explicit authorization before spending credits. Then implement/evaluate the shield.

At the next session, read the required documents and Git status first. Reuse these tested foundations;
do not restart the architecture or present the remaining research milestones as already complete.
