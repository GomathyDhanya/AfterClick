# P0 evidence audit — 2026-11-22T23:47:03.934152+00:00

Run: p0-20261122-audit; implementation HEAD 1fa4f02610a4e556b84a3984dc1e650b2b78cca7 (dirty).
App/source manifest: 71b000901e98372a067a8d2e8103f3c112d0c5b85b8eaa0086eeec2f655d9744. No scientific application source was changed.

Question: can the current checkout reproduce its bounded PostgreSQL/Chromium foundations?
Outcome: PASS for the audit checkpoint, not for adaptive live replay or C1/C2/C3.

Executed baseline: 122/122 tests, 0 skipped/failed; one upstream Starlette/httpx warning; frontend
TypeScript/Vite build and Ruff checks passed. Archived sprint JUnit has 88 cases: all remain;
34 added cases are 16 policy/parser, 15 semantic alignment and 3 browser adaptive test-double cases.
Seven real browser branches (afa078d8f51844ba8299ddef897c2962) are valid and all milestone assertions pass.
Backend pilot (cf24751ccc8b429499f979c38c12ed95): 24 attempted, 24 valid reference reconstructions,
0 invalid, 24 expected-class matches. Classification counts: recoverable 9, unrecoverable 3,
conflict 3, unknown 3, censored 3, partial 3. Each family/seed=7 contributes eight cases.
Unknown/censored are oracle outcomes, not invalid reconstruction. They are not safe/unsafe labels.

Certificate rerun: one replay certificate and 24 contract-recovery certificates exactly match saved
results. This reruns the independent evaluator implementation on stored snapshots; it is not an
independent operator replication or a second independently authored oracle. Nine sprint evidence
file hashes match the archived manifest. The new app source hash equals both invalid live archives.

Archived live runs d09833439a904963a00d08278fa83075 and 990e0e825b2a45b3afb5cb1b8fceeff8:
12 scheduled/attempted cases, 0 valid, 12 invalid; 144 branch slots, 4 completed-valid branch records,
140 invalid or source-skipped records. Only 51 branches actually initialized; 93 were skipped because
source traces were invalid. Six reserved generation attempts produced four completed responses and
two HTTP503 failures with uncertain usage. First observed errors are generateContent HTTP503, one
per run. The budget correctly freezes generation afterward. Subsequent countTokens attempts are
not new generation attempts. There is no observed parser/truncation error at the initiating failure;
logs cannot establish why the provider returned 503. The second run also has one browser-clock past-
time error independent of provider errors. Failure taxonomy and full traces are in historical_live_audit.json.

Engineering attempts: seven captured stages, five passed, two unsuccessful. Initial environment
inspection failed because local PostgreSQL was stopped; starting only Compose db repaired access.
A preregistered two-context clock probe (50ms controlled delay) failed its prediction: both legacy
and guarded pause succeeded. Its assertion failure/raw output remain archived. The intermittent
historical clock error is unresolved; no speculative code change or successful repair is claimed.

Most important observation: the deterministic foundation reproduces while live-agent evidence is
still invalid. Rival explanation 1 (test-count drift rather than lost baseline coverage) is supported
by the exact JUnit delta. Rival explanation 2 (provider availability rather than causal reconstruction
causes the first live failure) is consistent with HTTP503 and failed-closed budgeting, but successful
live reconstruction remains untested. The clock trace prevents treating all failures as provider-only.

All three families share one scripted-observer notification receipt mechanism. Selected actions are
planted. No organic error rate, minimal boundary discovery, causal population necessity, learning
improvement, enforceable shield efficacy or novelty is established. The legacy review oracle uses
weaker irreversible-event annotations; the versioned contract oracle additionally requires matching
receipt/history witnesses. Preserve legacy semantics and prefer versioned certificates for new labels.
Raw snapshots are available; certificates are local files, not signed/tamper-proof evidence.

Threats: shared seed/mechanism, planted positive fixtures, correlated branches, bounded horizons,
serialized scheduler, uncontrolled browser transport timing and deliberate backend freeze during
policy deliberation. Fixed development cases do not justify population confidence intervals; no
comparative effect size or calibration estimate was computed. Survival targets have not been
normalized by a P6 label pipeline: absent fields remain null rather than inventing censoring labels.

Cost: fresh model calls 0, Modal $0, Tinker $0. Historical Gemini completed-call estimate $0.001171,
plus $0.0013045 outstanding reservations; these are estimated accounting, not invoices. Actual
applicable Modal remaining credit/account use is unknown. No Modal endpoint was launched/queried.
The local Compose database was started; api/web were not started or reset. No holdout was opened.

Decision: stop for required human P0 review. Preferred next: $0 P1 adapter HTTP-mock preflight.
Do not expand data collection, train, or request paid deployment before that preparation and review.

Reproduce saved analysis without model calls (choose a fresh destination):
    .venv/bin/python research_ops/scripts/analyze_p0.py artifacts/research_runs/p0-20261122-audit --output /tmp/afterclick-p0-review-1
Reproduce the last backend check, preserving new outputs:
    .bootstrap/bin/uv run python -m afterclick.evaluation.pilot --output artifacts/p0-review-pilot
Full recorded commands, durations and log hashes are in raw/*.result.json; immutable protocol and
registry amendments distinguish the initial database failure and negative clock diagnostic.

## Feature status ledger

| Feature | Highest supported status | Evidence |
|---|---|---|
| FlowBoard + PostgreSQL scheduler | tests-passed | afa078d8f51844ba8299ddef897c2962 |
| Field CAS and conditional compensation | tests-passed | cf24751ccc8b429499f979c38c12ed95 |
| Seven-branch scripted browser replay | live-replay-valid | afa078d8f51844ba8299ddef897c2962 |
| Three-family contract oracle (one notification mechanism) | tests-passed | cf24751ccc8b429499f979c38c12ed95 |
| Gemini policy/parser/visible input construction | tests-passed | fresh JUnit / proposed only |
| 12-branch adaptive harness with observable test double | tests-passed | fresh JUnit / proposed only |
| Semantic branch alignment | tests-passed | fresh JUnit / proposed only |
| Live adaptive agent replay | coded | d09833439a904963a00d08278fa83075, 990e0e825b2a45b3afb5cb1b8fceeff8 |
| Distinct webhook/export external receipts | proposed | fresh JUnit / proposed only |
| C1 boundary search and minimization comparison | proposed | fresh JUnit / proposed only |
| C2 mechanism-held-out calibrated learning | proposed | fresh JUnit / proposed only |
| C3 enforceable learned shield comparison | proposed | fresh JUnit / proposed only |
| Post-P0 bounded research-cycle CLI | proposed | fresh JUnit / proposed only |

All features have comparative-validated=false and held-out-validated=false. Live agent replay is
false throughout; the live-replay-valid scripted row explicitly means actual Chromium/PostgreSQL
execution, not live model success. Exact source filenames/SHA256s, test paths and run IDs are in
`artifacts/research_runs/p0-20261122-audit/raw/feature_status_ledger.json`. The manifest includes
full source and lock hashes; raw/source_comparison.json and archive_integrity.json establish lineage.
