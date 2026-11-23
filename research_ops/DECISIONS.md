# Decisions

P0: reproduce the existing dirty checkout in isolated ac_* schemas. Alternatives: clean-clone only (would omit adaptive work), or paid retry (forbidden and premature). Reverse if source hashing or fresh baseline reveals incompatible foundations.

## 2026-11-22T23:49:40.712741+00:00 — audit checkpoint and result-conditioned next step
Evidence: p0-20261122-audit; 122 tests, 7/7 scripted branches, 24/24 oracle classes; 0/12 archived live cases valid.
Decision: P0 PASS as an evidence audit; adaptive live gate remains unmet. Stop for required human review.
Alternatives: (a) paid Gemini retry: cannot establish provider reliability from a new uncontrolled attempt,
no new authorization; (b) immediately build more mechanisms/search: premature while live validity is
unmet; (c) repair presumed clock race: 50ms probe did not reproduce it, so no speculative source change.
Preferred next after review: P1-local HTTP-mock adapter preflight, $0. Future paid smoke proposal only
after local pass, price/credit verification and specific approval. Do not assume Qwen resolves HTTP503.
Reversal: a baseline source/hash mismatch or contradictory oracle receipt reopens P0; failing mock
accounting blocks deployment. C1/C2/C3 remain proposed. No primary-paper aim changed.

## 2026-11-23T00:46:17.580575+00:00 — P1 infrastructure result and next discriminator
P1A passed with184 full-suite tests, final82 targeted tests,3/3 final HTTP-mock replay cases/36branches.
P1C approved cap$2; one missing-proxy create failure, one endpoint created,0ready/0model calls.
Stopped verified by UI and CLI, temporary proxy deleted. Metered$0.06300505, billed$0, credituse$0.03.
My missing proxy preflight and missing --yes cleanup flag confounded timing; both retained and
local cleanup/finalization tests added. Do not attribute this to Qwen schema/capability or invent
a causal replay failure. No paid inference retry or model swap. Original approval now closed.
Alternative: silently extend the first window/reuse approval; rejected because it would change
registered stopping conditions. Alternative: switch4B; unsupported without a controlled new arm.
Preferred next new max$1 proposal: same9B, proxy ready before timing, clean240s provision/60s
inference/60s shutdown, inspected rate<=$0.0021/s, <=20readonly decisions if time permits; no
browser writes. This replaces an intermediate180/120 timing draft BEFORE any new data; prior
endpoint remained unready after~206s, motivating a longer clean provisioning allowance.
Reversal: source/receipt mismatch reopens local gate; inability to inspect serving resources or
next paid failure stops collection and favors read-only/provider diagnostics. No primary aim changed.

## 2026-11-23T01:40:20.259832+00:00 — close v2; prepare separate4B feasibility arm

Evidence: v2 clean240s startup failed;44polls allprovisioning,0generation; teardown245.711s,
no active endpoint/proxy. Updated STATE and all living reports; historical raw records retained.
Decision: do not retry closed9B approval. Explicitly requested4B is a separate arm, provisionally
eligible from metadata/local mocks only. Proposedmax$1.50,480/60/60s,1decision, in-progresslogs.
Alternatives: another same240s retry has low information gain; claim4Bcheaper/faster lacks evidence;
custom serving app would add unvalidated setup. No final model selection without browser/replay.
Reversal: catalog/resource/schema mismatch blocks this arm; another provision failure triggers free
infrastructure diagnosis instead of paid model cycling. No primary research aim change.

## 2026-11-23T02:26:23.520914+00:00 — existing endpoint reuse and observer blinding
User mandates reuse ep-pkGzZooYksPv4BKbIqi0dk, no newdeployment or permanentstop. ReadonlyCLI confirmsliveAfterClick/pinned4B/Dedicated/public; browserInactive0containers. User explicitlypermits publicsyntheticuse and requestsP1C/P2completion, but specificnewdollarapproval stillneeded. Prepareone stagedmax$0.90pilot withautoscaler0/1/0/2s, no credentials, no endpointlifecycledelete. Alternatives: replacement9B forbidden; unboundedpublicrequestsscientifically/budgetunsafe; repeated1decisionpaidadmissionsaddlatency withouttestingreplay. Newpublicpolicyrequires taskhashallowlist; defaultprivatemodeprovenance unchanged. Literal suppressedfeedback wasleakingarmidentity; defaultpublichistory nowblindsit,legacyexplicitFalse retainedonlyforarchivereproduction. RawGatewaytracesunaltered. Mockassignee goalcompletedbutviolatedinitialnonotificationcontract; failurepreserved. Beforelivefreeze separateDescription+Highpriority-v2 task; nooraclethresholdrelaxed. Revisitassigneeonlywithlegitimatenotificationcontract/witness, notbyrelabelingfailedrun.

