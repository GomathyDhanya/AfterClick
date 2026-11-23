# Implementation progress

Updated November 18, 2026. Current scope: completion-plan sprint **AC-001 through AC-003**.
The historical seven gates and the completion plan's Gates 0–10 use different numbering;
`COMPLETION_GATES.md` is the current map. The original session log is in `history/PROGRESS_V0.md`.

## Completed implementation

- **AC-001:** replay certification now requires all seven pre-action checkpoints, including conflict.
  Negative tests mutate/remove the conflict checkpoint. Its deliberate later collaborator action is
  still allowed to diverge. The original report remains unchanged under `evidence/v0/`.
- **AC-002:** migration 0003 adds non-identifying task field counters and project summary ownership/
  counters. Every touched field advances even for same-value writes. Atomic field CAS allows safe
  nonoverlapping rebases; same-field/ABA changes fail closed. The frontend keeps original tokens,
  retains the unsaved draft on conflict, and never substitutes value equality for history.
- **AC-003:** versioned contracts define goals, authorization, forbidden history, preservation,
  fixtures, horizons and interfaces. Independent task/effect/recovery modules cover review/readiness,
  priority/escalation and status/summary. They accept actual state and a validated reference, not
  planner status. Bounded conditional compensation provides real witnesses for each family.
- Historical irreversible arrival is measured from selected-action logical time. Current recovery
  class is a separate target. A Boolean irreversible annotation alone is insufficient: receipt and
  matching history are required. Missing evidence, unobserved horizons and invalid references fail
  closed; false planner claims cannot certify clean state.
- Added a 24-case planted backend pilot with prefix/placebo validation, raw before/after/reference
  states, independent certificates and retained errors. This is not an adaptive browser benchmark.
- Added a clean-clone Linux validation harness with a separate PostgreSQL container, no host DB
  port, no model credentials, retained logs and isolated resource cleanup. CI now runs the pilot too.
- Archived the supplied completion plan and supporting roadmap; added threat model, novelty matrix,
  draft preregistration and the current gate checklist. Existing architecture is preserved.

## Validation and evidence

The original **39 tests passed again** before modification. The complete current local suite has
**88 passed, 0 failed** (one upstream Starlette/httpx deprecation warning). This includes two-browser
same-value/ABA regressions, concurrent field CAS, legacy migration backfill, all-seven-checkpoint
negative tests, and three-family oracle positives/negatives/preservation/uncertainty tests.

Ruff lint/format checks and the TypeScript/Vite production build passed. The committed seven-branch browser demo and all 24 backend oracle cases passed locally and in a
clean-clone Linux container with a separate PostgreSQL instance. Linux also passed all 88 tests,
frontend build, and Ruff checks. All seven final browser-branch hashes match across environments.

Python dependency audit: no known vulnerabilities reported. npm audit still reports four high
entries through the existing picomatch development-tool advisory; no forced downgrade was used.
Raw audit outputs: `artifacts/sprint-python-audit.json`, `artifacts/sprint-npm-audit.json`.

The v0 prototype and original evidence were committed as `34cc1f0` and tagged `afterclick-v0`.
The v0 report's missing conflict checkpoint is explicitly documented; it is not relabeled as fixed.
Current local test evidence: `artifacts/sprint-tests.log` and `artifacts/sprint-tests.xml`.

## Commands executed / reproducible commands

```sh
.venv/bin/pytest -q --junitxml=artifacts/baseline-tests.xml
.venv/bin/pytest tests/replay tests/integration tests/browser -q
.venv/bin/pytest tests/recovery -q
.venv/bin/pytest -q --junitxml=artifacts/sprint-tests.xml
.venv/bin/ruff check afterclick tests migrations
.venv/bin/ruff format --check afterclick tests migrations
npm run build --prefix apps/flowboard-web
```

Release verification commands (executed successfully from clean revision `dcc4d6b`):

```sh
uv run python -m afterclick.replay.demo --output artifacts/demo
uv run python -m afterclick.evaluation.pilot --output artifacts/oracle-pilot
bash scripts/validate-isolated.sh
```

On this host, uv is available through `.bootstrap/bin/uv` or by prepending `.bootstrap/bin` to PATH.
Container validation uses a separate installed runtime and clean local clone. It is not remote CI
or independent third-party reproduction. Both code and evidence revisions must be recorded honestly.

