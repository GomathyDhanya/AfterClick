# V12 implementation checkpoint — not completed research

The completion kit is copied verbatim here. All 22 supplied checksums pass. The
original v11 working tree was archived before editing; all 584 original files
matched their starting hashes before documentation updates. Branch:
`codex/afterclick-v12-completion-20261125`. No public push or publication.

This checkpoint does **not** contain the full benchmark, frozen TEST evaluation,
new model study, complete statistical analysis, or final v12 paper. The audit
reports those requirements as incomplete. Do not interpret local qualification,
formal examples, or historical rescoring as the requested model evaluation.

## Executed evidence

| Component | Actual result | Evidence |
|---|---|---|
| Existing complete regression | 360 passed, one dependency warning, 690.22 s | `artifacts/research_runs/v12-00-baseline-qualification/baseline-tests.xml` |
| Original integrity verifiers | 91 historical sealed runs; 8,927 / 9,088 checks; zero mismatches | baseline `verify_evidence.json`, `verify_observability.json` |
| Known-protocol reproduction | All six phases executed; numerical metrics equal after excluding elapsed/fit time | baseline `known-protocol-numeric-comparison.json`; `artifacts/reproductions/v12-baseline-20261125/` |
| Timing reproduction | 767 sealed hashes; 42 branches rescored; numerical/PNG reproduction exact | baseline `timing-reproduction/reproduction-report.json` |
| Historical graphs | All 36 frozen confirmation and six supervisor DEV branches; 1,208 nodes / 468 edges / 271 raw files independently checked | `v12-01-historical-graphs-attempt-1/verification.json` |
| Historical atlas | 42 SVG timelines, 266 event-prefix cuts, all six failed branches have safe source-cut siblings | historical graph run `atlas/atlas-manifest.json` |
| Legacy finite solver cross-check | 256 states, 10 repairable, zero disagreements | `v12-02-finite-qualification/summary.json` |
| New temporal finite game | 141 states; exact public-information robust certificates; all results relative to the six-tick model | `v12-02-temporal-formal-qualification/` |
| OpsConsole | Separate schema, business tables, API, UI and worker; two successful 13-action browser plans, 14 rejected mutations per plan | `v12-03-opsconsole-qualification-attempt-4/` |
| Real forbidden OpsConsole effect | Actual unrequested spare consumption rejected by the independent history oracle | `v12-03-opsconsole-negative-qualification/` |
| Controlled actuator delay | All 60 registered trials valid and independently rescored; 17 forbidden branch histories | `v12-04-enforcement-delay-v1/`, `v12-04-enforcement-analysis-v2/` |

The delay experiment has **three legacy fixture structures and six seeded
worlds**, not 60 independent tasks. It deliberately holds an already-correct
recommendation, varies delay and browser/HTTP path, and records real progressing
workers and receiver histories. It contains no model calls. A command ledger
timestamp is recorded inside the transaction; it is **not** an exact SQL COMMIT
timestamp. The analysis preserves that limitation. Local load from other
qualification processes can affect measured timings. No population inference
or pure neural-inference causal claim follows from this experiment.

Every historical graph edge is a recorded key join or a certified executed
source-cut continuation. Undated old native actions are not assigned invented
times. Intermediate cuts have event-prefix hashes, not complete replay-state
fingerprints. Current repair and robust live recoverability remain UNKNOWN.
Finite proofs are stored separately and are never silently projected onto live
trajectories. Successful siblings are conditional witnesses, not an online oracle.

## Commands

Run from the repository root with the existing locked environment. PostgreSQL
17.7 must be available on the configured local URL; each new world uses an
isolated `ac_*` schema. Chromium is real; HTTP receivers bind loopback. All
commands require a fresh output directory and preserve earlier attempts.

No-inference historical graph reproduction and independent verification:

```sh
.venv/bin/python -m afterclick.completion_v12.historical --output /tmp/afterclick-v12-historical-NEW
.venv/bin/python -m afterclick.completion_v12.atlas --graphs /tmp/afterclick-v12-historical-NEW/graphs --output /tmp/afterclick-v12-atlas-NEW
.venv/bin/python -m afterclick.completion_v12.qualify_finite --output /tmp/afterclick-v12-finite-NEW
.venv/bin/python -m afterclick.completion_v12.temporal_model --output /tmp/afterclick-v12-temporal-NEW
.venv/bin/python -m afterclick.completion_v12.analyze_enforcement --run artifacts/research_runs/v12-04-enforcement-delay-v1 --output /tmp/afterclick-v12-enforcement-analysis-NEW
.venv/bin/python -m afterclick.completion_v12.program --output /tmp/afterclick-v12-status-NEW
```