## 2026-11-23T06:14:26.547561+00:00 — retain multiaction failure and stop paid collection
Evidence: v3 has11validdecisions but fails independentPrioritygoal after8Descriptionfills; offlineaudit excludes omittedvisible/taskstate andcache. Alternatives: bypassmultiaction, loosenstepbudget, switchmodel, or isolate schemaeffect. Rejectfirstthree as posthocrescue/unapprovedscope. Decision: keepfailure; prepare exact-input schema-onlypair,holdpromptfixed,stopbeforepaidapproval. Modelplanning/grammarremainrivals. Reverseonlyafterindependent samegatepass undernewfrozenprotocol; neverrelabelv3. P2backendgatePASS but no livecollection/training unlocked. Directfake-bankpostingclockfixedafterprimary; rawprimarysnapshotretained and48certificatesrecomputed.

## 2026-11-23T15:40:52.591185+00:00 — predeclared revised P1C scope
Latest user mandate6.4 allows complete live replay with unreliable multiaction task as explicit limitation. Run same frozen conditional-v2 policy, no architecture/prompt tuning yet. Multi-action failure remains a reported failure; simple legitimate task and full12branch causalreplay remain required. This is not retrospective relabeling of oldv3. Alternatives are spend time on multigoalplanning or proceed with invalid replay; rejectboth unless replay exposes an essential blocker. Standing-authorized cap0.90/450s, supervisor lock/reserve and provider cap3/net0; only new endpoint.

## 2026-11-23T16:47:29.804937+00:00 — stopsearchcomplexity
Strongcoverageoutperformslocalfrontier; plainrandom wouldbeweakbaseline. RetainnegativeH1, usecoverageforlabelacquisition. Do notaddgenetic/MAP-Eliteswithoutobservedlimitation. Reverseonlywith a new mechanism-conditioned failure discriminated undernewbudgetmatchedprotocol, notposthocsearchtuning. Primaryquestionunchanged; benchmark/negativecontribution permittedbylatestmandate.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

Evidence: coverage defeats targeted search; the selected predictor is the specified mixture;
learned and timer controllers tie. Decision: finish a transparent bounded benchmark/mixed-result
paper; do not run evolutionary sweeps, larger models or extra live inference to rescue superiority.
Alternatives: continued tuning, claiming no-shield improvement as learned superiority, or treating
SQL audit counts as live policy diversity. Rejected because they do not resolve the strongest rivals.
Reversal criterion: independently implemented new workload/distribution with frozen public features,
strong baselines and a new untouched final evaluation demonstrates an incremental benefit.
The source checkpoint may include earlier user-owned uncommitted adaptive foundations, preserving
all bytes and their provenance; it is not an authorship claim.


## 2026-11-23T18:54:02.254534+00:00 — interaction mode
Native tools provisionally preferred for the failed development Description+Priority task: two calls,4725 tokens, task/effect oracle PASS, no repetitions. JSON three calls3302 tokens, two repeated satisfied proposals, no executed repeats, task incomplete. Native uses more tokens but completes; n1/mode/fixed order does not isolate prompt/schema/engine causal effects or establish reliability. Original JSON retained; no additional tuning. Both omit reasoning/reasoning_effort and never mix response_format with tools. Endpoint min0/idle verified, batch203.858s, cap0.60. New study continues locally.


## 2026-11-23T19:25:43.095453+00:00 — independent development checkpoint
Fixed acquisition/model/controller comparison complete; strongestselectedmodel is handwritten heuristic, besttrained ordinary hazard. Boundary acquisition hurts calibration and compresses source diversity. Mean+SD controller has worse harm but higher clean completion than observable rule, so no safety-superiority claim. Freeze models; test once without rescue. Quota opportunitycost is a credible rival, not proof of a novel controller.


## 2026-11-23T20:06:10.697972+00:00 — native interaction and observability extension

Stop interface optimization after i1; selected native for newdriver, preserve JSON and earlier replay. Stop scientific tuning after o2/o4: strong rules remain competitive; data selection/censor assumptions and myopic quota allocation are credible explanations. Limited secondary gains over alwaysverify are retained, not converted to a broad H4 claim. Exact race identity is elementary conditional algebra, not a new POMDP algorithm. Preferred next evidence is independent contract/implementation review, then externally measured cancellation/observation latency. Reversal criterion: genuinely new untouched workload with available enforcement information demonstrates a robust advantage against strongest matched baselines.
