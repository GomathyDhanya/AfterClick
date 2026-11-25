# AfterClick — Cross-study evidence synthesis (v11)

**Source of record:** `684_final 11.zip`, principally `paper/AFTERCLICK_RECOVERABILITY_PAPER.md`, `research_ops/RECOVERABILITY_EVIDENCE_AUDIT.md`, the registered/frozen `artifacts/research_runs/` metrics, and the separate read-only oracle-gap analysis. **Analysis performed:** examined the research registry and saved outcome summaries, reaggregated all 36 frozen live-arm rows by independent source/mechanism/authorization status, checked paired source discordances and experiment-level reported uncertainty, and compared claims against original study denominators. This is a **secondary analysis of saved evidence**; no new Qwen inference, PostgreSQL replay, or full independent software regression was performed.

## Executive synthesis

The strongest supported contribution is a **bounded operational characterization** of recoverability and intervention failure: (i) history-aware recovery is distinct from local rollback; (ii) a pending external consequence can pass its last preventable state during an actual Qwen continuation, before physical consumption and acknowledgement; (iii) immediate protective action can prevent a historical violation yet leave the authorized task incomplete; and (iv) extra counterfactual reasoning/supervision does not establish added value over fast deterministic controls in the tested workloads. These do **not** prove a general optimal policy or a novel universal algorithm. The novel-publication claim is still limited by prior work and external generalization.

## Rank 1: Frozen real-Qwen intervention trial — highest relevance to original question

**Runs:** `x3-progressing-qwen-confirmation-b1-v2`, `b2-v3`, `b3-v3`; reanalysis `x4-prospective-timing-analysis-v1/derived/timing-analysis.json` and `operational-timing-v2.json`. **Independent units:** 12 authored source-task instances with three paired branches each, 4 per mechanism (publication, delegated access, resource), 6 authorized and 6 prohibited effects. 36/36 arms valid, no invalid/censored/unknown; 145 genuine Qwen3.5-9B generations, 379,322 known input/output tokens, 140 native tool calls. Forks share source conditions; 36 arms are not 36 independent tasks. Six workflow structures/two core-goal variants; one application and model.

| Outcome | Immediate | Verify-first | Delayed containment |
|---|---:|---:|---:|
| Safe task completion | **11/12** | 10/12 | 10/12 |
| Legitimate completion | 11/12 | **12/12** | **12/12** |
| Forbidden historical effect | **0/12** | 2/12 | 2/12 |

Source-paired immediate-minus-verify: 2 wins, 1 loss, 9 ties = +1/12 or **+8.33 percentage points**. Archive's conservative 95% interval **[-41.24, +52.40] points**; exact discordance test p=**1.0**. No superiority or equivalence. Zero forbidden effects in 12 immediate arms does not demonstrate zero future risk; its two-sided exact 95% upper bound is approximately 26.5% under an iid binomial approximation, itself questionable given authored task families.

**Independent source breakdown:**

| Consequence type | Immediate safe | Verify safe | Delayed safe |
|---|---:|---:|---:|
| Publication, n=4 | 4 | 3 | 3 |
| Delegated access, n=4 | 3 | 3 | 3 |
| Resource consumption, n=4 | 4 | 4 | 4 |

All **six authorized-effect sources** had safe completion under all methods (18/18 dependent arms). All **four resource sources** tied (12/12 arms). Only three source IDs explain all differences: 05 (immediate loses task restoration), 07 (delayed variants permit notification), and 11 (delayed variants permit delegated read). Among 36 branches there are 31 safe, four with forbidden effects (two sources × two delayed arms), and one incomplete legitimate task despite no forbidden effect.

