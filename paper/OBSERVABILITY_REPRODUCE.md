# Reproduce the new observability study

Original study instructions remain in REPRODUCE.md; its frozen code/data/results are unchanged.
This supplement uses the same pinned Python3.11/uv research group, PostgreSQL and Chromium.
No new endpoint, paid model request or credentials are needed for numerical reproduction.

```sh
uv sync --frozen --group research
docker compose up -d --wait db
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
.venv/bin/python -m playwright install chromium
.venv/bin/pytest -q
```

The recorded suite passed260 tests/one upstream deprecation warning. Use loopback test PostgreSQL;
all writes use isolated ac_* schemas, with no ordinary FlowBoard reset or live snapshot restoration.

## Saved evidence and figures

Unpack the local extension evidence archive at the repository root. It contains original/new run
records, the final source snapshot, and checksums, without environments or credentials.

```sh
.venv/bin/python research_ops/scripts/verify_observability.py
.venv/bin/python research_ops/scripts/render_observability.py --output /tmp/afterclick-observability-review
```

Use a fresh destination. The renderer only reads saved artifacts: no fitting, SQL, simulator
execution or endpoints. Six PNG/SVG figures and eight CSV/Markdown tables reproduce the delivered
paper/observability-generated files. All model discrimination/calibration metrics remain available
in the complete CSV and raw metrics. Additional all-comparator contrasts are explicitly secondary.

## Bounded fresh numerical repetition

Inspect this dry run first:

```sh
.venv/bin/python research_ops/scripts/reproduce_observability.py --replica obs-review --max-cycles 2 --max-wall-minutes 15 --paid-mode disabled
```

Add --execute to run at most two fixed phases (development then known-protocol confirmation).
It copies versioned protocols, writes checkpoint/registry state under artifacts/reproductions/obs-review,
refuses non-loopback databases and paid mode, and preserves/refuses failed or interrupted replicas.
Reinvoke the same command to resume after a completed phase. It creates no background scheduler.
Never reuse original scientific run directories; both final opening markers refuse automatic reruns.
These repetitions reuse known laws/seeds and are not new untouched tests.

An actual two-phase repetition, obs-check-20261123, completed in this session. Every numerical metric
matched after removing elapsed_seconds; the saved comparison is o5/raw/reproduction-comparison.json.
The paper's main evidence counts exclude this duplicate repetition.

## Evidence units

- i0-native-offline-v1: strict parser/ID/error/leakage/browser tests, initial failure preserved.
- i1-format-pair-v1: exactly one failed-development task per mode, JSON3/native2 generations,
  independent PostgreSQL task/effect certificates, separate native/JSON journals and combined copy.
- o0-critical-diagnosis-v1: read-only audit of the previous study; no new scientific cases.
- o1-observability-development-v1:5120 finite panels/10240 potential-world label evaluations;
  40UNKNOWN/40CENSORED synthetic masks;16 fresh SQL worlds;6144 search queries.
- o2-observability-locked-v1:1536 fresh source clusters in three cohorts; paired controller outcomes,
  verification races and24 fresh SQL worlds in six source clusters;6144 held-out search queries.
- o3-frontier-certificate-audit-v1:118 SQL endpoint worlds/59 adjacent timing profiles/two paths.
  This shared physical audit is outside candidate-query budgets. It does not create59 mechanisms.
- o4-context-ablation-v1:2048 finite development panels/4096 label evaluations; no final access,
  eight fixed additional model fits, no predictor/threshold replacement.
- o5-observability-synthesis-v1: saved-data analysis, figures/paper, known-protocol reproduction check.

Six SQL engineering test worlds and150 property examples are engineering evidence, not additional
independent evaluation sources. Same-source twins share their partition. SQL uses controlled logical
timing and separately implemented parent/child/provider/receipt transactions. It does not measure
real service or review latency. Public cues are static preflight telemetry; age_ms is a configured
initial decision delay, not a feature derived from a future outcome. Prospective cancellation-time
panels may precede that nominal delay because all inputs are configured before dispatch. The modeled
inspector is perfect but delayed. Native browser grounding remains a separate original FlowBoard task.

## Interaction mode

research_ops/INTERACTION_FORMAT.json selects native tools provisionally. The new task driver is
research_ops/scripts/selected_browser_policy.py; make_policy defaults to that mode, with explicit
json_schema available as a baseline. It requires a mock transport or matching bounded live approval
and therefore does not silently launch requests. Existing frozen JSON replay remains unchanged;
native counterfactual12-branch replay has not been validated and is not claimed.

Do not rerun format_compare.py with a closed run or treat its stored approval as reusable.
The original mode comparison sends no reasoning/reasoning_effort: deployed schema does not establish
the supplied reasoning.enabled mapping. No automatic JSON/native fallback or combined formats exists.

## Scope and versions

FROZEN.json in o1 hashes source, protocols and data/model inputs before o2 opening. An initial
checkpoint included mutable stdout; its original bytes/source and AST-only freeze/main repair are
retained. No models or scientific outputs were changed. The original p6 freeze's207 paths still match.
The final source commit is a later reproducibility checkpoint, not the earlier dirty execution HEAD.
No source, paper or data were pushed or publicly released.

Optional repeated certification/diagnostics using the preserved original inputs and fresh outputs:

```sh
.venv/bin/python research_ops/scripts/audit_dispatch_witnesses.py --output artifacts/reproductions/obs-witness-review
.venv/bin/python research_ops/scripts/dispatch_context_ablation.py --output artifacts/reproductions/obs-context-review
```

These default to known-protocol reproduction when an output is specified, refuse an existing output,
and preserve the original118-world/2048-panel runs. The post-run CLI portability change affects output
location only; no frozen scientific model/environment code changed. `--help` was checked; numerical
primary reproduction was actually executed as described above.
