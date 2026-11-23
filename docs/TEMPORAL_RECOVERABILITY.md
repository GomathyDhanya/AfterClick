# Temporal recoverability: contract and finite model

Let x be the concrete world at logical time t, x^- the reconstructed suppressed-action reference,
C the authorized-state contract, I the independent legitimate changes, and A_t the admissible
recovery operations. Define fixed-time recoverability

R_C(x,t) = exists pi in A_t* such that C(pi(x),x^-) holds and I(pi(x)) = I(x).

The bounded model fixes the clock during recovery. Admissible operations compensate owned source
state, cancel pending external effects and refund captured principal. No operation erases an
independent observer's knowledge, restores a burned fee, revokes a separately delegated child
capability, rewinds a clock or repairs a missed immutable deadline. The foreign-ownership rule
forbids overwriting an independent owner's current field. Multiple operation orders are allowed;
breadth-first finite closure supplies a witness or exhausts every state in this declared abstraction.

This is capability-relative instantaneous recoverability, not universal physical impossibility.
If waiting is permitted, the budget/horizon must be part of a different explicit contract. Automatic
child expiry is an environmental transition, not instantaneous compensation. Current recoverability
can therefore change from recoverable to unrecoverable and back to recoverable. Historical receipt
of an unauthorized effect is a separate absorbing fact; it does not disappear when current authority
expires or principal is refunded. Database restoration alone does not satisfy an external contract.

Four tested recovery obligations are distinguished:

| Obligation | Residual preventing present recovery | Historical interpretation |
| --- | --- | --- |
| Notification | independent recipient observed content | historical observation persists |
| Fake fee | one conserved unit irreversibly burned under API | principal refund is compensation only |
| Delegated authority | child capability remains live outside parent-revocation API | current residual can expire; not permanently unrecoverable |
| Deadline opportunity | legitimate delivery missed an immutable deadline | releasing the lease cannot restore a past opportunity |

These are four obligation classes, not four demonstrated permanently irreversible mechanisms.
Permission expiry is a deliberate nonmonotone control. A mock access receipt uses synthetic data;
no production privilege, payment, disclosure or recipient exists. Additional network transports alone
would not add a new mechanism. The deadline result assumes that the declared deadline cannot be
extended, and does not claim universal impossibility under a richer business policy.

Physical feasibility and epistemic certification are distinct. An oracle may return UNKNOWN when
independent receipts have not arrived, even if hidden provider state would determine feasibility.
CENSORED means the prescribed observation horizon was unfinished. CONFLICT identifies an independent
ownership constraint; PARTIAL describes the attempted recovery, not proof that no admissible strategy
exists. Invalid reconstruction is excluded from causal inference while remaining in denominators.

The finite State contains owned source/pending/principal bits, four external residual bits, foreign
ownership and an independent-work digest. Every recovery edge preserves the digest. Exhaustive closure
checks all256binary states. This is not a bisimulation proof for every FlowBoard state or an arbitrary
real application: projection adequacy is tested against102 saved PostgreSQL cases. Of these63known
positive/negative assertions match; three PARTIAL implementations still have a feasible strategy;
unknown/censored/conflicting cases retain their original epistemic labels.

For prospective prediction define p(a,h | O_t) under a declared mixture of hidden schedules, where
O_t contains only observations available before action and h is a predeclared query horizon.
The following differ: effect time, independent receipt arrival, and information available for predicting
risk. No predictor may receive oracle state, future event time, branch labels, mechanism identity hidden
from the UI, or a post-action feature. Identical visible states with different futures require a
probability distribution, not confident point identification. A survival target for first historical
forbidden effect must not be substituted for nonmonotone recoverability-at-horizon.
