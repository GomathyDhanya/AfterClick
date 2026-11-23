# Model-in-the-loop sprint audit (2026-11-23)

Execution checkout: `86a2731dc81d3f6b2f18a4e6bddbe5e27f3e691e` plus additive, protocol-hashed uncommitted sprint files. Initial user-owned untracked ZIP and `research_ops/scripts/modal_smoke.py` preserved.

| Capability | Status before live pilot | Direct evidence |
| --- | --- | --- |
| Legacy structured JSON policy | preserved, prior tested | `afterclick/agent/modal_policy.py`, original seals |
| Legacy native tools | preserved, n=1 prior live task | `afterclick/extensions/native_tools.py`, `i1-format-pair-v1` |
| Natural-only task boundary | coded / offline tests passed | `afterclick/model_sprint/policy.py`; rejects nonempty public goals and private extras before HTTP |
| Real model/tool causal attribution | coded / offline tests passed | `afterclick/model_sprint/gateway.py`; actual model/revision/tool ID in action source; no deterministic action counted live |
| Asynchronous worker during agent execution | coded / PostgreSQL+Chromium mock tested | `afterclick/model_sprint/driver.py`, existing `create_app(auto_tick=True)`; actual browser timers; receipts can occur before agent stop |
| Private independent completion/effect oracle | coded / offline tests passed | `afterclick/model_sprint/oracle.py`; durable receiver/event consistency, exact task state, unauthorized writes, required action ordering |
| Nominal natural Qwen competence | not yet established | registered `s1-natural-qwen-pilot-v1`; 12 tasks / six source pairs |
| Counterfactual live continuation validity | not established | world/transcript checkpoints recorded by new driver; no certified new branching result yet |
| COPE comparative or held-out advantage | proposed only | conditional on pilot, strong prior overlap with SURE-Act and Cordon |

Recorded offline command: `.venv/bin/python -m pytest tests/model_sprint tests/agent/test_native_tools.py tests/agent/test_finance_supervisor.py -q --basetemp=artifacts/research_runs/s0-natural-driver-offline-v1/raw/test-worlds` → 19 passed, 1 existing deprecation warning, 12.00 seconds. Do not rerun into that sealed raw directory; use a fresh pytest base directory.

Frozen studies: before new registration, `.venv/bin/python research_ops/scripts/verify_observability.py` checked 32 seals / 2,537 paths with no mismatch. Existing scientific code and frozen outcomes remain unchanged. Their synthetic results cannot substitute for this live study.
