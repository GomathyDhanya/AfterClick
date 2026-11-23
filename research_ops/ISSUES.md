# Issues

P0-01: 88 versus 122 test/document drift — owner Codex, audit pending.
P0-02: two invalid Gemini archives — owner Codex, raw journal diagnosis pending; no paid retry.
P0-03: one shared notification mechanism — known scope limit, not three independent mechanisms.

## 2026-11-22T23:49:40.712741+00:00 — classifications and reproduction
- P0-01 RESOLVED: fresh 122; archived 88 retained with no removed test identities. Added cases:
  tests.agent.test_policy=16, tests.replay.test_semantic_alignment=15, tests.browser.test_adaptive=3.
  Repro/lineage: raw/tests.xml and raw/analysis-v2/tests_delta.json. Owner: Codex.
- P0-02 OPEN / provider availability and uncertain accounting: each archived batch first fails on
  generateContent HTTP503, then generation freezes. Raw reports/journals copied under raw/historical;
  traces and hashes in raw/analysis-v2/historical_live_audit.json. No provider root cause inferred.
  No paid rerun authorized. Remediation prerequisite: local adapter mocks, then separately approved
  priced smoke. Four completed generations, six reserved generation attempts total; journal rows
  include pending/final entries and failed preflight calls, so row count is not request count.
- P0-03 OPEN / scope: notification receipt is one mechanism across three workflow families.
  Planned P3 webhook/export sinks are not implemented; no mechanism/OOD evidence exists.
- P0-04 RESOLVED / local prerequisite: initial PostgreSQL connection refused. Captured environment
  failure; `docker compose up -d --wait db` then environment-recheck passed. Existing app records not reset.
- P0-05 OPEN / intermittent browser clock: archived second run priority-escalation seed7 lost_ack
  fails `Clock.pause_at: Cannot fast-forward to the past`. 50ms controlled local probe did not
  reproduce; assertion failed and negative trace retained in raw/clock_probe.log. No repair claimed.
  Fixed-fixture suite/demo passed. Reopen a bounded clock diagnostic if it recurs; do not hide it.
- P0-06 OPEN / evidence-label scope: legacy review verifier trusts irreversible annotations, whereas
  versioned contract verifier checks matching receipt/history. Do not silently relabel legacy data.
  New dataset labels require versioned witnesses and separate event-time/censoring QA in P4/P6.
- P0-07 OPEN / direct adapter visibility: public runner construction is allowlisted and tested;
  GeminiPolicy.decide accepts arbitrary dictionaries from direct callers. No raw/hidden sentinel
  reached the tested browser-policy boundary. A direct-call fail-closed schema is a P1-local prerequisite,
  not an already achieved P0 guarantee. No risk predictor exists to validate yet.
- P0-08 documentation repaired: README, docs/COMPLETION_GATES.md, docs/ADAPTIVE_REPLAY.md and
  docs/REPRODUCIBILITY.md now distinguish coded/tested harness from invalid live results and
  new $0 work from historical estimated Gemini usage. Historical progress remains append-only.

## 2026-11-23T00:46:17.580575+00:00 — P1 issues
P1-01 local adapter boundary/accounting: coded/tested; live endpoint compatibility unmeasured.
P1-02 fixed credential echo serialization: safe journal and embedded policy records, regression passed.
P1-03 preflight omission: proxy token must exist before authenticated endpoint create; first failure
retained. Temporary token creation was private; token/file deleted after attempt. Next run must
finish proxy setup before deployment timing; no credentials in artifacts. Owner Codex.
P1-04 startup unready: pinned authenticated endpoint ep-q7N7iwcaFpWA2jF35AqgqK stayed in managed
provisioning/download/OCI-unpack; app/server/service_url null. Initial window was partly consumed
by prerequisite repair, so normal cold-start/model cause unknown. Endpoint now stopped.
P1-05 fixed cleanup omission: CLI stop required --yes; TTY wait timed out, pipe aborted. Approved
dashboard stop succeeded; later --yes reported already stopped. Active endpoints[]; explicit
noninteractive/finalization/deadline tests3passed. Repro `.venv/bin/pytest tests/agent/test_modal_lifecycle.py -q`.
P1-06 usage cap$2 saved; net spend dialog showed Default$0 and disabled Save for unchanged0.
Effective default0 retained, custom0 NOT saved. No budget relaxation. Current credit$29.97.
P1-07 live phase remains unmet; prior approval closed. No paid retries or P2 data/training allowed.