Actual PostgreSQL/Chromium/HTTP qualification, without paid inference:

```sh
.venv/bin/python -m afterclick.completion_v12.qualify_ops --output /tmp/afterclick-v12-ops-NEW
.venv/bin/python -m afterclick.completion_v12.qualify_ops_negative --output /tmp/afterclick-v12-ops-negative-NEW
.venv/bin/python -m afterclick.completion_v12.enforcement --output /tmp/afterclick-v12-enforcement-NEW
.venv/bin/pytest tests/completion_v12 -q
```

The 60-row delay protocol is written and hashed before its first outcome. These
are **local mechanism** registrations. There is no v12 TEST freeze or paid model
queue. The full primary-model plan remains 9,720 executions, plus 8,424 second-model
core executions, subject only to a justified pre-TEST revision. None has run.

## Preserved unsuccessful attempts and limitations

OpsConsole attempt 1 exposed a stale success indicator that let the reference
driver race ahead. The UI now identifies the committed command and disables
controls while pending. Attempt 2 exposed a genuine collaborator version race;
the reference now re-reads public state and explicitly reconciles rejected
commands. Attempt 3 qualified the first oracle; attempt 4 additionally verifies
ordering obligations and seven extra mutation counterexamples. All earlier
snapshots/logs remain. These are DEV repairs before any new TEST exposure.

The first combined post-implementation test collection failed because the new
`test_contracts.py` lacked a package namespace and shadowed the old module. Adding
`tests/completion_v12/__init__.py` fixes collection without changing old tests.
The first delay-analysis attempt reconstructed the wrong contract metadata and
refused a hash-mismatched rescore; v2 uses the exact registered seed, case and
schedule. No trial or outcome was replaced.

The kit's illustrative contract reports dependency depth four, while its
supplied obligation DAG computes to three under the explicit node-depth metric.
The validator detects this; the supplied example is retained unchanged and is
not enrolled as a benchmark task.

The two old c0 timing failures are preserved in
`c0-supervision-local-qualification-v1/raw/full-regression.xml`: an adaptive
browser replay missed suppress/placebo branches, and a supposedly early
fixed-budget intervention permitted a receipt under its two-second deadline.
Both pass in the new 360-test baseline. This does not establish permanent
determinism or justify relaxing assertions. No historical runtime/test changed.

One DEV contract is authored and has reference witnesses, but remains a draft
pending complete benchmark/oracle/complexity review. The other 71 DEV and all
216 TEST slots are not authored. OpsConsole implements resource orchestration
only; its other five workflow families are not implemented. Full P0–P5 study
orchestration, DEV model calibration, source-clustered power, frozen matrix,
stronger-model runs, official external TEST, and the publication manuscript
remain incomplete. No human reviewer is claimed.

## Credits

Latest user authorization: endpoint `ep-Lqp751voQWfhhoZTNXD4Yf`, up to **$18** of
new v12 credit consumption; no cash charges authorized. Historical finance
ledgers remain byte-identical. New model calls / paid compute initiated: **0 / $0**.
Read-only provider billing, endpoint revision, catalog, rates and empty-container
checks are retained in the baseline run. The existing model revision is
`Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
The provider catalog lists additional models; no stronger model was deployed or
evaluated. Availability is not a technical blocker presently established here.

Before paid work, implement the new finite v12 reservation/credit-only launcher,
refresh credit and net-spend safeguards, forecast the complete registered study,
and finish qualification. Do not reuse a closed legacy lifecycle or its old
$20/$5 category caps as new authority. Do not interpret the $18 ceiling as a
promise that the full proposed matrix fits available credit.


Final combined verification: **402 passed**, zero failures, one upstream warning, 661.74 s. All 42 new tests and the original 360 were included. Source checkpoint `4224a75`; no original test/runtime changed. The failed collection attempt remains archived. Full research remains incomplete; no paid v12 requests or TEST outcomes.

Historical failure attribution: `artifacts/research_runs/v12-01-historical-failure-attribution/` reconciles all six unsuccessful archived branches with independent raw-receipt/terminal-state checks: five historical harms and one restoration omission. Timing component causality remains unresolved.