## Files changed

`afterclick/replay/demo.py`; domain/API/schema; migration 0003; React editor; legacy planner counter
maintenance; new `contracts/` and `evaluation/` modules; `recovery/conditional.py`; three versioned
contracts; replay, field-CAS, browser, migration and oracle tests; isolated validation Docker/Compose
and scripts; CI; research/architecture/reproducibility/continuation documentation. Original v0 oracle
semantics and raw evidence are retained separately.

## Limits and next work

No adaptive LLM, search archive, learned critic/shield, comparative recovery baselines or scientific
improvement is claimed. Three families have planted backend oracle coverage; only the original review
trajectory has browser counterfactual replay. The verifier is bounded witness verification, not an
exhaustive feasibility solver. The serialized scheduler, scripted observer and local application
capability model remain explicit limits. Full image digest pinning and remote CI remain future work.

Next sprint: implement an observable-only configurable LLM policy on the existing Gateway, semantic
branch alignment and explicit feedback interventions, then demonstrate valid fixed/adaptive replay
across the three families and multiple seeds. Preserve invalid trials and usage/cost evidence. Do not
start evolutionary learning before those validity gates. Tinker still needs dataset validation,
current API/model inspection, a costed smoke plan and explicit authorization. No paid model calls
were made; no Tinker credits were spent.

All three current families share the scripted notification receipt as their irreversible mechanism;
this is not evidence of three independently discovered irreversibility mechanisms.


## Final release verification

Implementation revision: `dcc4d6b7561eada3eb6cdef754dd38b860c106f7`. All four run manifests record
that revision with `git_dirty=false`. Their implementation hash matches the current code:
`85f156ab8c37f44a662e61ba7db7ae04b28dfd7eea626b31762a5e769061d4d9`.

| Evidence | Run ID / result |
|---|---|
| Local browser demo | `c2c728655fa64917961f8c3b04f792fb`; seven checkpoint/outcome acceptance checks pass |
| Linux browser demo | `e7fed950e3344ff5b11d18a27874b820`; same final outcome hashes for all seven branches |
| Local oracle pilot | `9c9f0a45f3664ad48a20fac37de63f9e`; 24/24 expected classes |
| Linux oracle pilot | `0a15dec54ad14e8da81cfd778480d775`; 24/24 expected classes |
| Full local suite | 88 passed, 0 failed |
| Full Linux suite | 88 passed, 0 failed |

Raw reports, both JUnit files, the Linux log and dependency audits are versioned in `evidence/sprint1/`.
`manifest.json` hashes those evidence files. Original v0 evidence remains separate and unchanged.
The isolated validation database/containers were stopped and removed; the temporary source clone
was retained for inspection. This is a separate Linux environment on the same Docker host, not
remote CI or a third-party replication.

AC-001, AC-002 and AC-003 pass their bounded sprint acceptance criteria. The code revision above
is the tested implementation; the following documentation/evidence commit does not change it.
The full research project remains incomplete, and no paid training was run.


The normal FlowBoard API/web images were rebuilt and restarted with migration 0003. Read-only
browser/API smoke checks confirmed live updates, non-identifying field tokens, no public research
reset route, and a working artifact explorer. No existing board data was reset during deployment.

## 2026-11-22T23:49:40.712741+00:00 — P0 checkpoint PASS; mandatory review pending
- HEAD: 1fa4f02610a4e556b84a3984dc1e650b2b78cca7, dirty; no commit made. User's prior adaptive
  application/test changes preserved byte-for-byte; no scientific application source changed.
- P0 run: p0-20261122-audit. App source SHA256: 71b000901e98372a067a8d2e8103f3c112d0c5b85b8eaa0086eeec2f655d9744 (same as both invalid Gemini archives).
- Commands: `python3 research_ops/scripts/p0_audit.py p0-20261122-audit register`; environment (failed),
  db-start, environment-recheck, check, demo, pilot. Controlled clock probe command and failed
  assertion retained in raw/clock_probe.py/log; both clock pauses succeeded. Registry records amendments.