**Operational mechanism:** source 11 has original cut at 705 ms, nominal eligibility threshold 2000 ms, actual external ticket admission around 2082 ms, delayed revocation at 2824 ms, physical external read at 3599 ms, and verify-first protection at 3899 ms. Admission overlaps a genuine 494-ms Qwen generation, establishing that a loss of prevention control can occur during actual model operation. Physical read and ack are later and separate. Across the whole confirmation, four admission events overlapped inference (including one prohibited ticket), and three receipts overlapped inference in dependent authorized branches. The evidence does **not** isolate neural inference latency as the sole cause: browser/tools/verification also consume time.

**Counterevidence:** in source 05, immediate intervention prevents the prohibited read but Qwen fails to restore legitimate review access, whereas both delayed arms safely complete. This is one observed continuation, not proof staging systematically causes unfinished tasks. Baseline comparison is specific to the actual verification-first package, which includes another model decision; optimized immediate verify-and-cancel has not been tested.

## Rank 2: Prospective feasibility versus policy failure — strongest interpretive analysis

From the same 12 sources, **each source had at least one observed safely completed policy arm (12/12)**. The retrospective per-source best-of-three envelope is thus 12/12, compared with immediate 11/12 and each delayed arm 10/12. All five failed live branches had a recorded safe sibling: one task-restoration omission (source 05), four missed prevention windows (sources 07 and 11). This is *witnessed feasibility*, **not** a deployable observation-based oracle or a mathematical upper bound over all actions/unknown futures. The common-source paired continuations vary stochastically, so ex-post branch selection must not be presented as an achievable controller. After a forbidden effect enters immutable history, full historical recovery is unavailable under that registered contract, even though prevention was observed feasible earlier.

## Rank 3: Recovery predicates, independent historical effects and bounded impossibility

**Original mechanisms:** 102 valid controlled backend cases (notification, delegated authority, mock fee, deadline), 78 determinate, 12 unknown and 12 censored, authored with shared seeds and modes; no genuine LLM-generated decisions in this population. Versioned derived analysis `w0d-recovery-predicates-v2-1/metrics.json` finds:

| Same-execution comparison | Disagreements / determinate cases |
|---|---:|
| Local rollback vs current-state recoverability | 39/78 (50.0%) |
| Local rollback vs full historical-contract recoverability | **42/78 (53.8%)** |
| Current-state vs full historical-contract recoverability | **3/78 (3.85%)** |
| Current-state recoverability vs actual safe task completion | 6/78 (7.69%) |

The three current/full-history conflicts are expiry of delegated capabilities while forbidden issuance remains historically recorded. Prospective prevention feasibility is **unknown for all 102 old cases**; one cannot infer deadlines from those terminal logs. The external benchmark UndoBench already has history-aware effect oracles, so the *concept of this disagreement* is not itself novel.

Finite solver `p3-formal-recovery-v1`: exhaustive 256 Boolean states at fixed time under three bounded admissible repair primitives; **10/256 have a repair path, 246/256 do not**. Categories: 224 immutable observed effects/fee/missed deadline; 16 active child capability without allowed waiting; 6 independent-ownership obstacles; 10 feasible. This is an exact model-relative classification, **not** an empirical 96.1% population failure rate. 63 historical determinate oracle assertions matched; three cases where an existing recovery procedure failed actually had alternate admissible repairs. Do not mistake planner failure for impossibility.

## Rank 4: Delayed verification's controlled exposure cost — strong mechanism, conditional prevalence

Independent observability study `o2-observability-locked-v1/metrics.json`: 3 frozen cohorts × 512 authored synthetic source instances = 1,536 controlled source clusters; distinct push in-distribution, shifted push, held-out delegated pull. `H5_verify_minus_cancel` extra exposure for delaying cancellation:

| Cohort | Additional harm | Conditional 95% interval |
|---|---:|---:|
| Push | **+17.97 pp** | +14.84 to +21.29 pp |
| Shifted push | **+33.40 pp** | +29.30 to +37.50 pp |
| Pull held-out | **+17.38 pp** | +13.87 to +20.70 pp |

