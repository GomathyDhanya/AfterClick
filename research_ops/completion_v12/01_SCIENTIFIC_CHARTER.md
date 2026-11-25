# 01 — Scientific charter: what must be shown

## Core problem

A tool-using LLM may issue an action that appears locally valid, yet its consequences become unacceptable because of asynchronous external commitment, unavailable information, delayed enforcement, or unfinished authorized work. The central object is the **time-indexed set of safe futures remaining** after each agent, controller, and environmental event.

A safe future is not defined by one reference action sequence. It is defined by a contract over authorized behavior, task obligations, effect histories, and allowed repair actions.

## Research questions and explicit falsifiers

### RQ1. How does safe-completion feasibility change along real agent trajectories?

- Separate **observed safe continuation**, **exact bounded existential feasibility**, **robust feasibility over specified uncontrollable schedules**, **current-state repair**, and **full historical-contract satisfaction**.
- Compare action-only trajectories with environment-aware action/effect/obligation graphs.
- Evaluate graph completeness, provenance validity, witness correctness, unknown rate, and whether added history actually changes conclusions beyond the best existing history-aware oracle.
- **Falsifier:** graph distinctions add no meaningful analysis beyond baseline event histories, or most real cuts remain unidentifiable with declared operations. Report that without declaring success.

### RQ2. When does information/deliberation help or hurt prevention under deadlines?

- Isolate no verification, fast public verification, verification followed by an additional model decision, and the review-to-enforcement pipeline.
- Compare against strong deterministic authorization and staging; measure both information-dependent decision changes and missed prevention frontiers.
- **Falsifier:** extra reasoning fails to change a choice, or its measured effect disappears after matching observation availability and enforcement timing.

### RQ3. Can intervention preserve legitimate-task completion while preventing forbidden history?

- Quantify protection-induced unfinished obligations, false blocks, unsafe restores, repeated consequential calls, and restoration after temporary intervention.
- Contrast fast protection with/without a **publicly observable** obligation-status check. Test across complex tasks and multiple models.
- **Falsifier:** obligation checks fail to improve joint completion, or apparent gains merely come from supplying hidden ground-truth labels.

### Scope/generalization questions (secondary, preregistered)

How do task complexity, mechanism family, authorization ambiguity, deadline slack, model capability, and application architecture modify the three RQ effects? These are effect modifiers, not license to mine subgroups until a significant result appears.

## Prespecified thesis; not a conclusion

A protective decision and a safe completed workflow are separated by: (i) choosing an appropriate policy under partial observability; (ii) enforcing it while an opportunity remains; (iii) satisfying remaining legitimate obligations. Tests should isolate these factors, including cases where simple deterministic protection is already optimal.

## What constitutes novelty versus established prior art

- **Not new:** history-aware state/effect oracles; rollback/compensation; transaction staging; counterfactual replay; LLM oversight; generic action graphs; dynamically changing tasks.
- **Potential incremental result to test:** controlled measurement of **loss of actionable safe futures** along genuinely model-generated trajectories with independently progressing external effects, verified alternate continuations, and authorized-task obligations, plus causal decomposition of where the protection opportunity was lost.
- **Need to surpass:** simply illustrating time pressure. Quantify frontiers or opportunity sets on multiple realistic workflows and compare to existing capabilities/baselines.

### Mandatory literature comparison (verify current papers and repositories during implementation)

1. UndoBench — https://arxiv.org/abs/2610.05622 — paired recovery/fault competence and history-aware oracles.
2. Cordon — https://arxiv.org/abs/2606.17573 — semantic transactions, staging, delegated authority.
3. SURE-Act — https://arxiv.org/abs/2610.24194 — executed counterfactual selection and cost.
4. AgentRewind — https://arxiv.org/abs/2608.14380 — aligned agent/environment recovery.
5. Safe to Resume? — https://arxiv.org/abs/2608.29381 — rollback continuity/security.
6. Async-RBench — https://arxiv.org/abs/2610.32429 — async task execution, event-response contracts.
7. ReInBench / When to Intervene? — https://arxiv.org/abs/2610.36471 — error and self-recovery traces.
8. AppWorld — https://aclanthology.org/2024.acl-long.850/ — complex, statefully verifiable app tasks.
9. tau2-bench — https://arxiv.org/abs/2506.07982 — dual-control tasks and compositional generation.
10. Existing runtime shield/transaction compensation work (shield synthesis, Sagas), acknowledged without novelty inflation.

For each, state exact evaluated observable, task environments, oracle type, temporal model, whether external effects progress during inference, and which claim AfterClick can uniquely substantiate. Do not mistake an omitted detail in an abstract for absence of functionality.

## Scientific honesty rules

- Use **independent source contract** as highest-level inference unit; branches, tokens, service receipts, and repeated seeds are nested observations.
- Clearly separate scripted tests, controlled simulated timing, real HTTP/SQL workers, genuine Qwen decisions, and external benchmark trials.
- Do not label the hindsight best-observed sibling an implementable oracle policy.
- To claim impossibility, state the admissible action set, horizon, observation model, and scheduler assumptions. Where unspecified, use UNKNOWN.
- Keep all null results. Do not choose positive tasks for final confirmation or stop once p becomes small.
- Final title and claims must fit results; a failed novelty case still produces a faithful characterization paper.
