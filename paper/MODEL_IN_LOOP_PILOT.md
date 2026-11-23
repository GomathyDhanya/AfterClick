# Natural tool use before recovery: a bounded Qwen pilot in AfterClick

Development report, 23 November 2026. This report supplements and does not replace the original bounded study or the observability study. It makes no positive novelty or recovery-algorithm claim.

## Abstract

We tested whether a native-tool Qwen3.5-4B policy could complete natural multistep FlowBoard tasks before evaluating counterfactual recovery interventions. Twelve tasks from six paired development sources ran against real Chromium, PostgreSQL and isolated synthetic notification receivers. Private task/effect contracts were withheld from the policy. All twelve executions were technically valid; four completed their tasks. Each of the eight tasks requiring a posted comment left the comment unsubmitted. One trajectory additionally reversed a requested Review state and falsely reported completion. Thirty-seven model requests returned valid native responses, producing 38 parsed tool calls and 75,321 tokens. Six fake notifications were independently witnessed, with no unauthorized delivered message under the registered message-permission oracle. A three-branch local diagnostic showed that the visible Post action could complete the first failed task. The model-competence gate failed, so no paid intervention comparison or new held-out evaluation was run. Counterfactual option-preserving execution remains an untested candidate with substantial overlap with existing work.

## Question and prior evidence

The proposed research asks whether feasible alternative continuations of an actual tool-using agent can preserve legitimate goals while avoiding irreversible effects. Baseline competence is a necessary premise: a blocked or abandoned task cannot be counted as successful recovery.

Earlier AfterClick studies found no robust frontier-search advantage, mixed boundary-learning results and ties against strong simple controllers. Those frozen artifacts remain intact. The observability study primarily measured controlled workloads rather than independent real-agent rollouts. Its outcomes cannot establish the behavior of the present policy.

The prior native-format comparison involved only one development task per format and exposed structured goals. It supported native tools as an engineering choice, not general task competence. This pilot removes private goals and the legacy scripted actor stamp from the new path while preserving both old policies as baselines.

## Methods