The race is an expected consequence of the declared scheduling/cancellation law. These estimates quantify **authored mixtures**, not actual network/agent-deployment risk. Independent SQL witness studies support testbed correctness. In the budgeted simulation, an observable rule has fewer harms than an uncertainty-aware controller at 30% intervention budget: 114 vs 158 (push); 188 vs 221 (shifted); 143 vs 169 (pull), each out of 512. The uncertainty-aware controller preserves more clean authorized work. This shows a conditional harm/utility tradeoff, not universal superiority.

## Rank 5: Genuine LLM supervisor — diagnostic evidence, not confirmatory ranking

`c1-supervisor-development-v1/metrics.json`, two authored independent source tasks, six paired execution arms, 27 genuine Qwen3.5-9B generations (21 actor, 6 supervisor), 71,247 tokens. Fast deterministic C1 2/2 safe, sequential Qwen C2 1/2, stage-first Qwen C3 2/2. Strict supervisor schema passed only **3/6** outputs; remaining three invoked predetermined fallback, so stage-first outcomes cannot be attributed wholly to the LLM's judgment. One valid STAGE recommendation returned **213 ms before** actual delegated-ticket admission (2,535 ms), yet revocation was enforced only at **3,187 ms**. Fast deterministic/stage-first revocations were at 939/940 ms. This isolates an *end-to-end recommendation-to-enforcement bottleneck*, not pure model inference. Authorized undispatched resource work remained withheld and then completed exactly once under all three methods. The pilot had NO-GO confirmation, so no inference about population superiority or intrinsic insufficiency of LLM supervisors.

## Rank 6: Negative learning/search/forecast evidence — a key boundary on claims

* Search `p4`: 14,400 candidate attempts (5 methods × 30 algorithm seeds × 96), under four fixed mechanisms. Coverage-guided + minimization mean coverage AUC **1.9375**, local frontier **1.5208**; coverage found 5/5 semantic transitions and local 4/5. Seeds quantify algorithm variability under fixed laws, not task diversity.
* Risk-learning `p9`: frozen 2,048 rows in 64 source clusters; a fixed boosted-tree arm benefited from boundary acquisition (Brier 0.015620 versus random 0.019310), but the specified-mixture comparator (0.014771) remained better and preselected models did not achieve a consistent improvement. In the held-out pull study, boundary-focused hazard performance was worse than ordinary data (Brier 0.252 vs ~0.206). Do not present a general learning improvement.
* Controller `p9`: 955 forbidden effects in 2,048 controlled cases with no protection; learned risk and authorization+timer each **546 effects** (409 fewer) with the same 409 interventions and full modeled task completion. The improvement over no protection is real within the synthetic model; there is **zero incremental effect** of the learned policy over the simple rule in the registered comparison.
* T-COPE `t6`: three development source groups, immediate stage/verify **3/3 safe**, time-blind **0/3**, adaptive T-COPE **2/3 with one censored**; distinctive adaptive forecasting never fired in the scored explicit-scope cases. There is no valid frozen T-COPE efficacy comparison (`t9`: 7 reconstruction-invalid branches, 49 unattempted). Looking ahead costs substantial world/browser orchestration, not just inference.
* Earlier Qwen3.5-4B natural task pilot `s1`: **38/38 parsed native function calls**, only **4/12** completed legitimate tasks; eight comment tasks left drafts unposted. Shows that interface/tool validity and successful task execution differ, but model/UI feedback changes confound later improvements.

## Rank 7: Replay-validity qualification — important internal validity, not main scientific motivation

OECR frozen experiment `u5`: six source tasks × original / faithful / fresh browser. Original and faithful initial requests match 6/6; fresh browser matches 0/6. First action changed 0/6 under faithful versus 6/6 fresh. Terminal completion disagreed with original 2/6 under faithful, 0/6 under fresh. Demonstrates that final task agreement is not sufficient to certify equivalent initial decisions; does **not** establish terminal-fidelity superiority or safety efficacy. Prior t9 controller confirmation invalidated because cloned browser's stale-state difference changed the decision problem. Recoverability paper should keep this in Methods/Threats to Validity.