- Actual check uses `PATH=.bootstrap/bin:$PATH`, custom AFTERCLICK_TEST_REPORT and `bash scripts/check.sh`:
  frozen uv sync, npm ci, TypeScript/Vite build, Ruff lint/format, full pytest (122 passed, no skipped,
  1 upstream warning). New audit helpers also pass Ruff/format/py_compile after local formatting fixes.
- Demo afa078d8f51844ba8299ddef897c2962: 7 attempted/valid, 0 invalid. Pilot cf24751ccc8b429499f979c38c12ed95:
  24 attempted/reference-valid, 0 invalid, 24 expected matches; 9 recoverable, 3 unrecoverable,
  3 conflict, 3 UNKNOWN, 3 CENSORED, 3 PARTIAL. 25 saved certificates independently recomputed by
  the existing evaluator and matched. Unknown/censored outcomes are not replay-invalid or safe labels.
- Historical: 12 case slots, 0 valid, 12 invalid; 144 branch slots, 51 actually initialized,
  93 source-invalid skips. Two initiating HTTP503 errors and one clock error, preserved.
- Engineering stages: 7 attempted, 5 passed, 2 unsuccessful (initial DB check and negative clock probe).
- Cost: P0 Modal/Tinker/model use $0/0 calls. Historical Gemini known estimate $0.001171 plus
  $0.0013045 reservations; actual invoice unknown. Modal applicable remaining credit unknown;
  no Modal endpoint launched/queried. Local db remains running; api/web unchanged.
- Source identity and abstract-level overlap checked against primary literature; no novelty clearance.
- Artifacts: manifest/protocol/trials/model_calls(empty, no fresh calls)/oracle_certificates/metrics/
  analysis/next_experiment/raw/figures(explicitly no scientific figure). Demo explorer retained.
- Files created/updated: README.md, scripts/check.sh, docs/COMPLETION_GATES.md, docs/REPRODUCIBILITY.md, docs/ADAPTIVE_REPLAY.md, docs/PROGRESS.md, research_ops/scripts/p0_audit.py, research_ops/scripts/analyze_p0.py, research_ops/PROGRESS.md, research_ops/DECISIONS.md, research_ops/CLAIM_REGISTER.md, research_ops/LITERATURE_MATRIX.md, research_ops/ISSUES.md, research_ops/EXPERIMENT_REGISTRY.jsonl, research_ops/NEXT_EXPERIMENT.md, research_ops/STATE.json, research_ops/SESSION_HANDOFF.md, research_ops/P0_EVIDENCE_AUDIT.md. Full raw source/lock hashes, final diff and file manifest retained.
- Claim result: C1/C2/C3 untested. No natural mistake frequency, population CI or held-out result claimed.
- Decision: STOP for P0 human review. Next preferred: $0 P1 local HTTP-mock adapter preflight;
  fallback minimize first failed mock without provider calls. See NEXT_EXPERIMENT.md.
- Repro saved analysis: `.venv/bin/python research_ops/scripts/analyze_p0.py artifacts/research_runs/p0-20261122-audit --output /tmp/afterclick-p0-review-1` (fresh destination).
- Repro backend: `.bootstrap/bin/uv run python -m afterclick.evaluation.pilot --output artifacts/p0-review-pilot`.
- Resume context: `cat research_ops/STATE.json research_ops/SESSION_HANDOFF.md research_ops/NEXT_EXPERIMENT.md`.

## 2026-11-23T00:46:17.580575+00:00 — P1 local PASS; live infrastructure INCONCLUSIVE; paid gate closed
- HEAD 1fa4f02610a4e556b84a3984dc1e650b2b78cca7, uncommitted. No commit/push/release. Existing Gateway/DB/scheduler/recovery
  preserved; adaptive runner adds public-input validation and provider-neutral usage reporting.
- Added afterclick/agent/inference.py, modal_policy.py, evaluation/modal_smoke.py; tests/agent/
  test_modal_policy.py, test_smoke_cli.py, test_modal_lifecycle.py; research_ops/scripts/
  p1_mock_replay.py, modal_lifecycle.py. Updated README/current gate/reproduction/progress docs
  and P1 reports, cost/failure/next/P2 plans, ledgers/state/handoff. Exact source/diff hashes retained.
