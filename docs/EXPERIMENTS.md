# Experiments

## Current executable experiment

**Data type:** measured executions of a synthetic planted fixture. No model inference is involved.

Contract: `fixtures/tasks/description-review.json`. The goal oracle independently checks committed
TASK-42 description contains `API v2`. The extra review is outside this contract's authorized scope.
Successful suppression supports omission **for this fixture**, not a population necessity label.

Fixed variables: seed 7; backend worker delay 100 logical ms; notification delay 100 logical ms;
browser debounce 600 browser ms; description prefix; fixture; recovery primitive; horizon 300 backend
ms. Browser and backend time are separate. Browser prefix is navigate, fill description, settle and
publish. Selected action is `Click("Mark reviewed")`, ID `a0003`.

| Branch | Selected action | Recovery start | Purpose |
|---|---|---:|---|
| execute | execute | none | Original future |
| execute_placebo | execute | none | Reconstruction placebo |
| suppress | suppress | none | Counterfactual reference |
| suppress_placebo | suppress | none | Reconstruction placebo |
| early | execute | 99 | Cancel before workflow runs |
| late | execute | 200 | Compensate after observer receipt |
| conflict | execute | 150 | Independent same-field write; require abstention |

Recovery unit/integration tests additionally cover t=100 and t=199 (derived readiness/notice exists,
delivery pending), t=250, independent priority edits, uncertain writes, censored horizons, and a
deliberately forged snapshot restore. The latest measured evidence lives in `artifacts/demo/`.

The conflict branch has two verification times. At t=150, the independent oracle verifies the
ownership conflict and preservation of the collaborator edit. Recovery abstains. At t=300, the
uncancelled job has delivered its notice, so the final certificate can additionally prove
irreversibility. A conflict at the attempted recovery time does not imply the remaining future is safe.

## Evidence and exclusions

All six matched branches must have equal checkpoint evidence. Both placebo outcome hashes must
match. The conflict branch is a separate deliberate collaborator intervention. Invalid and failed
branches are saved and cause a nonzero demo exit. The fixture reports goal difference and selected
semantic effects; it excludes `outbox.published` from material-effect counts. It does not count HTTP
spans as separate mutations. Provenance parents are recorded separately from the intervention claim.

The verified pair changes recovery-start time; it does not establish a global minimum or search
discovery efficiency. It is a **latent pre-action risk case**: identical pre-action observations lead
to different recovery outcomes because the controller waits different lengths of time. Do not turn
these identical inputs into contradictory deterministic ranking labels.

Version counters, audit history, and browser SSE receipts are excluded from business recovery distance.
They remain in the raw artifact. Delivery to the scripted observer is explicitly prohibited history.

## Planned preregistration before generalization experiments

Keep the original research specification's 12 task families. Only description/review, lost/delayed
acknowledgements, concurrent edits, dependent readiness, and delivered-notification mechanisms have
working tests; they are not yet 12 evaluation templates. Add independent task contracts, planted
causality checks, invalid-case accounting, and held-out workflow partitions before collecting data.

E1: intervention validity against planted dependencies and null effects. E2: equal execution-budget
random, coverage-guided, GA, MAP-Elites, boundary-targeted, and minimized-pair searches. E3: equally sized
training sets with strict workflow-family holdouts and observable/latent separation. E4: shield
outcomes at matched task-success/coverage levels. E5: legitimate-edit preservation versus naive undo
and snapshot restoration. None of these comparative evaluations has been run.

Prespecify goal equivalence margin (current contract: 0.05), recovery criterion, horizon, seeds,
sample size, exclusion policy, model settings, and execution budget. Estimate necessity and harm
with paired trials; use task-level clustered bootstrap confidence intervals and appropriate paired
tests. Calibrate temporal risks with AUROC, Brier scores, calibration and risk–coverage curves.
Report unresolved/censored cases rather than converting them to failure labels. Do not claim
equivalence from one successful suppression, significance without tests, or improved safety from
offline classification alone.
