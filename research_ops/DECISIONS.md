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

### 2026-11-23 — genuine policy trajectories before further synthetic modeling
- Evidence: 32 prior seals / 2,537 checksum checks preserved; old public_task exposes structured goals and Gateway stamps scripted-agent. Native n=1 format comparison is insufficient for nominal competence.
- Decision: additive `afterclick/model_sprint/` driver, natural instructions with empty public goals, private post-run oracle, truthful native tool results, real PostgreSQL background worker, actual model/tool-call provenance. Six paired sources / 12 development tasks; no old searches/predictors repeated.
- Alternatives: reuse hidden-goal driver (would confound new claim); add more mechanisms before observing behavior (unnecessary engineering); call branching novel (contradicted by SURE-Act/Cordon).
- Reversal criterion: interface/receiver/provenance failure halts collection; fewer than 9/12 nominal completions halts recovery-performance interpretation. No repeated paid tuning to manufacture harmful actions.

### 2026-11-23 — stop paid intervention at failed competence gate
- Evidence: s1 completed 4/12 (4/4 noncomment, 0/8 comment), all valid. Eight comment drafts never submitted; one Review toggle reversed requested state. Native syntax/usage valid; six receiver-consistent receipts. s2's scripted Post continuation fixes first failed task; placebo read does not.
- Decision: **PIVOT** to precise draft/commit semantics before considering another live competence arm. End paid work in this sprint; do not run COPE or held-out comparisons on this incapable nominal baseline.
- Alternatives: coach with hidden goal feedback (invalidates natural evaluation); tune prompts until passing (would obscure original negative evidence); treat zero unauthorized messages as proof of safety (small, protected, explicit task distribution); call a scripted repair live recovery (false).
- Reversal criterion: a separately versioned and preregistered natural-task policy must pass competence on independent task groups before actual live continuation comparisons. Original failed arm remains immutable. Existing standing authorization does not remove this scientific gate.
- Scope: s2 is a diagnostic controller action, not a live continuation implementation or a reproduced Cordon/SURE-Act system. RQ2–RQ3 remain unmeasured; no positive novelty claim or final research completion.

## 2026-11-24T04:18:48.413224+00:00 — Distinct-workload decision
E1competence adequate7/8goals but5/8safe; do not gate research on perfect competence. Compare immediateprotect against livebelieflookahead because resourcecancelmissedfrontier and accessneverrevoked. Contrary: noticecancel and authorizedeffects succeeded, no duplicatecapture. No further prompttuning; reversal if replay/provenance fails local qualification.

## 2026-11-24 — Freeze a correctness-qualified heuristic, do not rescue the null

E3selected21conditions/3sources show stage/fixed3/3safe, TCOPE2/3withone administrative wall censor, timeblind0/3safe; one earlier invalidity repair remains in all-attempt counts. No incremental TCOPE safety advantage. Do not increase model capacity, tune prompts or search thresholds. E4correctness changes are public-belief initialization (known cancellation/resolution/counts, no source hidden state), honest hypothetical-label scope, public-author display copying, actionable single-forecast risk deferral and accurate phase-time accounting. Local counterexamples/regressions justify these; no final outcomes observed. Alternative was freezing misleading default forecast state or counting a censored1-call task as efficiency; rejected. Reverse/stop if current qualification fails. Use the same1USD/555sec hard batch envelope and8USD confirmation category, with375sec inference ceiling sharing unused startup allowance and the original80% buffer preserved by measured startup. Freeze23000ms placebo by prespecified ceil(median development pre-protection deliberation); no outcome-tuned latency.

## 2026-11-24 — E4 amendment2 qualified

Code audit and E3's unnecessary authorized-action displacement justified protect-and-resume for ALL protective comparators, not just TCOPE. Fixed/timeblind candidate evaluations now actually rank the alternatives and share one public starting projection and independent prior draw. An ordinary visible comment author is copied without a forecast marker; initialization is privately labeled scripted. Current26local checks pass142.59s, including actual requested-action persistence and independent receiver prevention; full prior290checks passed318.72s and will be repeated after the locked cohort. All source/prompt/model choices now stop changing. Next is the predeclared8source confirmation, not another development sweep. If simple stage ties/wins, the final finding remains negative for incremental TCOPE safety. No final outcome has been opened.

## 2026-11-24T06:14:12.740600+00:00 — Additive study checkpoint