## 2026-11-23T01:40:20.259832+00:00 — v2 closure and diagnostic instrumentation

P1-04 remains OPEN/root cause unknown: clean240s9B provisioning timeout reproduced in v2;
no explicit runtime error or resource allocation recovered. Owner Codex; raw v2 preserved.
P1-08 FIXED stale state/placeholder analysis: v2 finalization verified; STATE now waiting approval,
endpoint count0; full analysis/cost denominators written. No model weakness inferred.
P1-09 OPEN log observability: post-stop provider logs expired. New controller captures startup logs
while provisioning; missing logs retained. Local negative tests pass; actual platform logs untested.
P1-10 PREPARED4B arm only: exact revision/license/catalog/template saved; startup/GPU/schema remain
unmeasured. New approval required; no browser/replay/training unlocked.

## 2026-11-23T02:13:49.023612+00:00 — P1-11 intervention feedback leakage
Legacy public_history passed suppressed status to the model. Structured allowlists alone did not catch this value-level disclosure. New opt-in blinded suppression acknowledges completed while retaining raw Gateway intervention; new public synthetic adapter rejects explicit suppressed feedback. Historical mocks retain their original scope and defaults; no live result relabeled. Regression/live-blinded validation pending.

## 2026-11-23T06:14:26.547561+00:00 — latest issues, owner Codex
P1-11 leak: new blindedmock tests12branches pass; no new liveblindedreplayyet. Historicalunblindedmockscope unchanged.
P1-12 readargumentcontract: v2invalid1/1; versionedconditional-v2 repairpasses11/11liveparses but taskvalidityseparate. Runtimeparserunchanged; no retrospectivefix.
P1-13 OPEN live multiactionstagnation: reproduce saved8-stepv3multi_action_task/report.json; sevenrepeatsalready-satisfiedDescription; Prioritygoalnevermet. Missingstate/cacheexcludedby11recordedreplays; planning/grammarunresolved. No paidretryapproval.
P2-01 directproviderclockconsistency FIXED postprimary: atomicpostingclockadvance;5QAchecks/full212pass; originalprimaryfinalstatesalreadyconsistent, frozenrawretained.
OPS-01 billingdelayed/nonmonotonic: CLIcredit1.42vsUI1.24; maxobservedusedforadmission. Exactprojectinvoiceunknown.
OPS-02 broadhelperlint: unchangedresearch_ops/scripts/modal_smoke.py import/formatfindings; preservedwithoutreformatorexecution. Scopednewsource/tests/helperspass.

## 2026-11-23T16:52:15.000275+00:00 — localcheckpoint/test findings
RISK-01 FIXED: freeze paths relativevsabsolute after40completefits. Added seal-only recovery; no retraining orheldoutaccess.
RISK-02 FIXED newtest expectation: prefixquota is acap,not aminimum. Lastrequestauthorized, so19denialsappropriate; testnowasserts19andpreservesgoalconstraint. Controllercodeunchanged.
RISK-03 LIMITATION: exploratory metric fit_seconds includes cumulativebundlefit+evaluation, notisolatedpermodeltraininglatency. Useoverallphaseelapsed only; do notclaimpermodelcostcomparisons.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

Resolved: final documentation drift (212/235→239 tests; prior closed per-run authorizations versus
latest standing mandate); scientific dependency group added to scripts/check.sh. P6 freeze-path
failure repaired without fitting again, original error retained. Incorrect quota-test expectation
corrected, no controller change. P1 v2 trial raw_reference strings used a nonexistent nested
report path; original records preserved and explicit reference-corrections.json supplies actual
counterfactual/<branch>.json locations. v1 lacked top-level branch journals; reconstructed audit
rows are labeled post-execution and grounded in saved branch files.
Open: multi-action live-policy failure, one-mechanism final scope, narrow fixed laws, model-based
labels, shared-developer oracle risk, no organic-error estimate, publication novelty unresolved.
Owner: next research session. Do not fix scientific limitations by tuning on the final set.
Legacy research_ops/scripts/modal_smoke.py has unrelated existing lint/style findings and is
preserved unchanged; it is not part of the no-cost reproduction entry point.
