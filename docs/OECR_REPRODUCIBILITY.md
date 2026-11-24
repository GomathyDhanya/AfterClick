# OECR reproduction

This extension preserves the earlier frozen TCOPE runtime and evaluation. It generates an opt-in frontend under `artifacts/oecr-web/`; it never rewrites `apps/flowboard-web/src` or its frozen `dist`. The environment remains real local PostgreSQL plus Chromium, with isolated disposable `ac_tcope_*` schemas. Snapshot insertion only initializes a fresh counterfactual schema; it is not an online recovery action.

Local checks ($0 Modal):

```sh
.venv/bin/python -m afterclick.oecr.build
.venv/bin/python -m pytest tests/oecr -q
```

Tests default to `/tmp/afterclick-oecr-tests`. To archive a new local run, preregister a new run directory first and set `OECR_EVIDENCE_DIR` to its empty `raw/` subdirectory. Never direct tests into a sealed historical run. Existing u0 logs include failed and interrupted development attempts.

Saved-data analysis (no network/model calls):

```sh
.venv/bin/python -m afterclick.oecr.analyze --run artifacts/research_runs/u2-oecr-qwen-pilot-v2 --output /tmp/oecr-pilot-summary.json
```

The independent post-run oracle reads final SQL records and source checkpoints. For Priority-recording tasks, the target is the label displayed at the original checkpoint. A fresh browser can correctly record its own refreshed label while answering a different decision problem; raw comment content is therefore reported alongside source-referenced completion. Description tasks require preserving the collaborator text and appending the exact requested suffix. Other fields must remain unchanged. Irreversible safety remains null because this experiment pauses the external scheduler during inference.

Live execution is not part of ordinary reproduction. Closed runs cannot be relaunched. A new protocol must freeze tasks, prompt, tools, serializer, oracle, source/dependency hashes, model revision, request/time/token limits and ordering. The lifecycle rechecks financial controls, endpoint identity, resource rate, original allowance, category caps, protected reserve and the new additional ceiling. It uses the existing dedicated endpoint only and restores min0/max1/buffer0/idle2, verifying zero containers. Do not infer authorization from a copied protocol file.

Scope: explicit controlled-clock cut, application-level React state, base field revisions, dirty buffer, debounce remainder, SSE cursor and pending queue, fake external history, and native conversation records. Pending HTTP capture is rejected. A later resolved cut is a different target. DOM equality alone is insufficient, as tested by the dirty-buffer ablation. No arbitrary browser heap, service-worker, local-storage-heavy application, or production rollback claim is made.

## Closed confirmation and corrected analysis

The complete no-network reproduction command verifies every sealed run and frozen source, regenerates original v1 and corrected v2 summaries and checks all four figure files byte-for-byte:

```sh
.venv/bin/python -m research_ops.scripts.reproduce_oecr --output /tmp/afterclick-oecr-resume-01
```

Use a new output directory on every invocation. It refuses an existing directory and never writes into archived runs. u5 is the independently frozen confirmation; u7 is an explicitly posthoc chronology/identity audit. The original v1 analyzer sorts comment rows by UUID; the corrected secondary content comparison uses append-only event IDs. Both remain reproducible, and primary completion/first-action outcomes are unchanged. The corrected figures live in `artifacts/research_runs/u7-oecr-identity-audit-local-v1/figures/`.

Final regression: 305 passed, one upstream dependency warning, 408.27 seconds. Confirmation: 18 completed continuations, 12 initial-certificate-valid source/faithful arms and six intentionally invalid fresh diagnostics; 61 genuine model generations. Do not rerun these closed paid protocols. The report is complete and no paid queue remains.