- Runs p1a-20261122-local, p1b-20261122-readiness, p1c-qwen35-9b-smoke-v1 registered before
  execution. User instructions and authorization copied without secrets; raw failures preserved.
- Local checks: frozen uv check reused .venv Python3.11.14; Modal1.6.4 via uv tool isolation; locks
  unchanged. Full pytest181 then184 passed; final targeted82 passed;3final lifecycle checks pass.
  188 unique test identities covered across batches, NOT a claimed188-case full-suite run.
  Ruff/format/diff checks pass. Commands and JUnit under p1a raw/.
- Primary mock replay9ce2a4d55bb84db4be88e18e40c3a648:3attempted/3valid/0invalid cases,
  36valid branches/goals,27mock requests. Prior ac4682b9f860463f9560ed915387eef5 retained,
  total6case runs/72branch slots; repeated three families at seed7, one mechanism; no population CI.
- P1C: user approved exactly$2; workspace usage cap lowered from$42.50 to$2. Effective default
  net spend$0 verified, no custom0 saved. Two create commands: first missing proxy, second created
  ep-q7N7iwcaFpWA2jF35AqgqK at pinned9B revision. Startup unready;0model requests/0live tasks/
  0live replay cases. Deployment timeout is not a recovery-censoring label or model error rate.
- Cleanup omission --yes fixed; dashboard stop and CLI stopped metadata/list[] verified. Temporary
  proxy and private ignored credential file deleted. Endpoint stopped19:34:55 EST; no active endpoint.
- Latest reported Modal metered$0.06300505, billed$0, creditused$0.03; dashboardcreditleft$29.97,
  workspaceusageheadroom$1.97. Billing approximate, no invoice guarantee. Model/GPU usage unknown
  because no resource metadata became inspectable. No fine-tuning/real external effects/holdout access.
- C1/C2/C3 untested. P1 incomplete; no positive live model or safety result. Paid approval closed.
- Preferred next: separately approved max$1 same-model clean240/60/60-second diagnostic,
  <=20readonly decisions if possible, resources/rate verified before generation. Not authorized.
- Repro free: `.venv/bin/pytest tests/agent -q`; fresh mock run:
  `.venv/bin/python research_ops/scripts/p1_mock_replay.py --output artifacts/p1-mock-review`.
- Resume: `cat research_ops/STATE.json research_ops/SESSION_HANDOFF.md research_ops/NEXT_EXPERIMENT.md`.

## 2026-11-23T01:42:23.263970+00:00 — P1 continuation: v2 finalized, local4B preparation

Full regression200tests passed in136.31s; artifacts p1d-20261123-4b-readiness/raw/full-tests.*.
9Bv2 clean240s startup failed;1create/44provisioningpolls/0generation,cleanup245.711s verified.
Both9B approvals closed; no active endpoint/proxy. Credit$29.95,used$0.05,billed$0;cap$2/headroom$1.95.
4B separate pinned arm prepared, runtimeGPU/startup/schema unmeasured. Newmax$1.50 diagnostic
requiresapproval;0newpaid authorized. P1Apass,P1Cincomplete;C1/C2/C3untested. See research_ops reports.
Free repro `.venv/bin/pytest -q`; safe resume `cat research_ops/STATE.json research_ops/SESSION_HANDOFF.md research_ops/NEXT_EXPERIMENT.md`.

## 2026-11-23T06:03:01.480683+00:00 — approved P1C contract-repair pilot starting
V2 closed after metadata200/one invalid read argument; no browser action. User approves v3 max$0.70, same public endpoint, conditional-v2 generation schema,410s/40generations+1metadata/zero retries; min1 temporarily then min0 verified. Credit28.86/headroom0.86; cap2 unchanged. Controller/source/protocol frozen before launch. Command: `.venv/bin/python research_ops/scripts/p1_existing.py --run artifacts/research_runs/p1c-existing-4b-validation-v3 --execute`. No C1/C2/C3 claim.

