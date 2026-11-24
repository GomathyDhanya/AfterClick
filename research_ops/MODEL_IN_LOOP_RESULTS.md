# Genuine model evidence — closed OECR extension

Historical TCOPE: 221 genuine Qwen3.5-9B calls, 608,107 tokens, 13 source instances. This remains a separate study.

| Run | Generations | Tokens | Attempted continuations | Initial-certificate-valid completed | Invalid completed/attempt | Censored | Unattempted |
|---|---:|---:|---:|---:|---:|---:|---:|
| u1 pilot v1 | 1 | 2,009 | 1 | 0 | 1 harness failure | 0 | 5 |
| u2 pilot v2 | 18 | 42,630 | 6 | 3 | 2 fresh diagnostics | 1 | 0 |
| u4 confirmation v1 | 0 | 0 | 0 | 0 | 0 | 0 | 18 |
| u5 confirmation v2 | 61 | 146,543 | 18 | 12 | 6 fresh diagnostics | 0 | 0 |

New total: 80 calls / 191,182 tokens, eight seeded sources (two pilot, six confirmation), two templates. Fifteen completed source/faithful continuations pass initial certificates: seven original parents and eight faithful counterfactuals. Fresh diagnostics deliberately do not qualify as causal siblings. Initial certification does not prove identical final model trajectories.

The independent confirmation and corrected chronology are reported in INDEPENDENT_CONFIRMATION.md and u7. First-action preservation is supported within scope; improved primary terminal-completion fidelity is unsupported. No irreversible safety benefit, natural-error frequency or cross-mechanism generalization is claimed. All paid runs are closed; no automatic continuation is queued.
