# AfterClick: When a Database Clone Changes an Agent's Decision Problem

Completed bounded evidence report, 24 November 2026. New results are separate from the frozen recovery-boundary, observability and TCOPE studies. Publication novelty is not assumed.

## Abstract

Counterfactual agent evaluations require more than matching database records. A browser may contain stale values, unsaved changes, queued updates and pending tool results. We study application-specific observation-faithful reconstruction in AfterClick, using real PostgreSQL, Chromium and controlled fake services. The local qualification preserves seven supported cuts, rejects unresolved transport and corruption, and shows that copying the visible draft alone can change subsequent autosave behavior. In a frozen six-source, two-template confirmation, faithful reconstruction preserved all six initial requests and first actions, while fresh-browser cloning changed all six first actions. However, primary completion disagreement was 2/6 for faithful replay versus 0/6 for fresh clones: improved terminal-outcome fidelity was not supported. Saved-trace falsification exposed fresh-identifier and serving-variation confounds. The contribution is a bounded empirical validity study, not a new theory of checkpointing or an established safety algorithm; publication-level novelty remains unestablished.

## 1. Motivation and previous evidence

The earlier frozen TCOPE confirmation reconstructed database state correctly but rejected seven branches because the source browser still displayed Priority Normal while fresh clones displayed High. Forty-nine planned branches were not attempted. The gate prevented an invalid efficacy comparison. Earlier development used 221 genuine 9B generations across 13 source instances; immediate stage/verify and fixed protected lookahead each completed 3/3 safely, while TCOPE completed 2/3 with one administrative censor. Adaptive forecasting was not exercised in those scored groups. These tiny development counts do not establish equivalence or an algorithmic advantage. The old artifacts and manuscript remain unchanged.

## 2. Closest related work

