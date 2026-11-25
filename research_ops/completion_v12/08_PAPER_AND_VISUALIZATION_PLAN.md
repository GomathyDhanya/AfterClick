# 08 — Paper, visuals, comparison to prior art

## Default framing

**AfterClick: When Safe Decisions Fail to Produce Safe Outcomes**

*Timing, Irreversible Effects, and Task Obligations in Tool-Using LLM Agents*

Choose final title after complete findings. If results do not establish outcome-level failures despite decision correctness, prefer **AfterClick: Measuring Action-to-Outcome Safety in Asynchronous Agent Workflows**. Do not call it "The Limits of Recoverability" unless the paper clearly states the admissible operation set for all purported impossibility claims.

## Paper skeleton

1. **Introduction.** A tool action may appear correct, yet workers continue during reasoning, commitments become irreversible, and remaining obligations persist. State precise gap and counterexample, without generalizing from an anecdote.
2. **Related work.** Compare UndoBench, Cordon, AgentRewind, Safe to Resume?, SURE-Act, Async-RBench, ReInBench, AppWorld, tau2-bench, safety shields and Sagas. Include what each already solves and why our exact measurement differs.
3. **Problem definition.** Partially observed task state; actions, consequences, receipts, external event transition, safety contracts, obligations, interventions, clock model. Define goal, history-aware safe completion, weak/robust reachability.
4. **System and benchmark.** Both real applications, task families, independent task authoring, complexity rubric, external receivers, independent oracles, verified safe reference paths, limitations.
5. **Methods and preregistration.** Agents, policies, clones, freeze, sample, model revisions, clean baseline, timing regimes, randomization, qualification, invalidity.
6. **RQ1 results.** Graph coverage and faithfulness; exact and witnessed frontiers; case studies with provenance, not universal claims.
7. **RQ2 results.** Effective enforcement vs recommendation time, information value, sequential reasoning, real deadline sweeps and uncertainty.
8. **RQ3 results.** Joint safety–completion, restoration, false blocking, obligations; model and app heterogeneity.
9. **Generalization and external evaluation.** Official unchanged benchmark scores; second app/model; limitations and differences in task definitions.
10. **Threats/limitations and ethics.** Constructed fake receivers, limited deployment realism, assumption-sensitive proofs, incomplete observability, model/provider differences, uncertain human difficulty.
11. **Conclusion.** Report bounded lessons, nulls, and the action-to-outcome evidence gap; avoid promising a new optimal controller.

## Essential paper figures

**Figure 1: Environment-aware trajectory example** — real model actions, controller recommendation, gateway implementation, worker admission, physical effect and outstanding obligations synchronized by time. Contrast early/late after certified common cut. Include exact evidence IDs.

**Figure 2: Recoverability graph** — witnessed vs formally certified vs untested edges; current-state repair vs historical violation separately colored/marked. Prefer one multi-state complex task, not just the old simple 5-step examples.

**Figure 3: Clean competence versus deadline stress** — joint safe completion and legitimate competence by task complexity, families and model, with task-cluster intervals; explicitly distinguish baseline schedule from ordinary stressed schedule.

**Figure 4: Information value versus lost actionability** — fast rule, fast verify and extra Qwen decision across verified authorization-ambiguity and deadline regimes, with true effective-action timing and uncertainty.

**Figure 5: Review-to-enforcement delay waterfall** — per-component actual durations and the observed fraction of lost protection windows; annotate overlap and 95th percentile.

**Figure 6: Safety–utility and obligations** — scatter or paired plot of forbidden effects versus legitimate completion plus explicit restoration-feedback effect, with false intervention rates and cluster bootstrap intervals.

**Figure 7 (appendix): Generalization** — effect estimates across application, model, mechanism and official external benchmark, clearly separating non-comparable raw scores.

**Additional appendix:** all task contracts/IDs and provenance; failure taxonomy with full source matrix; agent trajectory repetition; UI feedback control; supervisor schema errors; exact finite solver proof summary; full raw timing distribution; prior learning and frontier negative results; dev/holdout split and full analysis script/requirements.

## Thought experiments to convert into executed, falsifiable contrasts

- An instantly responding model with unchanged gateway: use actual controlled replay, not only subtracting time.
- A correct recommendation held until after the worker commits: replay gateway delay and measure late protection.
- Two worlds with identical allowed observations but different hidden consequences: validate explicit observation aliasing and robust feasibility lower bounds.
- A safe prevented action that leaves mandatory authorized access unrestored: test public obligation feedback.
- A controller that blocks everything: show that forbidden effects can fall to zero while legitimate completion also collapses.
- A fast rule on explicit vs ambiguous authorization: show when additional evidence is truly informative versus merely costly.

## Publication claim-to-evidence requirements

For every introduction/abstract claim, specify: metric, independent unit, sample size, model/app, observed effect, uncertainty, an explicit comparison baseline, exact raw artifact paths and analysis script hash. Any title-level generalization must be supported by multiple apps/models or framed conditionally. Qualitative trace examples cannot be turned into population rates. A null main comparison cannot be called policy equivalence without an actual equivalence/noninferiority design.

## External method comparison honesty

Use primary implementations and original oracles wherever possible. A proxy for Cordon-like staging is **not** Cordon. An official UndoBench evaluator already detects history-aware failures; AfterClick must provide a meaningful complementary dimension, not rebrand an existing metric. Async-RBench already studies asynchronous tasks; contrast *independent external commitment during genuine model execution and recoverability of the resulting histories* only if substantiated with the actual paper, not from superficial abstract comparison.
