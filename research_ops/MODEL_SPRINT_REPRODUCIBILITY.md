# Reproducing the new natural-agent pilot

Source execution: HEAD `86a2731dc81d3f6b2f18a4e6bddbe5e27f3e691e` plus hashes in s1/protocol.json. The later source commit is a checkpoint, not the executed Git revision. Both previous frozen studies remain unchanged.

Local environment: repository `.venv` / `uv.lock`, existing built `apps/flowboard-web/dist`, Chromium from the pinned Playwright installation, real local PostgreSQL as specified in `docs/REPRODUCIBILITY.md`. Only disposable `ac_*` schemas are created. Do not reset ordinary FlowBoard data. No SDK or model download is required for read-only artifact verification.

Read-only verification, no network or model requests:

```
.venv/bin/python research_ops/scripts/verify_observability.py
```

Regenerate the new descriptive analysis into a fresh output copy (sealed artifacts must remain unchanged):

```
.venv/bin/python research_ops/scripts/reproduce_model_sprint.py --output artifacts/model-sprint-review
```

Relevant offline regression (uses default fresh pytest temporary directory, never sealed raw directories):

```
.venv/bin/python -m pytest tests/model_sprint tests/agent/test_native_tools.py tests/agent/test_finance_supervisor.py -q
```

The s2 diagnostic runner accepts only a fresh registered run with the exact three branches. Add `--diagnostic-replica s2-replica-UNIQUE_NAME` to the reproduction helper to prepare a fresh registered local-only run, copy the old protocol without changing the original, and execute only local recorded/scripted actions. Its zero model calls cannot be counted as new live evidence.

A closed paid run cannot be resumed or retried. `live_sprint.py --run <existing s1> --execute` rejects an already launched run. A new live experiment must be newly registered, pass the applicable scientific gate, refresh provider identity/credit/rate/cap controls and reserve both project/category and $6 sprint envelopes under the persisted ledger lock. Do not edit SPEND_STATE to bypass an unresolved request. No paid resume command is appropriate after this failed competence gate.

Run inventory:
- s0-natural-driver-offline-v1: recorded 19-test offline suite and browser/mock SQL worlds; $0.
- s1-natural-qwen-pilot-v1: 12 real model tasks, 37 generations, 38 tools, raw transcripts/worlds/checkpoints, 12 independent certificates. 4/12 completed; no posthoc repair or hidden-goal coaching.
- s2-comment-commit-diagnostic-v1: one recorded source / three dependent local branches; zero new model calls. Explicit Post succeeds, original finish and read placebo fail.

Spending: $1.20 pilot reservation, about $0.35000157 reported account delta, $0.3961924467537401 conservative ledger charge. Actual isolated invoice is unknown; billing is delayed and approximate. Endpoint restored min0/max1/buffer0/idle2, idle verified. Cash charges reported $0; no endpoint created/deleted/stopped permanently.

The new report is `paper/MODEL_IN_LOOP_PILOT.md`. COPE live branching, comparative controller performance and new held-out evaluation were not completed because nominal competence failed. Preserve this limitation in every downstream use.