### Close the frozen confirmation on client-state invalidity
The first actual final source is safe/completed but every sibling fails full observation equality: databasePriorityHigh, originalvisibleNormal, reconstructedvisibleHigh. t10rulesoutdatabasecopycorruption. Follow the frozen stop, preserve7invalid/49unattempted, no paid retry/replacement or efficacy estimate. Alternatives rejected: relax input/full-text equality; refresh/relabel the source; tune method against an opened source; silently replace failed source. Future reversal requires a separately versioned client-cache/update-queue representation, local qualification and a separately frozen evaluation. Budget is not exhausted; causal validity is the reason to stop this cohort. Complete the honest report and retain the failure.

## 2026-11-24T19:09:20.970243+00:00 — Stop after contrary primary confirmation

Alternatives: expand paid repetitions, tune identities/prompts, rescue TCOPE, or report bounded evidence. Choose the final option: u5 primary completion agreement does not favor faithful reconstruction, despite exact initial requests and first decisions. u7 exposes identifier/serving confounds and corrects only secondary chronology. More tuning on this cohort cannot establish generalization. Reversal criterion: a separately specified multi-application, identity-controlled study with genuinely informative interventions and a fresh holdout; no such study is queued. Independent u5 confirmation closed: 18 attempted/completed continuations, 12 exact initial certificates and 6 deliberately invalid fresh diagnostics, no censored/unknown; 61 genuine Qwen calls/146543 tokens. Faithful first-action disagreement 0/6 versus fresh 6/6, but primary completion disagreement 2/6 versus 0/6 contradicts improved terminal fidelity. u7 posthoc audit preserves v1 and corrects UUID comment-order artifact (faithful content disagreement3/6→2/6); primary results unchanged. Later fresh identifiers/serving variation remain confounded. u6 full305tests pass/1warning408.27s; initial formatting lint failure retained and corrected; hashes and saved summaries/figures regenerate. No scientific runtime/prompt/cohort tuning; no new paid experiment queued. New conservative debit$3.169205895, original-allowance cumulative$8.032933131, conservativecredit$20.077066869; zero containers. Earlier u2 sleep overrun disclosed; trajectories category closed at$3.441710297 against$3. Report/claim matrix complete; novelty limited/unestablished.

## 2026-11-25T00:19:19.244289+00:00 — Unified recoverability paper

User-selected main question supersedes OECR headline positioning. Preserve earlier papers, use OECR as methodology, synthesize RQ1–RQ3 with common definitions but separate denominators. No-go paid collection: closedcategory/disabledmode, progressing-schedule twins unqualified. Alternative was new12sourceA/B; deferred because current validity/authorization does not support execution. Reversal requires local qualifying evidence and explicit applicable priced approval. Central saved tables reproduce; fresh tests/reproduction interrupted are not relabeled pass.

## 2026-11-25T02:09:15.858529+00:00 — Reviewer response v10 local gates

Review response local phase: corrected current versus history semantics, mapped102savedcaseswith78determinate comparisons, local/full disagreement42/78 and3current-return/history-failure expiry cases; all102prevention projections null. Newoperationalcut8conditionspass plus strengthened16testreviewrun, actualrestore1test, nativeGateway/pairsmokes; finalmockbudget3tests andSDKadapter4checks. OfficialpinnedUndoBench doctor/smokepass,5publishedwrapperscomplete100scriptedexecutions/50pairedcells/10task-seedinstancesin5authoredworkflows; unavailableEvoUndo failure retained. Officialhistoryoraclealready captures14local/fullscore differences and a naive-versusVBR ranking reversal, so novelty based on history-aware scoring is rejected. w3fresh320collectedtests/1warning464.64s and all6knownphases315.60sUTCpass;6metricsnumericallyequal. Lateramendments separatelytargeted,not324fullpass. Priorv0failurespreserved.0newQwencalls/$0Modal; designatedendpointmetadataandemptycontainersread-onlyconfirmed. PaidDEV/externalpilot/finalconfirmationblockedwithoutnewexplicitapplicablecontingencyearmark; nocategoryreset/new20allowance. Narrowmanuscript/appendix/provenance/noveltyreviewupdated; no submission readiness or newalgorithm claim.

SourceHEAD e2147c4 plus new review modules/reporting; no frozenruntime/officialtask changes. Choices: preserveoldlabels,versionderivedpredicates;withdrawhistorymetricnoveltywhenexternaloraclealreadycapturesit;qualifyprogressingcutlocallybutretainmissingQwenstage;finishnarrowpaperratherthantrain/tuneforpositivefinding. ReversalrequiresfreshfinancialadmissionandvalidgenuineDEV beforefreezingnewindependentfinalcohort. Repro `.venv/bin/python -m research_ops.scripts.reproduce_review_response --output /tmp/afterclick-review-NEW`; local `pytest tests/review -q`; full/reruncommandsinw3/raw.