## 2026-11-23T06:14:26.547561+00:00 — P1C live task FAIL; P2 local backend PASS; paid work stopped
HEAD 1fa4f02610a4e556b84a3984dc1e650b2b78cca7, uncommitted; no commit/push/public release. Existing foundations preserved.
Runs: warmv2 metadata200,1generation/0valid/1invalid Decision (nonempty read value); warmv3 metadata200,11generation/11valid Decisions, smoke and single task PASS, multiaction FAIL (8Descriptionfills/7redundant;PriorityNormal). Replay0attempted/12unattempted branchslots. Both approvals closed; no retries. V3 elapsed184.397s; min0/max1/buffer0/idle2 and idle0verified, user endpoint preserved.
P2 p2-20261123-distinct-mechanisms-v1:48attempted/executionvalid,36known,0invalid,6UNKNOWN,6CENSORED;48expectedmatches,88.033s,$0/0modelcalls. Offline all48primarycertificates and3receiptfollowups match. Receiptcommit100/arrival400/followup450 distinct from primaryUNKNOWNat300. Capability-relative fakefee, not realfinance/liveagent mechanismvalidation.
Local p1f recorded audit11/11 exactoutputs;0newlivecalls, excludesmissingPriorityinstruction/goal/visiblefield andadaptercache. Modelplanning vs installedgrammar remainsunresolved. P1e full212passed156.76s; agent101 andfinance5 separatebatches; conditionalmock15calls/12validrealPG-Chromiumbranches. Allfailuresretained. ScopedRuff/format/diff pass; unchangedlegacymodal_smoke.py broadlintfindings preserved, noexecution.
Changed paths: afterclick/agent/{modal_policy,decision_schema,browser_observation}.py; replay/adaptive_runner.py; benchmarks/mock_finance.py; evaluation/{finance_oracle,mechanism_pilot}.py; tests/agent/ andtests/evaluation/test_finance.py; research_ops/scripts/{p1_existing,analyze_mechanisms,audit_recorded_tasks}.py; README/docs/research_ops ledgers and reports. Exact hashes FEATURE_STATUS.json and run manifests. Final tracked diff hash 1fc44c70b183ac720145f35af9e5dae412b95170af57e59ee2889c29ce5fe316 (does not include untracked files).
Costs: v2/v3 approximate account credit deltas0.18/0.28, not invoices. CLIhighwaterused1.42,left28.58,cap2/headroom0.58,billed0; UIused1.24 retained. Projecttotal allocation unknown because user activity/delayed adjustments; no tokenbilled API or training. Endpoint idle0, no ownedactiveGPU.
Claims C1/C2/C3 untested; no organicunauthorizederrorrate, minimalboundarydiscovery or heldoutresult. Next: prepare one exact-input schema-only diagnostic locally; future paid probe needs distinct approval. No taskbypass or thresholdrelaxation.
Commands: `.venv/bin/pytest -q --junitxml=artifacts/research_runs/p1e-20261123-existing-endpoint-audit/raw/contract-final-full-tests.xml` (executed; do not overwrite archived log on rerun); `.venv/bin/pytest tests/evaluation/test_finance.py -q`; paid closedcommand `.venv/bin/python research_ops/scripts/p1_existing.py --run artifacts/research_runs/p1c-existing-4b-validation-v3 --execute` (refuses reuse); offline `.venv/bin/python research_ops/scripts/analyze_mechanisms.py artifacts/research_runs/p2-20261123-distinct-mechanisms-v1 --output /tmp/afterclick-p2-review` (fresh destination).
Resume: `cat research_ops/STATE.json research_ops/SESSION_HANDOFF.md research_ops/NEXT_EXPERIMENT.md`.

## 2026-11-23T06:17:36.047632+00:00 — sealed P1C/P2 checkpoint
Six completed run directories sealed; all1009archived file hashes verify. P1C live task FAIL, liveP2BLOCKED; localP2backendPASS. All approvals closed/paidmodedisabled; user endpoint min0/idle0 preserved. Fullhandoff research_ops/SESSION_HANDOFF.md; registry/STATE updated.

## 2026-11-23T15:38:16.519439+00:00 — new standing authorization and endpoint audit
User mandate supersedes per-run approval requirement with<=20additional Modal compute, reserve>=8, category caps3/3/4/8/2. New endpoint ep-NtuMALXsRWKk5JLfZk4BOF is pinned4B851bf6e…,not9B; APIAfterClick,publicDedicated,H1001/CPU4/RAM16GiB,0containers. Only endpoint listed; app list empty. Account credits28.11/used1.89/billed0. Authorized incremental workspacecap2→3 saved; effective defaultnetspend0 verified. Provider caps are workspacewide; software charges all accountdelta conservatively; no unrelatedspendauthorized. Costsupervisor tests precede inference; no model requests yet. Earlierfailedruns unchanged.

