# Same-execution evaluation comparison — derived v2.1

Population: all102 archived planted PostgreSQL backend cases,12UNKNOWN/12CENSORED retained;78 determinate score comparisons. Same source seeds and sibling modes remain grouped. No population confidence interval is assigned to exhaustive authored fixtures. No model calls. Raw labels unchanged. w0/w0b failed on adapter serialization/envelope handling and are preserved; w0c's goal-only safe score is superseded by v2.1 because actual current obligations must hold at completion.

- local_rollback_success__vs__current_state_recoverable: 39 disagreements /78 determinate, 24 unresolved.
- local_rollback_success__vs__full_history_contract_recoverable: 42 disagreements /78 determinate, 24 unresolved.
- local_rollback_success__vs__prevention_feasible: 0 disagreements /0 determinate, 102 unresolved.
- local_rollback_success__vs__safe_task_complete: 39 disagreements /78 determinate, 24 unresolved.
- current_state_recoverable__vs__full_history_contract_recoverable: 3 disagreements /78 determinate, 24 unresolved.
- current_state_recoverable__vs__prevention_feasible: 0 disagreements /0 determinate, 102 unresolved.
- current_state_recoverable__vs__safe_task_complete: 6 disagreements /78 determinate, 24 unresolved.
- full_history_contract_recoverable__vs__prevention_feasible: 0 disagreements /0 determinate, 102 unresolved.
- full_history_contract_recoverable__vs__safe_task_complete: 3 disagreements /78 determinate, 24 unresolved.
- prevention_feasible__vs__safe_task_complete: 0 disagreements /0 determinate, 102 unresolved.

The three current-recoverable/full-unrecoverable cases are capability expiry at seeds7,19,31. Their independent issuance receipts persist; external access is not inferred. Local state restoration can conceal notification, fee, deadline and authority residuals. Conversely a currently un-restored state can admit an alternative strategy. The definitions are A source business-state rollback, B finite fixed-time feasibility, C full history-aware feasibility, D causally witnessed prevention, E actual safe completion. B/C/E are not interchangeable success scores.

Prevention remains null in all102 backend projections: these post-recovery logs do not by themselves give an admissible future intervention witness. Absence of a receipt is not positive evidence of prevention. Paired operational qualification supplies prevention witnesses for its separate cases, not retroactive fill-in of these records.

No policy ranking is estimated from backend mode labels; they are controlled recovery cases rather than randomized policies. The separate unchanged UndoBench DEV baseline study does provide a concrete scoring/ranking comparison. See UNDOBENCH_EXTERNAL_VALIDATION.md.

| Same execution | Local rollback | Current recoverable | Full-history recoverable | Actual safe completion |
|---|---|---|---|---|
| Expired child, prohibited issuance recorded, task complete | Yes | Yes | No | No |
| Expired child with separately witnessed prohibited read (regression) | Yes | Yes if no current residual | No | No |
| Refunded principal but fee burned | Yes possible | No under fee contract | No | No |
| Task values reverted after notification received | Yes | No under observation contract | No | No |
| Unrestored owned state, no history violation, alternative repair exists | No | Yes | Yes | No until actual obligations satisfied |
| Collaborator ownership prevents allowed restoration | May fail | No under fixed ownership API | No | Depends on complete actual contract, never inferred from description alone |

These measurements expose definition sensitivity. They do not establish that history-aware evaluation itself is new. The primary external benchmark already records final-state and effect-history predicates; the incremental novelty claim based on their disagreement is rejected.