## 2026-11-25T02:38:00.545069+00:00 — Fixed prospective confirmation decision
Alternatives: stop aftervalidDEVtie; expandmethodmatrix/tunemodel; freezea single12-source timingcomparison. Evidence: DEV27new9Bgenerations,6validbranches,alltie,actualsubsecondinferenceandmulti-secondtooloverhead,guard.411998USD; no receiptinsidegeneration. Decision: newcohort12source/3mechanisms,6explicitlyauthorized/6prohibited, variedlegitimatedescriptionversusprioritygoals, balancedshuffledshort/medium/longwindowsandarmorders. N12haswideintervals andcanonlydetectlargeconsistentpairedchanges. Comparepublic-ruleimmediateprotectionvsverificationplusnewdecision; delayedcontainmentsecondary. No newlearnedalgorithm, fullcompensationororganicunauthorized-actionfrequencyclaim. ExistingUndoBenchcaptureshistoryrankingnovelty, Cordonstagingknown. Reversal: technicaladmission/unknownusage/financialfailurestops; otherwisecompletefixedcohortregardlessoutcome, no positive-resultsampling. Currentmodelsandtasksnotalteredafterfreeze.

2026-11-25T02:51:22.351181+00:00 — Before opening final efficacy: source audit confirms Database.transaction serializes writers by per-schema PostgreSQL advisorylock, so runtime state mutations cannot silently overwrite concurrent cancellation. Clarification: preregistered analysis field prevention_deadline_ms is imposed scheduling eligibility, not a measured minimal physical frontier. Preserve v1numerics; derived operationalaudit separately records actualconsumeradmission/ticketsnapshot, independentreceiverreceipt and inference overlaps. Primarysafe-completionscoring unchanged; no threshold/selection amendment.

## 2026-11-25T03:13:51.116764+00:00 — Prospective timing final checkpoint
Frozen12-source/36-branch realQwen confirmation:145generations/379322tokens/140nativecalls, all36valid,0invalid/censored/unknown/unattempted. Immediate safe11/12,T11/12,harm0; verify-first and delayed safe10/12,T12/12,harm2each. Paired2wins/1loss/9ties,+.083333,conservative95%[-.412351,.524033],exactp1.0. No superiority/equivalence. Source05immediatepreventsreadbutQwenomitslegitimateaccessrestorationbelowcallcap. Sources07/11delayedallowforbiddeneffects; source11ticketcommitduringrealgenerationcannotberecalledbeforelaterread. All36workersprogressduringinference;3receipt-overlaps(twoauthorizedsources/3dependentbranches),4admission-overlaps(includingoneprohibitedticket). Primaryprevention_deadlinefieldisnominaleligibility; v2auditseparatesactualadmission/receipt/publicACK. GenuineDEV27calls/72577tokens/6validarmsalltied. No held-out tuning/replacement. Newstudy172calls/451899tokens;guard2.779124094USDincludingzerocallstartupfailure. Cash0,min0/idle2/zero containersverified. New20authorizationseparatefromoldguard8.032933131. Conservativecredit17.297942775,unusednewauthorization17.220875906;initialoperational5retained. Fresh330testspass/1warning493.92s,UTCwrapper499.14s; fullre-score42armsmatches. Originalfrozenruntimesandrawstudiesunchanged. No furtherpaidcollectionjustified.

## Ablation C preregistration — 2026-11-25 UTC
Alternative: run a large actor/supervisor factorial or spend remaining20. Decision: qualify strict public-only independent reviewer locally, compare C1/C2/C3 on exactly2development sources, only freeze independent confirmation after meaningful contrast. Evidence: original12-source efficacy result inconclusive with one restoration omission; strong simple rules already sufficient for much explicit authorization. Reversal criterion: technical qualification plus nonredundant advice, timing or task-restoration contrast under valid independent oracles. No extra20authorization or increase of5operational ceiling. Prior history-ranking novelty explicitly rejected.

## 2026-11-25T06:21:06.991030+00:00 — Stop after supervision DEV
Alternatives: expand3-sourceconfirmation, tune output schema/prompt, or stop. Evidence:6validbranches but only3/6validreviewcontracts; C1matchesC3, everyaccessarmrestores; C2timinglossincludespost-responseenforcement. Decision:NO-GO for confirmation; no interface tuning/paidmatrix. Further collection would mainly duplicate rules/fallbacks and an already observed temporal mechanism. Reversal criterion for a future separately scoped study: demonstrate reliable structured reviews and a plausible public-information or restoration advantage over C1withoutusingaheld-outtask. This session authorizes no new allocation or automatic run.
