# Reviewer-response novelty and measurement comparison

Primary texts checked2026-11-24; official UndoBench source pinned4a25c4f. This is a comparison of documented contracts and measurements, not a claim to reproduce complete external systems other than the scoped local UndoBench run.

| Method / primary source | Quantity actually evaluated / maintained | Overlap and AfterClick result | Remaining distinction and limit |
|---|---|---|---|
| [UndoBench](https://arxiv.org/html/2610.05622v1),§2.4,§4,AppendixK; official engine.py/StateOracle | PairedCONTROL/FAULT competence-conditionedCRSR; goal/invariants; wire-levelduplicates/missing/EOR; finalstate and forbiddeneffects | Explicitly history-aware. w2officialbaseline already reverseslocal-only ranking; adding history alone is not novel | Our finite existentialcurrent-feasibility and time-dependent cancellation witnesses are additional declared targets; no demonstrated superiority or unique principle |
| [Cordon](https://arxiv.org/html/2606.17573v1),§3–4.6,§6 | Taskcorrectness, cross-stepcontainment/security and performance; staged effectoutbox records pending/released/aborted/manualrecovery | Supports admission,staging and externalreleasehistory; these mechanisms are established | No full head-to-head implementation. Timing/observational measurement can be evaluated inside similar semantic boundaries, not claimed absent fromitsdesign |
| [SURE-Act](https://arxiv.org/html/2610.24194v1),§3.2–3.4,§4 | Executedcounterfactual utility, actionranking, end-to-endperformance and interactioncost | Already collects clonedalternatives underfrozenbackbone | AfterClick reports independently witnessed irreversibleeffects and temporalfeasibility; does not beatutilitycontrolorcopyitsentireprotocol |
| [AgentRewind](https://arxiv.org/html/2608.14380v1),externalenvironmentboundary and appendixC | Recovery/taskcompletion within workspace-file/context boundary; externalnetwork/runtimeeffectsexcluded | Rollback/contextalignment established; no claimthat it failsinsideitsstatedscope | Browserclient/SQL/externalhistoryspecific implementation; not arbitrary snapshot theorem |
| [Safe to Resume?](https://arxiv.org/html/2608.29381v1),§IV/VI | Missing/inconsistentstate, externalmismatch, nondeterminism/unrecordedeffects and concrete securitycases | Currenthistory/replay validity problems substantiallyoverlap | Exactapp-levelcutcertification is a scoped engineeringinstance, notfirstdiscovery |
| [Sagas](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf) | Completionorcompensatingtransaction semantics forlong-lived transactions | Compensation is not physicalhistoryerasure, alreadyestablished | No new compensation principle |
| [Shield synthesis](https://arxiv.org/abs/1501.02573) / [safeRLshielding](https://arxiv.org/abs/1708.08611) | Enforcement of temporal safety specs via actioncorrection/admission; learnerperformance separately | Safetyshields and minimalintervention established | AfterClick has no formalshieldguarantee ornewoptimalalgorithm; it measures boundedtask/effecttradeoffs |

**Decisive incremental result:** source-only restoration scoring can mis-rank methods, but the independently developed official UndoBench evaluator already catches the same ranking reversal on its unchangedDEVtasks. Reject novelty based on state/history scoring alone. Prospective prevention/current-feasibility metrics remain a scoped measurement distinction, with no evidence yet that they change a live policy conclusion beyond existing history-aware protocols. This is not established publication novelty.

The concrete metric-ranking reversal is an external falsification of our broader novelty hypothesis, not a new method comparison win. Stronger novelty would require a case where the additional current-feasibility/prevention measurement changes a consequential conclusion beyond that existing dual oracle, supported by a valid independent trial. That case is not established by the current results.

## 2026-11-25 — Actual prospective timing result
Freshprimarytextschecked:UndoBench§2.4/§5/AppendixK andpinnedcanonicaladapter; Cordon§4.5/§4.6/§6. ActualtimeprogressingconsumersduringnewQwencallsaddascopedoperationalaxisoverourinspectedboundary-basedbenchmarksetup. Prohibitedticketcancommitduringgenerationandpersistpastparentrevocationbeforelaterread. Immediateprotectionalsoleavesalegitimaterestorationunfinishedinonerealization. Neitherhistoryoraclenorstagingisnew; completeexternalmethodsnotreproduced/head-to-head. Fastverificationautomatonremainsuntested. NewN12primaryeffectinconclusive; publicationnoveltyLIMITED/UNESTABLISHED,notguaranteedbythiscapabilitydistinction.

## Supervision extension evidence (separate DEV)
| Claim | Direct evidence | Status / limit |
|---|---|---|
| Independent public-only reviewer executes through trusted Gateway | afterclick/review/supervision;30newlocaltests;c1genuine21actor/6reviewercalls | Implemented and live-replay-valid; only3/6reviewoutputsvalid |
| Stage-first supervision improves over strongest rule | c1C1/C3both2/2safe; allrestore | NOT DEMONSTRATED; no independent confirmation |
| Sequential review loses an existing opportunity | c1accessC2ticket2535ms/revoke3187ms/independentreceipt | Valid package-level timing case; recommendation returned213ms beforeticket, so not pure inference crossing |
| Undispatched action progresses while withheld | c1authorizedresourceallarmscompleteonce | FALSE in this environment; withholding prevents dispatch |
| New oversight/staging/history principle | SUPERVISION_NOVELTY_ASSESSMENT | REJECTED; prior overlap acknowledged; bounded measurement only |

The original12-source efficacy result remains unchanged. Do not pool this2-sourceDEV with its confirmation denominator.