[Safe to Resume?](https://arxiv.org/html/2608.29381v1) already identifies incomplete and inconsistent execution state; [AgentRewind](https://arxiv.org/html/2608.14380v1) aligns agent context with its controlled recovery boundary. [SURE-Act](https://arxiv.org/html/2610.24194v1) evaluates executed alternatives from cloned checkpoints under a frozen backbone. [Cordon](https://arxiv.org/html/2606.17573v1) mediates staged effects, while [UndoBench](https://arxiv.org/html/2610.05622v1) separates recovery evaluation from ordinary completion. These are substantial overlaps, not methods reproduced in our comparator. Detailed scope and limitations are in `research_ops/NOVELTY_MATRIX.md`.

Distributed process/channel state and consistent global cuts are established by [Chandy and Lamport](https://lamport.azurewebsites.net/pubs/chandy.pdf). The value of computation is established metareasoning, including [Russell and Wefald](https://doi.org/10.1016/0004-3702(91)90015-C). We make no priority claim for these concepts.

## 3. Problem and formal definitions

Let a decision checkpoint be X=(B,C,Q,H,M), where B is backend state, C is application client state, Q is pending client update/timer state, H is the historical external-effect ledger and M is the native model conversation including unresolved tool identifiers. Let O(X) be the model-visible allowlisted browser observation. Backend equality B=B' is weaker than observation equality O(X)=O(X'). Observation equality is in turn weaker than continuation equivalence: identical visible drafts may have different dirty buffers or base revisions and therefore different subsequent writes.

For a declared action/event set A and finite horizon h, scoped continuation equivalence requires matching public traces and relevant world outcomes under matched input sequences. Our finite tests are witnesses for specific sequences, not a proof for all A or all h. A valid comparison additionally requires identical conversation state and preserved historical receipts. A hash proves artifact integrity only; it does not prove scientific equivalence.

Recoverability at a time means that an allowed intervention can still prevent the specified historical effect under the defined environment. Its occurrence time, observation time and prevention deadline may differ. This new study evaluates reconstruction and bounded task continuation, not an estimate of irreversible recovery efficacy. Unobserved or pending effects are not labeled safe.

## 4. System and threat model

The original FlowBoard frontend, backend and frozen experiments remain intact. An opt-in research build instruments application state. PostgreSQL schemas are isolated and disposable. Fake external observer receipts are immutable. New schema construction is a counterfactual setup operation, never a recovery primitive. The policy receives visible controls/text, task instruction and public action history only; hidden schedules, certificates, source identifiers and private target contracts stay outside its input.

The testbed is trusted and synthetic. The serializer is application-specific. It does not capture arbitrary browser heap objects, network sockets, browser extensions or external production services. We reject unresolved transport. Resolving a delayed request and capturing afterward is an explicitly different consistent-cut alternative.

## 5. Method and implementation

At the declared controlled-clock cut, pause client update application and pending autosave timers; reject in-flight writes or refreshes. Capture React tasks/draft, base revisions, dirty buffer, operation identity, UI status, connection status, cached activity/comments/notices, session identity, SSE cursor/queue, relative timer remainder and model conversation. Read a repeatable database snapshot and verify that the world does not change across observation capture. Store a canonical hash envelope.

Initialize a separate schema with the captured world and fake-effect history. Bootstrap the instrumented client without a fresh server read. Resume the SSE stream after its captured cursor, preserving queued messages. Compare current database, public observation, client fields and conversation exactly before allowing a faithful continuation. Pending timers retain relative duration at the controlled cut. This is a finite application-level reconstruction, not an OS snapshot algorithm.

The fresh-browser comparator copies the same database and opens the same app without client bootstrap. Its mismatch is expected and recorded. It is not admitted as a causal safety sibling; executing it diagnoses how a changed decision problem can alter evaluation results.

## 6. Local qualification and falsification

u0 contains eight prespecified conditions: synchronized state, stale collaborator state, pending autosave, delayed SSE, delayed acknowledgment, corrupt checkpoint, pending native-result state and an external effect committed but not visible. Seven supported cuts pass exact checks; the corrupted artifact and original in-flight transport state are rejected. The delayed-ack case additionally reconstructs at a later resolved cut. Fresh-browser observations differ in 4/7 reconstructable cases.

Pending autosave commits once in source and clone. A queued SSE update changes stale Priority to the committed value on resume. Historical receipts survive while public state remains stale. A targeted DOM-only ablation preserves visible draft text but removes dirty fields; the initial observation matches while subsequent autosave loses the intended change. Thus initial text equality alone does not certify executable behavior.

Development failures are retained: missing JSX compiler configuration, inconsistent capture under an advancing backend clock, and replayed SSE events after reconnect. These are engineering errors, not favorable scientific outcomes. A mock three-world driver checks the public model boundary; it is not genuine LLM evidence.

## 7. Real model setup and independent oracle

All live requests use the existing Qwen/Qwen3.5-9B endpoint, API name AfterClick, revision c202236235762e1c871ad0ccb60c8ee5ba337b9a, unchanged native function tools and corrected public-commit policy. Temperature 0 does not guarantee determinism. No new reasoning option, prompt tuning or endpoint deployment is introduced. Each continuation has at most 4 model calls, 16384 input and 512 output tokens per call, one concurrent request and no retries.

Source cuts are scripted concurrency fixtures, not organically arising agent mistakes. Subsequent proposed actions are fresh model generations and execute through the authorized Gateway. Original, faithful and fresh conditions share the source task and frozen world; arm order is preregistered. Backend time is paused during inference in every arm. Browser timers and PostgreSQL writes remain active. This isolates reconstruction from inference-time deadline loss, and limits the resulting claim accordingly.

The post-run verifier checks committed SQL fields and comments independently of model completion claims. Priority-recording tasks are judged against the originally displayed label; we also report raw content because refreshed browsers may satisfy their own changed observation. Description tasks must append the requested suffix while preserving collaborator text and unrelated fields. Safety is not inferred from absent receipts with a paused scheduler.

## 8. Results, cost and uncertainty

The independent cohort was frozen as u4 before outcomes, with six new seeded source instances from two templates (three Priority and three Description), one application and one stale-client concurrency mechanism. There are four distinct task instruction strings; repeated Priority tasks are not three independent task designs. u4 warmed the endpoint but made zero generations because a public-task allowlist ordering mismatch failed admission. u5 retained exactly the same cases, prompt, tools and scientific sources; a documented execution amendment sorted the allowlist and changed the wall envelope from 420 to 540 seconds at the unchanged $1 cap. Its first admission attempt rejected expired financial evidence before reservation; refreshed evidence admitted the run. No outcome-based selection occurred.

All 18 continuations completed: 12 initial-certificate-valid original/faithful continuations and six deliberately invalid fresh-browser diagnostics; zero censored or unknown. The six faithful branches are genuine new model-generated counterfactual continuations. Source creation and concurrency are scripted. No organic policy-error frequency is estimated.

| Outcome | Original source | Faithful reconstruction | Fresh browser (invalid sibling) |
|---|---:|---:|---:|
| Initial exact certificates | 6/6 | 6/6 | 0/6 |
| Original-target task completion | 3/6 | 5/6 | 3/6 |
| First-action disagreement with source | — | 0/6 | 6/6 |
| Completion disagreement with source (primary) | — | 2/6 | 0/6 |
| Chronological final-content disagreement | — | 2/6 | 3/6 |
| Genuine generation calls | 24 | 22 | 15 |
| Total inference seconds | 11.639 | 11.194 | 7.239 |
| Total browser execution seconds | 31.748 | 29.122 | 7.395 |
| Total reconstruction seconds | 0.961 | 6.252 | 6.274 |

The preregistered stronger completion-fidelity prediction is unsupported and points in the opposite direction: fresh-minus-faithful completion disagreement is -2/6 (-33.3 percentage points). The faithful arm's 5/6 completion is not evidence of more faithful terminal behavior, nor a safety gain. Fresh-browser first actions differ in all six sources despite matching the original aggregate completion rate. Thus completion alone can conceal a changed decision problem. Initial faithful requests are exactly equal to their paired originals and their first actions match all six; this bounded first-decision finding is the strongest positive evidence.

Per-template detail: all Description arms complete 3/3. Priority originals complete 0/3, faithful 2/3 and fresh 0/3 against the original-label/exactly-one-comment target. Source 01 and faithful both post Normal then High; sources 03 and 05 also post twice, while their faithful counterparts post only Normal. Fresh arms post High. Repeated comments are model-selected actions, not parser retries. A fresh browser's High comment may be locally correct for its refreshed screen; the private original-source contract explains why this is a different estimand, not intrinsically unsafe behavior.

![Validity and task completion](../artifacts/research_runs/u7-oecr-identity-audit-local-v1/figures/oecr-counts.png)

![Paired disagreement, corrected chronology](../artifacts/research_runs/u7-oecr-identity-audit-local-v1/figures/oecr-disagreement.png)

### Statistical interpretation

Descriptive source-level Wilson 95% intervals for first-action disagreement are faithful [0,0.390] and fresh [0.610,1]. For completion disagreement they are faithful [0.097,0.700] and fresh [0,0.390]. These marginal intervals are not a paired test. Source dependence within two templates makes population inference especially weak. The posthoc template-cluster resampling sensitivity range for the paired completion contrast is [-0.667,0]; for content [0,0.333]; for first action [1,1]. With only two clusters, even a degenerate range is not confidence in generalization. No p-value, equivalence proof or claim of population superiority is made.

### Saved-trace falsification and disclosed analysis correction

u7 checks all six initial request pairs and 22 available paired request turns. Thirteen later requests after equal preceding action sequences differ only in fresh tool-call IDs and UUIDs under diagnostic normalization; three precede action divergence. The normalization is analysis-only: no original request is modified or resent. Fresh identifiers and serving variability remain competing explanations. This cannot causally attribute divergence to UUID sensitivity or rule out unmeasured execution state.

The frozen v1 analyzer compared comments in UUID row order. Two saved rows differed from numeric committed-event chronology, cross-checked against the comment multiset. The original u5 summary/figures remain sealed. u7 publishes an explicitly versioned chronological correction: faithful content disagreement changes from 3/6 to 2/6. Primary completion, first actions and initial certificates are unchanged. This correction was not used to tune the model, source tasks or runtime.

### Cost and latency

u5 used 61 genuine generations, 146,543 tokens (143,148 input; 3,395 output), and 315.514 seconds including startup and shutdown. Its conservative ledger charge is $0.57001343. Calls vary because policies finish at different turns under the same four-call cap. These are matched ceilings, not equal realized computation. The table separates reconstruction and browser execution from inference latency. Backend clock pausing excludes any claim about deadline loss during reasoning.

Across all new live runs, including failures, there are 80 genuine generations and 191,182 tokens across eight seeded source instances (two development, six confirmation). Eight completed faithful counterfactual continuations have exact initial certificates (two development, six confirmation); this does not certify arbitrary subsequent trajectory identity. Together with the earlier archive, the separately labeled ledger contains 301 generations and 799,289 tokens. Historical and new studies are not pooled for efficacy.

The OECR effort consumed $3.169206 in conservative ledger charges, including failed runs; cumulative charges against the original $20 additional authorization are $8.032933. Conservative remaining credit is $20.077067, above the $8 reserve. These are guarded estimates, not isolated invoices. The latest read-only provider summary reports $8.20609678 account metered usage, $0 billed, and $0 token-API usage; the prior higher meter $8.47610194 is retained because billing is asynchronous. Workspace cap remains $14 and effective default cash limit $0. No endpoint was created. Existing endpoint ep-Lqp751voQWfhhoZTNXD4Yf was restored to min0/max1/buffer0/idle2 and zero containers verified.

Financial incident: during u2 the host slept for 885 seconds while min1 remained configured. Monotonic elapsed time omitted suspension; cleanup then encountered timeouts. Readback after protective min0 restoration found no containers. The account delta through cleanup was $1.49003454, exceeding the $1 run ceiling. A 1,250-second UTC upper bound and margin yield a $1.989756944 guard charge. The trajectories category reached $3.441710297 against its $3 cap and is closed to further paid collection. This was a safeguard failure, not compliant spending within that category. Later confirmation used its separate authorized category, an active sleep inhibitor, UTC-inclusive accounting and min0 after readiness. The original incident evidence and accounting amendment are preserved; no limit was raised or reset.

## 9. Limitations and threats

One application and two authored task templates cannot establish broad mechanism generalization. Sibling continuations are dependent; source instances from shared templates are also related. Any source-level confidence interval is descriptive under an independence assumption, not a population claim. Native inference can vary despite temperature0. A changed first action need not change final completion; convergence is contrary evidence to a stronger downstream-effect claim. Correct updated information is not intrinsically unsafe: the issue is whether a purported sibling preserves the original decision problem.

The controlled cut omits real-time hazard competition. Local exact checks are finite witnesses, not bisimulation proofs. In-flight transport remains unsupported. The negative control is our own fresh-browser clone, not a head-to-head comparison with complete external replay frameworks. Prior work already addresses the general state-completeness problem; the novelty verdict must remain limited accordingly.

## 10. Reproduction and conclusion

See `docs/OECR_REPRODUCIBILITY.md`. Raw protocols, model journals, browser traces, snapshots, certificates, failures and seals are under `artifacts/research_runs/u*`. All 305 local tests pass (one upstream deprecation warning). Both original and corrected saved-data analyses reproduce exactly; frozen historical/scientific hashes and sealed evidence are checked. Historical frozen results remain separate. Observation-faithful reconstruction is a necessary admission check for the controlled comparisons tested here, but it is not sufficient to guarantee final behavioral identity. We stop without claiming improved controller safety or a novel algorithm.

## 11. Failure analysis and alternatives considered

u1 made one generation before a public-history shape mismatch stopped the harness; it is invalid, not a successful task. u2 made 18 calls, completed five arms and censored one during host suspension; only one complete three-arm development source is available. Local fixes targeted observable defects: compiler configuration, inconsistent capture under advancing clocks, duplicated SSE replay after reconnect and malformed public history. No frozen historical run was changed. u4's zero-generation failure and u5's pre-reservation expired-evidence rejection remain archived. u2's financial incident is disclosed above.

An observation-only DOM reconstruction is weaker than executable reconstruction, as the dirty-buffer ablation demonstrates. The fresh-browser comparator is effectively database cloning plus ordinary initialization; a database alone is not an executable browser-agent baseline. A later resolved consistent cut handles the delayed-ack case but changes the intervention point. We therefore do not manufacture five nominally distinct full live baselines. Complete external replay frameworks were not reproduced.

The intervention-selection, partial-observability and TCOPE candidates were assessed in the hypothesis portfolio. Existing explicit authorization and enforceable staging often settle the available choices before lookahead can add value. The current evidence neither activates the adaptive forecast nor identifies a genuine uncertain task where it beats immediate protection. Creating artificial uncertainty to activate it would change the claim. We select the bounded replay-validity result and stop tuning.

## 12. Scientific claim–evidence matrix and novelty verdict

| Claim | Evidence | Verdict and strongest challenge |
|---|---|---|
| Database equality need not preserve the agent's decision problem | Historical t9 rejection; u0 local cases; u5 fresh 0/6 exact and 6/6 first-action mismatch | Supported for this app/fixture; already consistent with distributed-state literature |
| Capturing client state preserves tested pending behavior | u0/u3 autosave, queued SSE, history, conversation tests; DOM-only ablation fails continuation | Supported finite witnesses; not universal heap or network reconstruction |
| Faithful initialization preserves the first model decision | u5 six exact initial requests, 0/6 first-action mismatch; u7 audit | Bounded support; two templates and one model/app |
| Faithful replay improves terminal completion agreement | u5 primary disagreement 2/6 versus fresh 0/6 | Unsupported; strongest measured completion comparator is fresh despite invalid sibling state |
| Exact initial state guarantees identical complete model trajectories | Later divergence and u7 identity audit | Not established; identifiers and serving noise remain confounded |
| OECR improves realized irreversible safety | Backend scheduler paused; no matched safety trial | Not tested by this study |
| TCOPE beats immediate staging | Prior development favored/tied simple staging; invalid t9 final | Not established; unchanged historical conclusion |
| New general snapshot/replay/active-reasoning principle | Closest primary literature substantially overlaps | Rejected as a novelty claim |
| Application-specific empirical replay-validity contribution | Code, independent SQL witnesses, real Qwen traces, failure taxonomy and frozen paired cohort | Limited supported systems evidence; publication novelty unestablished |

The report's final question is when a reconstructed browser presents the same decision problem to an LLM. We demonstrate a concrete failure of fresh initialization and a scoped executable remedy, then retain a negative primary terminal-fidelity result. This is a complete bounded research outcome. A multi-application generalization study with controlled identity streams and repeated provider samples would be needed for stronger claims; it is not authorized or queued here.
