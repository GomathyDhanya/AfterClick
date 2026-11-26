# Graph evidence interpretation

G1 records actual application events, receiver physical commits, browser HTTP requests, model request/response intervals, native actions and terminal outcomes. Edges are limited to explicit operation/effect IDs and recorded program order. Every node has a raw-file hash and JSON pointer. The independent verifier checks raw references, clock order, join identities and graph acyclicity.

G2 joins actual policy continuations from certified equivalent *initial* cuts within the same run/model. It is not an invented replay of a changed response. A successful sibling witnesses a safe alternative under its executed timing; it is not robust against every possible scheduler. No claim of exact mid-trajectory reconstruction is made.

G3 comprises separately exhaustive finite models (256 legacy states and a 141-state temporal game). Their certificates establish only the bounded transition systems actually enumerated. No G3 proof is assigned to a complex browser trajectory.

A terminal forbidden physical-history record is a fixed history violation even when current local state is repaired. A safe terminal result is a realized safe completion. All other states remain UNKNOWN. Missing final state, invalid requests and unexecuted continuations do not establish infeasibility. Intermediate observation nodes carry UNKNOWN reachability. Non-success with a successful source sibling is a conditional observed policy gap; it is not proof that the actor could have recovered from its later state.

Raw model contexts may be long. Graphs index them by path and hash rather than duplicating them. Container wall-clock timestamps describe observation/audit bounds; audit timestamps are not exact transaction commits. Overlapping model, browser and external intervals must not be added as disjoint latencies.
