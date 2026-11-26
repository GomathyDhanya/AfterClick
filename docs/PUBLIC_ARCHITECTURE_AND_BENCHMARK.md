# Architecture and benchmark guide

## Runtime boundary

- **Applications:** `apps/flowboard-web/` and `afterclick/api.py`; the second application is implemented in `afterclick/completion_v12/opsconsole.py` with separate UI and business tables.
- **Persistence and progressing work:** `afterclick/domain.py`, `afterclick/infrastructure/`, `migrations/`, and `afterclick/completion_v12/benchmark/` implement durable transitions and isolated research worlds.
- **Actor and policy:** `afterclick/agent/` and `afterclick/completion_v12/benchmark/runner.py` coordinate native function calls and controlled experiment execution.
- **Oracle and analysis:** `afterclick/completion_v12/benchmark/oracle.py`, `afterclick/completion_v12/oracle_v2.py`, and `research_ops/scripts/` separate policy proposals from independent outcome checking, graph verification, statistics and saved-data reproduction.

## Experimental units

The v12 task catalog is `research_ops/completion_v12/candidate_contracts_v7/`: 72 DEV plus 216 TEST task contracts, crossing six families, three levels and two applications. An enrollment is a task contract; an episode is a fresh task-world-policy execution; confirmatory statistical clustering is by source task. Policy labels and statuses must never be inferred from filenames alone.

The final pre-TEST registered protocol is `research_ops/completion_v12/proposed_protocol_v4_final_credit_bound/`. The complete assignment table is `research_ops/completion_v12/final_package/FROZEN_MATRIX_RECONCILIATION.csv`. It includes valid, invalid, executed and not-run assignments. Evaluation code and oracle evidence are not interchangeable with human review. All pre-registration revisions and failed/negative branches remain research records.

## Status and boundaries

The immutable acceptance audit reports 2,904 registered TEST assignments, 1,479 terminal records, and 1,425 unexecuted. It identifies missing causal-control arms, lack of exact mid-trajectory counterfactual reconstruction, and imprecise worker-read/SQL-commit boundary information. The suspension-first P5 queue-hold proxy is not equivalent to semantic staging. Figures and papers must not overstate these limits.

For operational detail see [original architecture](ARCHITECTURE.md), [v12 kit](../research_ops/completion_v12/README_START_HERE.md), [manuscript](../paper/v12/AFTERCLICK_V12_MANUSCRIPT.md), and [claim-to-evidence table](../research_ops/completion_v12/final_package/CLAIM_TO_EVIDENCE.md).
