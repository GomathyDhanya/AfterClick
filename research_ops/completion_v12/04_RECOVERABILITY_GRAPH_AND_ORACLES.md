# 04 — Trajectory/effect graphs and defensible oracle bounds

## Why this is necessary

V11 has event provenance, independent service receipts, the bounded 256-state solver, and genuine Qwen branch traces, but lacks a validated end-to-end graph annotating **every agent/control/environment action** with its consequences, remaining obligations, and provable safe futures. Build this as a first-class reusable analysis artifact, not a hand-drawn retrospective figure.

## Two different graph products

### G1: Observed execution/effect provenance graph

A partial-order DAG over facts that actually occurred:
- Agent observation and model decision (model request ID, tool-call ID).
- Browser event, HTTP request, gateway acceptance/denial, DB mutation, job issue.
- External worker eligibility, ticket admission, delivery/consumption, acknowledgment.
- Collaborator actions, task-obligation satisfaction/invalidation, controller recommendation and enforcement.
- Clock-domain and confidence metadata; direct parent IDs and inferred happens-before edges must be distinct.

A G1 edge is grounded by an actual ledger ID, source hash, browser trace, tool response, or receiver receipt. **A merely inferred parent is not proof of a counterfactual causal effect.** Annotate concurrent events when no reliable ordering is known.

### G2: Executed counterfactual and bounded feasibility graph

Nodes represent decision cuts and histories, not just raw screen text. A canonical state fingerprint should include:

`(application + task contract + user-visible/client buffers + database state + pending jobs + authorized tool surface + external effect receipts/history + valid permissions + clock/scheduler state + outstanding obligations + model context hash)`

Edges are one of:
- `OBSERVED`: happened within a recorded trajectory.
- `EXECUTED_COUNTERFACTUAL`: branch created from a certified equivalent cut; effect/oracle independently re-scored.
- `FORMAL_TRANSITION`: generated from fully specified bounded model/action rules.
- `HYPOTHETICAL_UNVALIDATED`: interesting but never counted as evidence of achievable success.

Store graph as JSONL node/edge tables plus Parquet/CSV exports. Provide a visual explorer and static SVG/PDF-ready figures. Attach the exact raw evidence locator and checksum to every node and edge.

## Feasibility definitions (never conflate)

1. **Realized safe completion**: actual executed branch satisfies every legitimate obligation and recorded forbidden-effect constraint.
2. **Witnessed safe continuation**: a real executed sibling from a certified same initial cut safely completed; this proves possible under that observed schedule, not that the agent could identify it in advance.
3. **Bounded existential feasibility**: in declared finite model, **some** allowed action sequence and **some** allowed environmental realization reach safe completion. This is a weak bound.
4. **Bounded robust feasibility**: an admissible **observation-based** controller can succeed across **all** exogenous schedules in the specified uncertainty set. The controller cannot use unavailable hidden futures. Explicitly quantify action/env move order and observation update.
5. **Fixed-history infeasibility**: full historical contract has already been violated by an immutable recorded effect; current-state repair may remain possible.
6. **Unknown**: graph incomplete, action set open, solver timed out, schedule not modeled, or exact replay invalid. A timeout is **not** a proof of impossibility.

Do not confuse `∃ action, ∃ schedule` with `∃ public-information policy, ∀ schedule`. The latter is much stronger. Do not call a hindsight best-of-three policy deployable.

## Formal finite solver

Start with `afterclick/research/recoverability.py`, which only supports three repair operations in a tiny 256-state fixed-clock abstraction. Extend **without retroactively rewriting its historical results**:

- A finite transition system with clearly declared actor, controller, and uncontrollable worker transitions.
- Time-indexed pending-to-committed transitions; asynchronous receipts and scoped cancellation APIs.
- Temporal/ordering constraints and obligation DAG; current-state versus history predicates.
- Backward reachability for finite goal states, game-style viability for specified hostile/benign uncontrollable schedules, and forward executable witness generation.
- Bounded model-checking certificates for negative results: visited-state count, exhausted action set, all successor expansions, horizon, theorem property, solver version/hashes. Distinguish `NO_PATH_WITHIN_HORIZON` from proven closure-based `NO_PATH_UNDER_DECLARED_MODEL`.
- Admissible operation cost/latency budgets, effect scheduling and staging eligibility. If extra downstream compensation API would change the result, specify its absence rather than claiming a universal limit.

Validate the solver on hand-checkable tiny instances, the archived 256-state enumeration, and generated finite cases with trusted brute-force enumeration. Verify any alleged last-prevention frontier through actual deterministic PostgreSQL/HTTP replay at both sides of the boundary.

## Algorithmic baselines and ablations

- Final state only.
- Final state + full history (must include UndoBench-like history, not a straw man).
- Events + action-only sequence.
- Events + action/effect provenance.
- Full time-indexed graph + obligations + admissible actions.

For each, measure: agreement with independent outcomes, recall of recorded effect chains, edge provenance precision, amount of UNKNOWN, time/memory growth, certified bounds/feasible witnesses, and any real decision benefit. Graph construction alone is not an ML advance.

## First validation targets

- Archived Source 05: early harm prevention, incomplete restoration; alternate successful sibling.
- Archived Source 07: notification cancellation frontier.
- Archived Source 11: child ticket admitted during genuine Qwen generation, parent revocation later, eventual read.
- Supervisor DEV access case: valid STAGE returned before ticket admission yet revocation late; separate review versus enforcement.

For each, issue a trace-to-graph comparison and assert that **observed** edges/outcomes match the raw saved records. Then process all existing 36 frozen branches, six supervisor DEV branches, and all new TEST trajectories. Add property-based and mutation tests for clock reorderings, duplicate receipts, missing causal links, and unobservable state changes.

## Recommended graph visuals and metrics

- Four-lane time-synchronized action/controller/worker/obligation diagrams.
- Recoverability frontier map: x=time, y=state/branch, shades represent *witnessed*, *proven*, or *unknown* (not unsupported certainty).
- Safe-option loss: number or proportion of certified admissible safe next actions at each cut, with declared finite action set.
- Distance/cost-to-recovery for feasible states, jointly with deadline slack; do not silently count unavailable actions.
- First point of **historical contract violation**, first point of **lost current preventability**, and first point of **legitimate obligation failure** separately.
- Observed plan equivalence: identical action types but different external effect histories; position and real timing matter.

## Output acceptance

A graph must have a machine-readable schema, visualization, per-edge provenance, independent verifier, semantic/temporal invariant tests, and a justified UNKNOWN category. It is **not complete** merely because it renders a pretty branch diagram.