## 2026-11-23T15:47:00.294439+00:00 — live lost-ack failure; preregister visible retry guard
Newendpointv1:16valid decisions/18245tokens, simpletaskPASS, multiactionFAIL,6validbranches thenlost_ack Gateway blockedmutationwhileFailed;5branchslotsunattempted,caseINVALID.199.451s,min0/idleverified,$0.36000177approx accountdelta. v2only adds visible Failed+Retrysave guard, no hiddenstate; hybridpolicy provenance explicit. Tests6pass. Standingauthorized max0.60/355s/40gen, existingcap3/effectivenet0unchanged; supervisorhigherbillingretained. No training.

## 2026-11-23T15:51:24.383688+00:00 — P1C minimal scientific gate PASS
New endpoint v2, hybrid visible Retrysave guard,19modelcalls/21563tokens; smoke/simpletaskpass, multiactionfails,12/12replaybranchesvalid/all6placebos/null/lostackverified. Oneplanteddevelopmentcase, no organicerrorrate or C1/C2/C3.209.654s,min0/idleverified,~0.36accountdelta. Two currentstandingruns conservativelycharged~0.72total; no furtherP1spendingneeded. Scope revision preregisteredfromuser6.4; oldv1failure unchanged. P2new54-case primaryrunning locally.

## 2026-11-23T15:59:27.873085+00:00 — P2/P3 bounded local gates PASS
New54case PostgreSQL pilot:54executionvalid,42known/6UNKNOWN/6CENSORED/0invalid,135.643s,$0. Four total recovery-obligation classes, not four permanent irreversible effects; permissionchild expiry gives nonmonotone current recovery. Formal finite closure audits102savedcases/63knownassertions/0disagreement and256abstractstates;3PARTIALimplementation failures have valid strategies. Unknown/censored/conflict labels not overwritten. See docs/TEMPORAL_RECOVERABILITY.md. Next matchedsearch; no learning/holdout accessed yet.

## 2026-11-23T16:47:29.804937+00:00 — H1 local explorer fails strongest baseline
p4-matched-search-v1:14,400candidatequeries/6,144separategroundtruthqueries,10PGboundaryendpointchecksvalid,4mechanisms/5transitiontypes. coverageAUC1.9375 > local1.520833; localdifference-0.416667. random_min1.482639 (vscoverageCI[-0.571181,-0.339583]); plainrandom/enumeration0adjacentboundaries at96budget. Conditionalfixed-benchmark result, notpopulationCI/novelalgorithm. Stopcomplexsearch; nextregistered matched-budgetdata/learning.

## 2026-11-23T16:52:15.000275+00:00 — development completed; holdout still closed
P6/P7:16,384attemptedfinite labelqueries,128UNKNOWN/CENSORED retained (64each),40modelbundles/560metricrows,20.326s excludingcoldimports. No modelcalls/GPU. BoundaryGB IDBrier0.01788 vsrandomCF0.02109, butauthorityOODcurrent~0.298 (notselectedonOOD). These are developmentonly, no heldoutclaim. Freeze path-normalizationerror occurredafterallfits; repairedfromsavedartifacts withoutretraining. Fullsuitefirst234pass/1failure: newtest incorrectlyrequiredspendingallquotaevenwhenlasttaskauthorized; correctedexpected19 ratherthanrejectauthorizedgoal. Runtimecontrollerunchanged. Narrowtestandfullregressionrerun beforeopeningfinaltest. Rawfailurelogsretained.

## 2026-11-23T17:00:24.465531+00:00 — open final evaluation once
Frozen code/data/model hashes verified;235fulltests pass160.55s plus2separateGatewayenforcementtests5.66s. Models/controller unchangedafterfreeze. P7actualpublicinputcollision confirmedatprospective150: noticeREC,feeUNREC. Finaldeadline2048finitecases/16PGspotchecks startunderpreregisteredprotocol, $0/noendpointrequests. No post-holdouttuning.

