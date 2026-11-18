# Completion gates

These are the completion plan's Gates 0–10. The historical seven-gate plan used different numbering:
its Gate 3 meant narrow recovery, not an LLM agent.

| Gate | Status / evidence required |
|---|---|
| 0 — Reproducibility | Passed local/clean-clone Linux reproduction on dcc4d6b; v0 and sprint evidence archived. Remote CI and full image digest pinning remain outstanding. |
| 1 — Validity | AC-001 certifies seven checkpoints. AC-002 uses field CAS and two-browser same-value/ABA tests. 88 tests and seven-branch demo passed locally and in Linux. |
| 2 — Oracles | AC-003 adds explicit contracts for review, priority and status, with planted positives, negatives, conflicts, unknown/censored and false-clean tests; 24/24 pilot cases passed in both environments. |
| 3 — Adaptive LLM | Not started; next sprint. Fixed/adaptive continuations, null/placebo controls, usage records and leakage tests required. |
| 4 — Recovery baselines | Three bounded conditional witnesses exist for oracle validation. Comparative baselines and exact enumeration remain unfinished. |
| 5 — Evolution | Not started; no discovered/minimized archive or equal-budget comparison. |
| 6 — Dataset/structured model | Not started; no held-out prediction result. |
| 7 — CRBL | Not started; paid Tinker work requires approval. |
| 8 — Shield | Not started; no learned prevention or staging guarantee. |
| 9 — Comparative evaluation | Not started; preregistration is a draft. |
| 10 — Research release | Offline explorer exists; scientific plots, paper and full release remain unfinished. |

Executed checks are recorded in `PROGRESS.md`. The three-family oracle pilot is backend-only,
not multi-family browser/adaptive replay. Passing it permits the next gate, not safety/novelty claims.
