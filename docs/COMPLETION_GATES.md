# Completion gates

These are the completion plan's Gates 0–10. The historical seven-gate plan used different numbering:
its Gate 3 meant narrow recovery, not an LLM agent.

| Gate | Status / evidence required |
|---|---|
| 0 — Reproducibility | Passed local/clean-clone Linux reproduction on dcc4d6b; v0 and sprint evidence archived. Remote CI and full image digest pinning remain outstanding. |
| 1 — Validity | AC-001 certifies seven checkpoints. AC-002 uses field CAS and two-browser same-value/ABA tests. 88 tests and seven-branch demo passed locally and in Linux. |
| 2 — Oracles | AC-003 adds explicit contracts for review, priority and status, with planted positives, negatives, conflicts, unknown/censored and false-clean tests; 24/24 pilot cases passed in both environments. |
| 3 — Adaptive LLM | Coded and tested with observable test doubles in the dirty checkout; fresh P0 suite has 122 passing tests. Both archived live Gemini batches are invalid (0/12 fully valid cases). Live gate remains unmet. |
| 4 — Recovery baselines | Three bounded conditional witnesses exist for oracle validation. Comparative baselines and exact enumeration remain unfinished. |
| 5 — Evolution | Not started; no discovered/minimized archive or equal-budget comparison. |
| 6 — Dataset/structured model | Not started; no held-out prediction result. |
| 7 — CRBL | Not started; paid Tinker work requires approval. |
| 8 — Shield | Not started; no learned prevention or staging guarantee. |
| 9 — Comparative evaluation | Not started; preregistration is a draft. |
| 10 — Research release | Offline explorer exists; scientific plots, paper and full release remain unfinished. |

Executed checks are recorded in `PROGRESS.md`. The three-family oracle pilot is backend-only,
not multi-family browser/adaptive replay. Passing it permits the next gate, not safety/novelty claims.

P0 audit (2026-11-22): fresh seven-branch Chromium/PostgreSQL demo
`afa078d8f51844ba8299ddef897c2962` and 24-case backend oracle pilot
`cf24751ccc8b429499f979c38c12ed95` passed. The historical 88-test record above remains a
statement about its committed revision; 34 later tests account for the current 122. See
`../research_ops/P0_EVIDENCE_AUDIT.md` for hashes, failures, feature ledger and uncertainty.
P0 is stopped at mandatory human review. No C1/C2/C3 or held-out gate has passed.

P1 continuation: P0 review was accepted by the user's P1 instructions. P1A local validation
passed (184-case full suite plus final targeted tests; three HTTP-mock cases/36 branches).
The specifically approved $2 private Modal attempt created the pinned endpoint but never
reached inspectable readiness before its startup limit. Zero model calls/live tasks/replay cases
were attempted. Endpoint stop and proxy deletion are verified. Gate 3 remains unmet; see
`../research_ops/P1_FINAL_REPORT.md` and the retained infrastructure failure artifacts.

CurrentP1 amendment: full200tests pass. Both9B deployments stopped before live readiness;0generation, no live gate passed. Separate4B preparation passed locally; proposed1decision diagnostic needs newapproval. See P1_MODEL_EVALUATION.md and STATE.json.

## Current checkpoint — 2026-11-23 UTC (supersedes pending proposals above)
Current212-test suite passes. Live4Bv3 has11validdecisions, smoke and single-task PASS, two-action
FAIL; no live replay. Gate3 remains unmet; no collection/learning unlocked. P2local backend pilot
48execution-valid/36known/6UNKNOWN/6CENSORED with all48expectedmatches supports only bounded fake
notification/fee obligations. All48primary certificates and3delayed follow-ups recompute. This local
prerequisite does not complete master-roadmap liveP2 or comparative/held-out gates. All paid approvals
closed; user endpoint retained atmin0/idle0. See research_ops/P1_FINAL_REPORT.md and P2_FINAL_REPORT.md.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

Current gates override stale historical statuses above. P1C PASS within preregistered hybrid simple-task
scope (12/12 branches), multi-action limitation unresolved. P2/P3 PASS bounded backend/formal audits.
P4/P5 PASS comparison execution, H1 targeted advantage NOT SUPPORTED. P6/P7 PASS dataset/leakage checks
and locked execution, H2 primary contrast zero; fixed-tree secondary improvement only. P8/P9 PASS
enforceability/evaluation execution; learned advantage over timer NOT SUPPORTED. P10 paper/artifact
DRAFT COMPLETE; publication novelty INCONCLUSIVE. Bounded study complete=true, broad research
complete=false. No stronger conclusion follows from tests or unused credit. Final holdout opened
once; never tune or threshold-select on it.
