# Failure analysis

Historical Gemini live archives remain0/12valid cases;503transport and one clock error retained.
P0 baseline122passed. Original88vs122test drift reflects different revisions/batches, not new evidence.

9B attempts had provisioning/deadline failures,0generations. First confounded by missing proxy and
shortenedstartup; second clean240s/44polls. Private4B480s attempt misseddeadline despite weights loading
in4.28s; logs show image/warmup cost. Post-stop Traceback is not evidence of spontaneous pre-stopfailure.
These operational outcomes do not establish modelquality or comparative9B/4Bstartup performance.

Existing public4Bv1: metadata503beforebackendready,0generation. Initial30s cleanup could not verifyidle;
later separateCLI[]/UIInactive0confirmedidle.503bodynotretained (instrumentationgap); no retry/fabrication.
V2explicitboundedmin1warm fixedearlyready ambiguity:metadata200, one invalidreadargument. Flat generation
schema allowed nonemptyvalue while runtimeDecision forbadeit. Runtimevalidation was correct and remains
unchanged. Conditional-v2 schema+instructions introducedasnewv3arm with versioned cache/recordedprovenance.

V3metadata200,11valid Decisions; smoke+single taskpass. Two-action taskfailed,8Descriptionfills,7after
satisfiedgoal,PrioritystayedNormal. All11requesthashesunique,noadaptercachehits; offlineexactrecordedaudit
passes11/11. Priorityinstruction,goal,currentNormalprovided, so missingtaskstate/cacheareexcludedfortrace.
Modelplanning,promptsalience,livegrammarreachabilityremainrivals; noneprovenasunique cause. No action
bypass, stepbudgetextension or posthocacceptance. Replayunattempted, no causal certificates. Paidapprovalclosed.

Leakageissue: legacypublic_history disclosedsuppressedfeedback. Newdefaultneutralcompletedack and public
inputrejection protect newarms; rawGatewaytruthretained. Olderunblindedmockresultsarenotblindedmodelproof.
Mockassignee taskhadbadnonotificationcontract; failedretained; separateDescription+Prioritytaskfrozenbeforelive.

P2oracle negatives/unknown/censored remain separate. Directfake-providerpostingclockrepair happenedafter
primary48cases; originaldriverfinalstatesconsistent, all48savedcertificatesrecompute. Current212tests pass.
Broaderhelperlint foundunchangedoptionalmodal_smoke.pyformattingissues; main/newhelperslintpass. Noexecution
ofthatlegacybillableexample. Billingisdelayed/nonmonotonic; retainlargerusageobservationforadmission.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

**Preserved failures and scoped recovery**

Unmodified v1 lost-ack branch attempted a new mutation while save was Failed; Gateway refused. v2 visible-only Retry save guard repairs that reconstruction path. Multi-action repeated edit failure remains in both arms. This distinguishes provider syntax reliability, task competence and causal replay validity. Original traces and failures remain, not relabeled safe/unsafe.

Authoritative synthesis: paper/PAPER.md; raw run IDs in evidence/research-20261123/index.json.