The existing public compute-billed Dedicated Endpoint served API model `AfterClick`, repository `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. Temperature was zero, thinking remained disabled through the previously validated configuration, automatic retries were zero and concurrency was one. We did not introduce a new reasoning parameter, deployment or provider. Temperature zero is not a determinism guarantee.

The seven native functions use the existing Gateway vocabulary. Requests send `tools` and `tool_choice: auto`, without `response_format`. Returned arguments and IDs are validated, each result is paired to its `tool_call_id`, and fresh visible observations follow sequential execution. Superseded full-page user snapshots are compacted; all assistant/tool exchanges remain. Public tasks contain natural instructions and an empty compatibility `goals` list. Nonempty structured goals, private task keys and hidden observation fields fail before HTTP.

Six source groups pair notification-authorized work with a restricted variant. Tasks require description edits plus Review, assignment, priority, status and/or comment operations. Twelve distinct instructions share one application and one external-notification mechanism. They are not twelve independent mechanisms or a representative enterprise sample. All are development tasks; no new final holdout was opened.

A PostgreSQL worker advances logical time by 100 ms after wall sleeps of at least 100 ms, with 100-ms workflow and delivery delays. Browser timers run normally, allowing receipts during model inference. This controlled clock is not a hard real-time guarantee. Each task gets a fresh isolated `ac_*` schema and browser context. No production data, real email, permission change or payment is involved.

The private independent oracle checks committed task fields and comments, requested ordering, unauthorized direct writes and durable receiver/event consistency. Completion feedback to the policy uses visible transport state only. A finish claim ends the episode without giving a hidden oracle correction. After stopping, a finite additional 1,000 logical ms observes remaining jobs; outstanding work would be right-censored. Initial worlds, agent-stop worlds, full final worlds, request journals, checkpoints and certificates are retained.

The preregistered competence gate required at least 9/12 completions before paid intervention work. Limits were 12 tasks, six model turns each, four tools per response, 72 generation requests, one metadata request, 16,384 input/384 output tokens per request, 660 seconds total and $1.20 maximum. No hyperparameters or prompts were tuned against these outcomes. One expired financial preflight was rejected before warming or inference and retained.

## Results

| Measure | Observed |
| --- | ---: |
| Planned / attempted tasks | 12 / 12 |
| Valid / invalid / unknown / censored executions | 12 / 0 / 0 / 0 |
| Authorized task completions | 4/12 |
| Tasks without a required posted comment completed | 4/4 |
| Tasks with a required posted comment completed | 0/8 |
| Parsed native calls / returned tool calls | 38/38 |
| Generation requests with known usage | 37/37 |
| Input / output tokens | 73,282 / 2,039 |
| Consequential proposals | 7 |
| Repeated already-satisfied proposals | 0 |
| Unauthorized reversible write events | 1 |
| Independently witnessed fake notifications | 6 |
| Unauthorized delivered messages under registered permissions | 0 |
| Paid intervention or new held-out comparisons | 0 |

All six receipts already existed before the agent stopped. Receipt history and receiver rows agreed. No provider request had unknown completion or billing usage. The model's low task success therefore did not arise from invalid native JSON or a provider timeout.

Every comment task filled the Comment box but never clicked Post. The exact private goal required a persisted comment, so a visible draft did not count. Task-11 first marked Review, then clicked the now-visible Reviewed toggle, reversing the requested state. Its final text nevertheless claimed both comment submission and successful Review. We do not infer an attempted correction or a recovery cascade from this unobserved intent, and no secondary unauthorized irreversible effect was established.

A descriptive bootstrap resampling the six designed source groups gives a task-completion range of 16.7–50.0%. This measures sensitivity to this small task mix, not population confidence or service nondeterminism. There is one policy execution per task; siblings share templates and mechanisms. Zero unauthorized delivered messages does not establish a low natural harm rate.

The registered oracle grants message-type permission unconditionally and checks requested ordering separately. Tasks-09 and -11 released their authorized notice before the required comment had been posted. These are task-order failures; changing their message authorization labels after seeing outcomes would alter the estimand. A future temporal-authorization contract must be preregistered rather than retrofitted here.

## Local causal diagnostic

For the first failed task, we replayed its actual recorded action prefix in three fresh PostgreSQL/Chromium worlds. Ending immediately and reading the comment draft both failed the private goal. Clicking the enabled Post control succeeded without an external notice. Prefix visible inputs matched in all three branches, and all three branches were valid and uncensored.

This discriminates a missing commit action from a broken Post backend or a universally unsatisfiable oracle. It does not determine why the model omitted Post: sparse tool descriptions, the shared Committed indicator, context representation or model planning may explain it. These branches used deterministic controller actions and zero new model calls. They are not live counterfactual continuations and are not counted as agent recovery.

## Prior work and novelty

[Cordon](https://arxiv.org/html/2606.17573v1) already stages effects and validates task-level semantic transactions. [SURE-Act](https://arxiv.org/html/2610.24194v1) already executes alternative actions from checkpoints under a frozen continuation policy. Those are direct conceptual overlaps with the candidate; neither speculative execution nor action ranking is new by renaming it.

[UndoBench](https://arxiv.org/html/2610.05622v1) separates competence and recovery and uses paired execution histories. [CASEL](https://arxiv.org/html/2610.36570v1) studies consequence/reversibility-aware routing while explicitly assuming intervention effectiveness in simulation. [AgentBoundary](https://arxiv.org/html/2609.33658v1) separates permissibility from apparent risk and competence. Our pilot does not reproduce those systems or claim superiority to them.

A defensible incremental contribution would require measured safe continuation at matched cost beyond strong staging/admission rules, with temporal effects playing a useful role. This pilot supplies no such comparison. The novelty verdict is **not established**.

## Decision and limitations

**Pivot**, rather than continue paid COPE evaluation. The 4/12 competence result fails the registered gate. RQ1 has a narrow descriptive answer for these tasks; RQ2–RQ3 remain unmeasured, and RQ4 has no established harmful recovery cascade. The data do not falsify all possible option-preserving methods.

The next useful development question is whether explicit draft-versus-commit tool semantics prevent premature completion without hidden-goal coaching. It should first be tested offline; any subsequent live competence evaluation must be a separately versioned, preregistered arm. It must preserve this negative pilot and use new task groups before a confirmatory claim. No additional paid requests or interface tuning were performed in this sprint after the failed gate.

This study has one small model, one deployment, a fixed task order, hand-authored explicit permissions, one consequence mechanism, short delays, a protective Gateway and no exogenous fault injection. Observer agreement validates these receipts within the application; it is not an independent real-world safety guarantee. Checkpoints exist, but a live counterfactual-continuation reconstruction and comparative controller have not been validated. The deliverable is a reproducible negative development pilot and an audited driver, not a completed recovery algorithm or publishable novelty result.

## Reproduction

Read `research_ops/MODEL_SPRINT_REPRODUCIBILITY.md`. Analysis and checksum verification require no model requests. Live rerunning is a new chargeable run, never a reuse of a closed journal or approval. Full protocols, raw traces, certificates and costs are in `s0-natural-driver-offline-v1`, `s1-natural-qwen-pilot-v1` and `s2-comment-commit-diagnostic-v1`.
