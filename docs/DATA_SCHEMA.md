# Research data schema

The current saved-data implementation is in `research_ops/publication/analysis/`. Compact publication evidence is in `evidence/publication/`; full normalized tables and raw inputs are in the local evidence packages. Historical studies retain their own formats.

## Application persistence

Each live integration/probe world uses an isolated real PostgreSQL `ac_*` schema. FlowBoard stores versioned tasks, dependencies and scoped capability grants. OpsConsole separately stores work orders and assets. Shared infrastructure includes `v12_controls` (version and service state), `v12_outbox` (queued/admitted/delivered/canceled work), `v12_events` (audit entries), `v12_receipts`, `v12_physical_effects` and idempotency request records. Receipt/physical/audit history is immutable under the modeled interfaces. Outbox state is mutable execution state. Snapshot reads are evidence; snapshot replacement is not a live repair action.

## Normalized tables

| Table | Unit and important fields | Interpretation |
|---|---|---|
| `assignments.csv` | Registered assignment; cohort, source, policy, seed, disposition | All 2,904 original assignments, including 1,425 not run |
| `episodes.csv` | Terminal internal episode; `episode_key`, cohort, source, policy, timing regime, status, L/G/F/Y | 1,239 terminal internal episodes; invalid outcomes remain unknown |
| `events.csv` | Episode-scoped event ID, kind, wall time, reported monotonic value, clock domain, JSON payload | Audit and harness domains are distinguished |
| `effects.csv` | Receiver/effect ID, operation/scope, receipt time, physical-content pointer | A receipt is checked against actual persisted synthetic content |
| `obligations.csv` | Contract duty, type, dependency IDs, origin, satisfaction and commit witnesses | Preexisting business/restore duties remain separate from induced debt |
| `model-requests.csv` | Request intent, actor/reviewer role, received/unknown status, known usage, input/response provenance | Requests, received generations and complete trajectories are different denominators |
| `restoration-debt.csv` | Narrow service-reopening triggers and discharges | Original extractor: 547 service duties |
| `duties.csv` | Induced duty ID/type, trigger, dependencies, discharge, observed span, censoring | Independent reconstruction: 547 service reopening plus 70 approved resubmission duties |
| `episode-debt.csv` | Maximum concurrent unit debt, observed debt area, unresolved items | Backend audit exposure only; unequal/censored horizons prevent a naive causal comparison |
| `rq4-refined-ordering.csv` | Effect/admission/control/action identities, commit-return bound and receipt | All 34 late-receipt cases; exact original SQL read/commit instants remain unknown |

Rows with raw provenance contain a repository-relative path, SHA-256 and JSON pointer (or a declared row key). JSON objects/lists inside CSV cells are JSON encoded; booleans use the emitted CSV representation, and empty values do not automatically mean false. The input manifest records parser and plan hashes. Original absolute paths are relocated in the reader without changing original files.

L is native current local completion. G is independently checked legitimate completion. F is nonempty forbidden effect history. Y is G and not F. L and G agree in all observed valid internal episodes but remain different definitions. Invalid and unexecuted outcomes are unknown.

Wall values are epoch seconds; recorded monotonic values are seconds within a qualified application/harness domain. New probes additionally record PID, thread, process clock domain and nanosecond read/lock/commit-return observations. Historical audit insertion is inside a transaction; response return is an upper bound after commit. Do not fabricate exact historical commit/read times or subtract across unestablished clock domains.

Private contract choices, hidden scheduler details, oracle outputs, debt labels and retrospective graph labels are evaluator data. They are not live model inputs. Public signed verification is an application observation. Graph labels distinguish executed transitions, executed initial-cut siblings, witnessed safe alternatives, formal certificates in separate finite models, fixed history barriers and UNKNOWN intermediate states.
