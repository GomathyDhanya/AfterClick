# Unified Modal compute ledger

Updated 2026-11-24T03:22:47.804014+00:00. Original baseline credit28.11; total additional ceiling20; protected credit reserve8; confirmation allocation8. All charges below are conservative guards, not isolated invoices.

| Run | Category | Guard USD | Idle verified |
| --- | --- | ---: | --- |
| p1c-new-endpoint-live-v1 | p1c | 0.360002 | True |
| p1c-new-endpoint-live-v2 | p1c | 0.360001 | True |
| i1-format-pair-v1 | p1c | 0.324502 | True |
| s1-natural-qwen-pilot-v1 | trajectories | 0.396192 | True |
| t1-9b-commit-feedback-v1 | trajectories | 0.362974 | True |
| t3-native-live-branches-v1 | controller | 0.370000 | True |

Guard sum: 2.173671. Account additional highwater: 2.120035; reserve uses the larger, so user-created endpoint/preexisting compute is not ignored. Active reservation: None. Unresolved: False.
No new endpoint or external token API authorized.
