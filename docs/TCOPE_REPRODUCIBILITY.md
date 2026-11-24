# Reproducing the additive live-agent timing study

The original bounded study and observability papers remain unchanged. The additive manuscript is `paper/TCOPE_PAPER.md`; its locked specification is `research_ops/TCOPE_FINAL_FREEZE.json`. Confirmation artifacts are `artifacts/research_runs/t9-locked-native-confirmation-v1` and the eight child run IDs in its protocol. Development uses t1/t3/t4 and t6 controller runs, including failed and repaired attempts.

## Saved-evidence reproduction — no paid requests

From the repository root, with the existing locked research environment:

```sh
.venv/bin/python research_ops/scripts/verify_evidence.py
.venv/bin/python research_ops/scripts/verify_observability.py
.venv/bin/python -m research_ops.scripts.reproduce_tcope --output /tmp/afterclick-tcope-reproduction
```

Choose a fresh output directory each time. The reproduction command verifies frozen source and sealed child/cohort files, then regenerates development and confirmation tables, source-paired uncertainty, architecture, timing and computation figures. It reads saved raw model outputs and certificates. It never calls Modal, loads a model, opens a new evaluation set or rewrites an archived run. Do not execute a child lifecycle to reproduce a table: a launched run cannot be reused, and new paid samples require the standing safeguards and a separate protocol.

## Local execution checks

Use `uv sync --locked --group research` when recreating the Python environment; retain the committed frontend lock/build and install the matching Playwright Chromium. The frozen environment records exact versions (Python 3.11.14, Playwright 1.65.2/Chromium 159.0.8154.6, PostgreSQL 17.7, ModalCLI 1.6.4); different environments are replications, not identical historical executions. Follow `docs/REPRODUCIBILITY.md` to start the real local PostgreSQL service. All integration tests create isolated `ac_*` schemas.

```sh
.venv/bin/python -m pytest tests/tcope -q
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
```

These tests use controlled local services and mock model responses; they are not new live Qwen samples. Some tests run actual Chromium, PostgreSQL and loopback HTTP workers. Run them when no paid live experiment is active to avoid confounding the wall-clock workload.

## Data and unit of analysis

Each confirmation child starts a new actual Qwen source trajectory, freezes its earliest real proposed browser action, and runs seven dependent controller suffixes from that checkpoint. Primary rows have `role=primary_controller`; `source_parent` and `public_belief_forecast` rows are separate denominators. Forecasts use at most two fresh model turns and may be horizon-censored; they are not complete independent tasks. Cached proposals and imposed controller actions do not count as new model decisions.

`model_calls.jsonl` retains started/finished HTTP requests, known usage and provenance. `requests.jsonl` indexes requests; raw responses and native tool IDs remain in the per-run journals. `oracle_certificates.jsonl` links independent SQL/receiver checks. World reports retain event times and immutable receipts. Failed, invalid, censored, unknown and unattempted conditions remain visible. Same-source siblings stay in one partition. Eight confirmation sources span four familiar mechanisms with instance/timing shifts; they do not demonstrate unseen-mechanism generalization.

## Timing and financial interpretation

Scheduled eligibility D, actual dispatch/ticket F, external receipt E and public acknowledgment A are distinct. Clone/tool/browser work contributes to deliberation wall time; raw inference latency is recorded separately. A failed implemented recovery is not proof that every physically possible recovery is impossible. The online controller never sees actual hidden schedules or private oracle grades.

All costs are approximate account changes or conservative finite-runtime guards, not isolated invoices. The fixed endpoint/revision, output limits, single-request concurrency, zero retries, total wall deadline, $1 child/$8 cohort ceilings, original $20 additional project ceiling, $8 reserve and effective $0 cash limit are recorded in protocols and the spend ledger. Every launched child must restore min 0/ max 1/ buffer 0/ idle 2 and verify zero containers. No server or endpoint deployment is part of reproduction.
