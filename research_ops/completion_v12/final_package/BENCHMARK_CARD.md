# AfterClick v12 benchmark card

## Intended use and scope

A constructed benchmark of permission-sensitive, asynchronous application work. It measures the conjunction of legitimate task completion and permitted effect history. It is not an evaluation of arbitrary websites or a formal safety guarantee for an open environment. All externally observed effects are synthetic HTTP services and PostgreSQL records; no actual customer notification, disclosure or purchase is performed.

## Cohort

There are 288 contracts: 72 DEV and 216 TEST. Six families (access migration, cross-team approval, customer release, incident response, resource orchestration and retention/export) cross three complexity levels and two applications. DEV has two variants and TEST six variants in each of 36 cells. L1/L2/L3 require 8/13/21 business operations. Structural metrics are in every contract. Authoring uses compositional operators and six policy vocabularies, with 24 layouts overall. DEV and TEST do not have identical layouts, but share operators and policies. This is not 216 independent human-authored business ontologies.

## Application separation

FlowBoard uses work items, dependencies, approvals, readiness and an outbox in the existing business model. OpsConsole has separate work-order, signoff and asset tables, API, UI and worker logic. Their experiment audit, browser gateway, native-tool protocol and receiver infrastructure are shared. Each trial uses a fresh isolated `ac_*` PostgreSQL schema and receiver namespace. Real Chromium interacts with visible controls. The independent HTTP receiver persists physical side effects and acknowledgment histories. Snapshot reads are evidence collection only; restoration never rewinds live state.

## Legitimate obligations and choices

Tasks require ordered work, choosing an authorized scope from signed classifications, resolving public ambiguity with Verify, role approvals, preserving concurrent collaborator edits, waiting for or reconciling uncertain external acknowledgments, and restoring named assets or grants. L3 has two external duties with a receipt dependency. Role approvals are phase-specific but are not represented as cryptographically scope-bound grants. Do not infer a stronger authorization model than implemented.

Pending external requests are genuinely approved or prohibited under the signed public policy. Some require a public Verify operation to reveal authority. The experimental schedule is private. Unapproved exfiltration-like synthetic delivery, duplicate effects, wrong scopes and loss of collaborator changes are prohibited. Receipt-backed completion commits can reconcile known external effects idempotently without fabricating another physical delivery.

## Model information boundary

Actors and reviewers receive the visible application projection, documented native tools and their own continuous assistant/tool history. They receive no independent oracle verdict, private expected action or hidden scheduler state. Dynamic observations include current versions and remaining public work. P4 feedback is a public obligation status, not evaluator feedback. API bodies, tool IDs, HTTP outcomes and model outputs are archived. The endpoint temperature is zero and thinking is disabled; repeated contexts may still vary because environment timing and shared serving state vary.

## Oracle qualification

Two full safe browser reference plans were executed per contract: 576 witnesses. A separately written verifier checks these witnesses and rejects 10,944 evidence/obligation mutations. This is independent implementation, not independent human review. The versioned operational oracle is `afterclick/completion_v12/oracle_v2.py`; it accepts receipt-backed idempotent reconciliation that the original oracle falsely rejected. Real DEV counterexamples, original labels and derived corrections remain archived. Qualification evidence and the frozen registry supersede historical `draft`/`verified=false` authoring markers and original oracle metadata in immutable contract files.

## Timing and recovery limitations

Application state is read and updated across separate transactions. A worker can read older authorization before a controller change, and concurrent writers can race. Audit events are recorded inside transactions; their timestamps do not identify exact SQL COMMIT instants or the worker's exact read boundary. Delayed enforcement experiments identify the total effect of a randomized gateway delay in these backends. They do not isolate pure neural inference latency or prove atomic revocation.

Initial source certificates cover quiescent browser/client state, public projection, application/audit state and seeded schedule before inference. They do not certify identical provider caches, GPU scheduling or intermediate environment state. Policy siblings are genuine newly executed continuations from equivalent initial cuts. Intermediate repairability is UNKNOWN unless separately witnessed; safe siblings do not imply an online recovery algorithm. Bounded formal certificates are confined to their explicitly finite models.

## Frozen credit-capped design

See `../proposed_protocol_v4_final_credit_bound/PROTOCOL_FROZEN.json` and `PRE_TEST_DESIGN_REVISION.md`. The primary model enrolls every TEST task with two clean episodes and two stress worlds shared across P0-P3, plus fixed P4/P5 subsets. The larger-model comparison is a 36-task supplementary study, not full model replication. The original prospective counts are preserved and explicitly superseded before TEST. Missing or invalid assignments remain UNKNOWN with full-denominator bounds. Neither low success nor nonsignificant contrasts permit a claim of equivalence.

## Resources and reproducibility

Model generation uses dedicated credit-funded endpoints. Finite job records separate reservations, conservative guard accounting, provider account meter deltas and unidentifiable isolated invoices. Previous financial records are preserved. No cash or fine-tuning is authorized. Local reanalysis needs Python 3.11 with the repository lock; live integration additionally needs PostgreSQL and Chromium. Model evaluation cannot be regenerated without inference; saved-data analysis can.
