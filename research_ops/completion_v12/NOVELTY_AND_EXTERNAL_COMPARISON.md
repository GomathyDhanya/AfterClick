# Preliminary primary-source comparison — audit incomplete

Primary publication pages were checked on 25 November 2026. Full-text sections
on effect history, staging, and asynchronous delivery were additionally inspected
for UndoBench, Cordon, and Async-RBench. This is a scoped literature refresh;
complete implementation/code comparison, official external TEST execution, and
independent novelty assessment remain unfinished.

| Work | Verified existing contribution | Implication for AfterClick |
|---|---|---|
| [UndoBench](https://arxiv.org/html/2610.05622v1) | Paired nominal/fault runs separate competence and recovery. Its dual evaluator checks final state and complete effect history; its study distinguishes fault locations around mutation and acknowledgment. | History-aware grading, competence controls, and phase-dependent recovery already exist. Our unchanged official external TEST model evaluation is still unexecuted. |
| [Cordon](https://arxiv.org/html/2606.17573v1) | A task-scoped transaction tracks lineage, mediates local changes, and holds external effects in an outbox for validation and release. Its recovery protocol distinguishes pending effects from effects already dispatched. | Staging and provenance graphs are prior art. Our HTTP/browser delay study is a local mechanism experiment, not a reproduction of the original Cordon implementation. |
| [Async-RBench](https://arxiv.org/html/2610.32429v1) | Concurrent subagents return results through a controller with task-state release conditions and timeout fallback. Evaluator-only event-response contracts check changes, preservation, prohibited effects, validation and terminal outcome. | Asynchronous tasks and obligation-aware scoring already exist. Autonomous receiver commitment during an agent call is a particular measurement target requiring explicit comparison with its code; absence is not inferred from its abstract. |
| [ReInBench / When to Intervene?](https://arxiv.org/abs/2610.36471) | Studies agent errors and self-recovery traces, and predicts whether intervention is needed. | Error detection, recovery prediction and intervention timing are established adjacent questions. Our controlled actuator study does not establish better error prediction. |
| [AgentRewind](https://arxiv.org/abs/2608.14380) | Records aligned context/environment checkpoints for long-horizon recovery, with task-completion and checklist-progress evaluation. | Aligned checkpoints and partial obligation progress are established. AfterClick must document external effects outside any restoration boundary. |
| [Safe to Resume?](https://arxiv.org/abs/2608.29381) | Studies security failures when rollback restores state without the dependencies and external history required for valid continuation. | A consistent local snapshot is insufficient evidence for secure recovery. Our source-cut checks and immutable receiver records need careful comparison with these failure conditions. |
| [SURE-Act / Agents' Last Doubt](https://arxiv.org/abs/2610.24194) | Executes legal alternatives at decision cuts and trains a controller to rank actions using completion, interaction cost and irreversible-error outcomes. | Executed counterfactual choice and action/cost tradeoffs are prior art. Historical safe siblings cannot be promoted into a deployable optimal policy. |
| [AppWorld](https://aclanthology.org/2024.acl-long.850/) | Complex interactive tasks span multiple applications and admit programmatic state tests that also check collateral changes. | Task count, multiple apps, alternative valid plans and collateral-damage checks are insufficient novelty claims by themselves. |
| [tau2-bench](https://arxiv.org/abs/2506.07982) | A shared world supports user and agent actions, compositional verifiable tasks, and coordination/reasoning ablations. | Concurrent collaborators and compositional task authoring already have strong precedents. Their scientific value here depends on new controlled evidence. |

The implemented v12 additions currently support historical provenance auditing,
bounded formal distinctions, an independent application workflow, and controlled
recommendation-to-actuator delay measurements. They do not yet establish the
proposed broad measurement contribution on complex native-model trajectories.
No controller superiority, optimality, conference acceptance, or novel general
graph algorithm is claimed.

Outstanding comparisons: official unchanged UndoBench TEST with genuine model
episodes, original-versus-proxy staging eligibility, materially stronger model
replication, independent complex task diversity, exact wall-clock behavior in
the cited implementations, and the full paper claim-to-evidence audit. Preserve
the prior v11 negative novelty verdict while these remain incomplete.