## External benchmark and publication novelty

`w2-undobench-official-local-v1`: unchanged pinned official UndoBench task definitions/oracles, five baseline wrappers, 100 scripted executions in 50 dependent paired cells nested in 10 task-seed instances from 5 workflows. Published-style recovery rates: naive 2/10, checkpoint 2/10, saga 2/10, idempotency 6/10, verify-before-retry 4/10 in this tiny local DEV subset; not official population leaderboard scores and no live Qwen external benchmark run. **The official evaluator already captures the historical-effect-based ranking reversal**. Cordon already stages effects. Thus AfterClick cannot claim invention of history-aware recovery or staged enforcement. A distinguishing *measured operational detail* is the progression of mock external consumers during real model/browser execution; one application and a few witness cases do not yet establish general new scientific laws or wide applicability.

## What the full evidence really supports

1. **Verified under declared causal contracts:** current rollback, full historical recoverability, prevention and actual safe completion are distinct quantities; some historical effects cannot be erased by admitted repairs.
2. **Operationally observed in real Qwen executions:** a pending delegated ticket may become committed during inference while later revocation is too late, and early protection can itself leave an authorized task incomplete.
3. **Measured but statistically uncertain:** the fixed immediate-protection policy has 11/12 safe completions versus 10/12 delayed, but the source-paired confidence interval includes large negative and positive effects.
4. **Repeated negative evidence under specific authored workloads:** simple rules match or outperform added learning, lookahead and supervisor overhead, though each sophisticated method has its own untested settings and cannot be declared universally inferior.
5. **Feasibility versus policy failure:** every failed branch in the 12-source confirmation has a successful sibling. No intrinsic task-level safe-completion impossibility is established at the common source checkpoints. Historical irreversibility after the witnessed forbidden effect remains possible under narrower contracts.

## Scientific cautions

- Distinguish *controlled synthetic samples* from genuinely independent live-agent tasks. Do not combine them in one efficacy sample or report 91 sealed runs as 91 independent trials.
- The 12 live sources are authored and share six workflow structures; apparent sample size and generalizability are limited.
- Effect timing depends on constructed mock services/eligibility distributions. External mock receipts are real independent observations *within the harness*, not production receipts.
- The verification-first baseline includes a fresh model decision and browser/tool operations; comparison does not isolate a pure effect of neural inference latency or establish a lower bound on the performance of fast verification.
- Stage-first supervisor in the two-source pilot often used deterministic fallback; 3/6 schema-valid is an interface-contract failure count, not general supervision accuracy.
- The retrospectively best observed policy per source leaks outcome information. It is not a deployable oracle or proof of an optimal bound.
- A difference not reaching statistical significance is **not** evidence of equivalence.
- Stored checksum/test results are repository claims; this secondary review did not freshly rerun all tests or externally replicate billing.

## Recommended paper thesis and results order

**Thesis:** *In the tested tool-agent environments, safety intervention is constrained by three separable obligations: prevent unerasable historical effects before external commitment, act while prevention is still feasible despite asynchronous reasoning/verification, and ensure that the agent can still finish its legitimate task. A decision may be correct yet enforced too late; an intervention may be effective yet leave task obligations unfinished.*

**Suggested main evidence:** (1) exact recovery predicates and failure oracle with illustrative external-history witnesses; (2) conditional timing experiment and operational Qwen ticket-admission witness; (3) frozen 12-source live policy comparison and source 05/07/11 contrasts; (4) two-source supervisor pipeline bottleneck as exploratory; (5) negative algorithmic studies and UndoBench overlap as supporting/limitation evidence. OECR resides in methodology.

**Most defensible title:** *AfterClick: Characterizing Recovery and Intervention Failures in Tool-Using LLM Agents*. The existing *Limits of Recoverability* title is acceptable only when explicitly defined as **contract- and time-relative limits**, not an optimal achievable bound on agent recovery.