## 2026-11-23T17:11:09.392750+00:00 — locked confirmation complete; preserve mixed/negative findings
P9:2048finiteheldoutdeadlinecases (64sourceclusters),16/16freshPGspotcasesvalid,55.707s,$0/0modelcalls. Allmodels/controllerfrozenbeforeopening. PrimaryH2selectedboundaryminusrandomCF Brier0(identicalknown-mixturewinners); secondaryfixedGBimproves-0.00369067[CI-0.00483658,-0.00269943]butknown-mixturebaselineBrier0.014771<boundaryGB0.015620. H3at409/2048interventionsandtaskcompletion1:955/2048no-shieldharms→546/2048learnedandtimerboth; learnedminustimer0,CI[-0.00146484,0.00146484]. PGcontrollerreplayno-shield8/16harms→5/16forrule/timer/learned,3interventions,16/16goals; purposiveauditnotpopulationestimate. BroadH1/H2/H3notestablished; narrowedbenchmark/observability/negativecomparison. Finalrawstructuralindependent-editflagnotempiricalcollaboratortest, annotatedseparately; donotoverclaim. Next P10writeup/reproducibility, no tuning or paiddata needed.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

The bounded study and evidence-backed paper draft are complete. Final regression: **239 passed** in
172.43s, with one upstream deprecation warning. Research novelty remains **INCONCLUSIVE**; broad
C1/C2/C3 superiority is not established. See `paper/PAPER.md`,
`paper/REPRODUCE.md`, and `research_ops/SESSION_HANDOFF.md`.

One hybrid Qwen3.5-4B live-policy case has 12/12 valid branches; the unmodified arm retains one
invalid case (6/7 attempted branches valid). Multi-action competence remains unresolved. Backend
pilots cover 102 planted cases in four recovery obligation classes: 78 known, 12 UNKNOWN,
12 CENSORED, zero execution-invalid. These are not organic agent-error measurements.

Search uses 14,400 candidate queries, separately audits ten PostgreSQL endpoints, and validates five
semantic transitions. Coverage beats the targeted local explorer. Learning uses 16,384 finite-model
acquisition queries, not live browser trajectories. On the locked 2,048-row/64-cluster deadline test,
the selected-model H2 contrast is zero; the fixed tree improves Brier by 0.003691 over random CF,
but the stronger specified mixture scores better. At 409 interventions and full task completion,
learned and timer shields both yield 546 harms versus 955 unshielded. Sixteen fresh PostgreSQL
controller audits likewise show no learned advantage.

No further paid calls are running. The two new live pilots have conservative guard accounting of
$0.720003; the account high-water increase is about $0.630003, not an isolated invoice. Conservative
remaining credit is $27.48; latest UI/CLI report $27.64, with $0 billed. The saved workspace cap is
$3 and effective default net spend limit $0. Endpoint ep-NtuMALXsRWKk5JLfZk4BOF remains min0/max1,
buffer0/idle2, zero containers verified. Standing authorization remains bounded and idle; no new
approval is routinely required under the latest mandate. No new endpoint or public release occurred.

Executed commands: `.venv/bin/pytest -q --junitxml=artifacts/research_runs/p10-synthesis-v1/raw/final-tests.xml`
(239 passed); `.venv/bin/ruff check afterclick tests migrations`; `.venv/bin/ruff format --check afterclick tests migrations`.
Read-only final Modal billing/endpoint/container/autoscaler checks are saved under P10 raw/.
Execution HEAD was 1fa4f02610a4e556b84a3984dc1e650b2b78cca7 with a dirty tree; later source checkpoint
will be recorded separately. Changed paths: afterclick/research/, capability benchmarks/oracles,
tests/, research_ops/, docs/, paper/, pyproject.toml, uv.lock, scripts/check.sh. Old raw runs retained.
Repro: `.venv/bin/python research_ops/scripts/render_research.py --output /tmp/afterclick-review-20261123`.
Next: independent workload-distribution replication, not further current-holdout tuning.


## 2026-11-23T17:50:00.462380+00:00 — final checkpoint

Packaging: CI/check.sh/validation image now select optional research dependencies explicitly; bash syntax/uv frozen dry-run pass. No scientific code changed after freeze and no full repeated evaluation was needed.
