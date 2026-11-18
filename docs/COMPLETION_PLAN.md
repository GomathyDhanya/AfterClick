# **AfterClick — Complete Project Completion Plan**

**Starting point:** The audited `684_final(1).zip` repository, dated November 17, 2026.

**Final objective:** Complete a reproducible ML + systems research project that discovers recovery-boundary failures, learns from counterfactual executions, and demonstrates a defense that reduces consequential browser-agent mistakes on unseen workflows.

## **1. Where we are and what remains**

The existing repository should be the foundation. We should **not rebuild FlowBoard, replace PostgreSQL, or discard the existing replay implementation**.

According to `docs/PROGRESS.md` and the independent audit, the current system has seven research gates:

| Gate                                   | Current status                               | Next requirement                  |
| -------------------------------------- | -------------------------------------------- | --------------------------------- |
| 1. Reactive web application            | Passed for initial scope                     | Expand scenarios                  |
| 2. Deterministic counterfactual replay | Passed for one quiescent scripted trajectory | Generalize and harden             |
| 3. Selective recovery                  | Passed for review/readiness                  | Multiple independent workflows    |
| 4. Evolutionary discovery              | Not started                                  | Boundary search and minimization  |
| 5. Machine learning                    | Not started                                  | Dataset, baselines, CRBL          |
| 6. Learned defense                     | Not started                                  | Runtime integration               |
| 7. Scientific evaluation               | Not started                                  | Comparative experiments and paper |

The saved demonstration is worth preserving: both execute and suppress branches complete the description-edit goal; early recovery at logical time 99 succeeds; a scripted receipt at time 200 makes complete historical recovery impossible under the fixture's model; and overlapping collaborator edits trigger a conflict.

That proves the initial experiment is feasible. It does **not** establish a general causal result or learned safety improvement. The repository reports 39 passing tests, but those were not independently rerun in the audit environment.

Recommended completion schedule

Core implementation

## **8–10 weeks**

Research evaluation

## **3 weeks**

Paper and release

## **1–2 weeks**

A 12–15-week plan for approximately four contributors, assuming the existing infrastructure remains usable. The milestones, not calendar dates, should control progression.

## **2. Lock the research contribution before expanding the code**

Our primary novelty hypothesis should be:

> **Counterfactual recovery-boundary examples discovered through targeted evolutionary search provide more useful supervision for predicting and preventing difficult-to-recover browser-agent effects than equally expensive random counterfactual training.**

We will test three separate claims.

**C1 — Discovery:** Boundary-targeted evolutionary search finds more diverse, verified recovery failures per evaluation budget than random and coverage-guided search.

**C2 — Learning:** A critic trained on the discovered boundary examples better predicts risk on held-out workflows than a critic trained on equally many randomly selected counterfactual examples.

**C3 — Defense:** Integrating that critic reduces unauthorized and irreversible effects while maintaining legitimate task success at a matched intervention budget.

The project is not complete merely when the model trains. **C3 is the end-to-end result that makes this an ML-systems safety project.**

One important change from the earlier specification: use *time to first independently verified irreversible effect* as the main survival-learning target. General recovery feasibility can improve or worsen with later events, so it should be measured separately rather than incorrectly treated as an absorbing event.

# **3. Implementation roadmap: ten completion gates**

Project dependency map


Completion gates are ordered by scientific dependency. Some frontend, documentation, and testing tasks can run in parallel.

## **Gate 0–1 — Fix the existing prototype**

Highest immediate priority

Week 1 · Replay correctness, concurrency correctness, reproducibility

| Task   | Exact files                            | Required change                                                                   |
| ------ | -------------------------------------- | --------------------------------------------------------------------------------- |
| AC-001 | `afterclick/replay/demo.py`            | Include `conflict` in the pre-action checkpoint-equivalence certificate           |
| AC-002 | `tests/replay/test_validity.py`        | Add a negative test where the conflict checkpoint is deliberately mismatched      |
| AC-003 | `apps/flowboard-web/src/main.tsx`      | Replace value-only stale-write rebase with revision-aware conflict handling       |
| AC-004 | `afterclick/domain.py`, API and schema | Expose safe field revision tokens and support atomic field-level compare-and-swap |
| AC-005 | `tests/browser/`, `tests/integration/` | Test two sessions writing the same value with different ownership                 |
| AC-006 | Repository/CI                          | Create a clean Git revision and reproduce the initial demo on an isolated machine |

The `409` problem is particularly important. Two writes can leave the same field value yet represent different ownership histories. The client must not infer that no intervening write occurred simply because the values match.

**Acceptance gate:** All existing tests still pass, the seven-branch demonstration remains reproducible, and intentionally corrupted checkpoints or same-value ownership changes fail safely.

## **Gate 2 — Generalize the research oracle**

Weeks 2–3 · Task contracts, independent evaluation, diverse workflows

This is the most important dependency before ML. The current `afterclick/recovery/oracle.py` is specialized around `TASK-42`, the description goal, and review/readiness effects.

Add task-specific contracts and independent verifiers for more workflows.

| Workflow family               | New task example           | New consequence                             |
| ----------------------------- | -------------------------- | ------------------------------------------- |
| Review and readiness          | Review a prerequisite      | Changes dependent readiness                 |
| Priority and escalation       | Change one task's priority | Creates escalation and notification         |
| Assignment                    | Reassign a task            | Updates assignee and internal notifications |
| Status and summary            | Complete a task            | Recalculates project completion             |
| Comments/activity             | Add or edit a comment      | Creates persistent activity history         |
| Concurrent multi-task editing | Edit related records       | Creates conflicts or dependent changes      |

For every family, test known recoverable, known irreversible, harmless, conflicting, unknown, and censored cases.

Add the following modules:

```
afterclick/contracts/
    schema.py
    predicates.py
    authorization.py

afterclick/evaluation/
    task_oracle.py
    effect_oracle.py
    recovery_reference.py
```

A critical rule: the oracle cannot label a scenario irreversible merely because the recovery planner timed out or does not support the action.

**Acceptance gate:** At least three independent workflows have validated recovery labels before moving to adaptive LLM replay. Expand toward six or more workflow families for final generalization experiments.

## **Gate 3 — Implement an actual LLM browser agent**

Weeks 3–5 · Agent execution, counterfactual continuation, causal validation

Currently, the action sequence is scripted. That is valuable for repeatability but cannot tell us how an autonomous agent behaves after an action is removed.

Preserve the existing `Gateway` and add:

```
afterclick/agent/
    llm_policy.py
    browser_observation.py
    action_parser.py

afterclick/replay/
    adaptive_runner.py
    branch_compare.py
    semantic_alignment.py
```

Each original execution should record the model, prompt, observations, proposed actions, tokens, cost, and final task outcome.

Then evaluate each selected action under two modes.

**Fixed continuation:** Keep the original subsequent actions where semantically valid. This tests the trajectory's structural dependencies.

**Adaptive continuation:** Suppress the action and let the LLM observe the new state and plan again. This tests whether the agent can compensate.

Add an explicit feedback intervention for selected writes—such as a committed operation whose acknowledgement is lost—to study duplicate requests without conflating execution with feedback.

**Acceptance gate:** Demonstrate valid counterfactual differences across multiple workflows and seeds, with placebo tests and an adaptive LLM that does not receive hidden backend state.

## **Gate 4 — Expand selective recovery**

Weeks 4–6 · Compensation, preservation, independent verification

The existing review/readiness compensation is the starting point.

Extend it to priority/escalation, assignment/notification, status/summary, and pending jobs. Preserve immutable history and require atomic version checks.

Compare these recovery strategies:

| Method                                       | Role                                                              |
| -------------------------------------------- | ----------------------------------------------------------------- |
| No recovery                                  | Untreated baseline                                                |
| Agent undo                                   | Tests ordinary model-directed correction                          |
| Snapshot restore                             | Offline comparison; never a live collaborative recovery primitive |
| Reverse-order compensation                   | Basic recovery baseline                                           |
| Dependency-aware conditional undo            | Strong systems baseline                                           |
| Counterfactual-informed constrained recovery | Proposed method                                                   |

Every method must start from an equivalent recovery-time state.

**Acceptance gate:** No legitimate collaborator changes are silently overwritten; irreversible notifications remain represented in history; unknown outcomes are never certified as recovered.

# **4. The algorithmic core: evolutionary discovery**

## **Gate 5 — Find recovery boundaries automatically**

Weeks 6–8 · Scenario genomes, MAP-Elites, paired minimization

This is where the current implementation becomes a new research method rather than a larger set of hand-written tests.

Implement:

```
afterclick/evolution/
    genome.py
    schedule_validator.py
    random_search.py
    coverage_search.py
    genetic_search.py
    map_elites.py
    boundary_pairs.py
    minimizer.py
    archive.py
```

The genome should vary legitimate execution conditions: autosave delay, worker delay, acknowledgement delay/loss, SSE delivery timing, collaborator timing, and retry settings.

Do not evolve arbitrary application business logic. That could artificially manufacture dramatic failures.

### **Search procedure**

1. Generate a valid browser execution scenario.
2. Reconstruct the same pre-action checkpoint in two isolated branches.
3. Execute the action in one branch and suppress it in the other.
4. Independently evaluate the resulting effects and recoverability.
5. Retain scenarios with a verified recovery-boundary contrast.
6. Minimize the differences between each boundary-crossing pair.
7. Use MAP-Elites to preserve diverse failure mechanisms instead of repeatedly optimizing one scenario.

Compare with random search, coverage-guided testing, an ordinary genetic algorithm, and standard MAP-Elites, using the same expensive evaluation budget.

**Acceptance gate:** A reproducible archive containing independently verified boundary pairs across at least three mechanisms, with equal-budget comparisons.

If the evolutionary method does not outperform random search, that is a legitimate negative result. We should not proceed as though the search novelty has already been proven.

# **5. The machine-learning core**

## **Gate 6 — Build the training dataset correctly**

Weeks 8–9 · Counterfactual labels, observability, leakage protection

The dataset should contain:

| Field                                  | Use                                |
| -------------------------------------- | ---------------------------------- |
| User instruction and task contract     | Legitimate goal and authorization  |
| Pre-action browser observation         | Model input                        |
| Proposed browser action                | Model input                        |
| Trusted, observable workflow metadata  | Optional model input               |
| Execute/suppress outcomes              | Supervision                        |
| Measured causal effects                | Supervision                        |
| First verified irreversible-event time | Temporal supervision               |
| Recovery outcome and deficit           | Separate recovery supervision      |
| Replay certificate                     | Label validity                     |
| Observable/latent pair classification  | Prevent unlearnable ranking labels |
| Task and workflow family               | Leakage-resistant splits           |

**Never place future effect events or hidden scheduler state in the model input.**

This is especially important for the existing early/late example. If both branches have identical information before the action, the model cannot know which later recovery time will be selected. Such examples teach uncertainty or distributional risk, not deterministic differences.

Split by workflow family before final model selection. Reserve entire automation families for out-of-distribution evaluation.

## **Gate 7 — Train and compare CRBL**

Weeks 9–10 · Structured baseline, contrastive supervision, Tinker

Train a structured model first—for example, CatBoost or XGBoost plus a discrete-time hazard model.

Then compare fine-tuned models:

| Model                     | Training signal                                              |
| ------------------------- | ------------------------------------------------------------ |
| Ordinary SFT              | Task success/failure                                         |
| Random-counterfactual SFT | Random execute/suppress outcomes                             |
| Boundary-pair SFT         | Minimal recoverable/unrecoverable contrasts                  |
| **CRBL**                  | Boundary pairs plus time-dependent recovery-risk supervision |

Keep model architecture, sample count, token budget, and held-out test families comparable.

Use Tinker only after dataset and cost validation, and obtain explicit authorization before spending the credit, as the repository's `AGENTS.md` requires.

The decisive result is **not training accuracy**. It is improved recovery-risk prediction on unseen workflows, with calibration and uncertainty.

**Main ML success criterion**

CRBL must outperform the equally budgeted random-counterfactual model on held-out workflow families.

Report time-dependent discrimination, integrated Brier score, calibration, risk–coverage, and variation across training seeds. The final safety benefit must still be tested through actual browser executions.

# **6. Complete the defense**

## **Gate 8 — Integrate Recovery Shield**

Weeks 10–11 · Prediction, authorization, containment, compensation

The final shield will make a decision before consequential tool actions.


Do not implement `STAGE` as a cosmetic delay. It must be backed by a real, enforceable application boundary that can prevent release of pending effects.

The shield should have at least three execution configurations: static authorization only, learned prevention only, and learned prevention with recovery. This isolates the contribution of each mechanism.

**Acceptance gate:** The integrated system can complete legitimate tasks and demonstrates a measured safety benefit on held-out scenarios, without relying on privileged oracle information at inference time.

# **7. Final evaluation requirements**

## **Gate 9 — Experiments and statistics**

Weeks 11–13 · Holdouts, baselines, ablations, confidence intervals

Start with the original 12-task pilot, but do not treat it as sufficient for strong ML generalization claims. Expand toward 24–36 task templates across six or more workflow families, with sample size ultimately determined by pilot variance and available rollout budget.

| Research claim                   | Primary evidence                                       |
| -------------------------------- | ------------------------------------------------------ |
| Boundary search works            | Verified boundary discoveries per 100 evaluations      |
| Search finds different failures  | Distinct mechanisms and MAP-Elites archive coverage    |
| Boundary supervision improves ML | Held-out risk prediction, calibration, and uncertainty |
| Shield prevents damage           | Reduced historical and residual unauthorized effects   |
| Shield preserves usefulness      | Task success and unnecessary intervention rate         |
| Recovery preserves work          | Legitimate collaborator-edit loss rate                 |
| Verification is trustworthy      | False complete-recovery claim rate                     |

Use paired experiments with task/workflow-level clustered confidence intervals. Do not interpret a statistically nonsignificant change in success as proof of equivalence; use a prespecified noninferiority or equivalence margin.

The critical ablations are:

- Remove boundary-pair minimization.
- Remove temporal recovery supervision.
- Replace evolutionary data with randomly sampled counterfactuals.
- Remove counterfactual validation from graph construction.
- Remove recovery from the learned shield.
- Remove the learned shield and rely only on static authorization.

This identifies what each research contribution actually adds.

## **Gate 10 — Scientific visualization and paper**

Weeks 13–14 · Measured graphs, reproducible figures, publication artifacts

The existing offline timeline explorer is a good foundation. Expand it into four linked scientific views.

**Butterfly Explorer**

Original versus suppressed execution with aligned event timelines, record changes, and links to raw replay evidence.

**Cross-service Blast Radius**

Browser, API, database, workers, SSE, and collaborator effects. Clearly distinguish provenance edges from experimentally supported causal relationships.

**Evolutionary Recovery Landscape**

MAP-Elites archive and heatmap of recovery outcomes across timing parameters, with selectable minimal boundary pairs.

**Safety–Utility Frontier**

Actual unauthorized-effect rate versus task success and intervention budget for all defense baselines.

Every plotted figure must be generated from stored run IDs, oracle certificates, and reproducible analysis scripts.

# **8. What each contributor should own**

| Role                              | Main implementation responsibility                                            |
| --------------------------------- | ----------------------------------------------------------------------------- |
| **Systems and replay**            | Field revisions, checkpoint validity, browser gateway, scheduling             |
| **Contracts and recovery**        | Multi-workflow task contracts, independent oracle, compensation, preservation |
| **Evolution and causal analysis** | Semantic effect graphs, MAP-Elites, minimization, archive                     |
| **ML and evaluation**             | Dataset, structured baseline, Tinker after approval, shield, statistics       |

All contributors should jointly review task contracts, research metrics, and final results. These are scientific assumptions, not just isolated software modules.

A weekly integration gate should require passing tests, a reproducible experiment command, and updated `docs/PROGRESS.md`.

# **9. What we must explicitly avoid**

The audit reveals several tempting directions that would delay the project without strengthening the initial research contribution.

| Avoid                                                               | Reason                                                           |
| ------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Rebuilding FlowBoard                                                | The existing app is already a functioning foundation             |
| Starting Tinker training immediately                                | Current labels are limited to one planted workflow               |
| Claiming general causal attribution from action IDs                 | Provenance alone is insufficient                                 |
| Expanding immediately to arbitrary public websites                  | Complete causal verification and recovery become impractical     |
| Replacing the deterministic scheduler with uncontrolled concurrency | Removes the experimental control we currently have               |
| Treating all recovery conflicts as irreversible                     | Conflict is not necessarily proof of impossibility               |
| Training on hidden future timing                                    | Produces information leakage and misleading results              |
| Adding multiple agent models before basic validity                  | Expands cost and confounding                                     |
| Building the final dashboard before experiment data                 | Risks producing attractive but scientifically unsupported graphs |

A secondary nonserialized dispatcher stress test is worth doing later, but the primary deterministic environment should remain intact.

# **10. First implementation sprint: exact assignments**

These are the next three issues I would hand to a coding agent.

**AC-001 — Complete replay certification**

P0

**Files:** `afterclick/replay/demo.py`, `tests/replay/test_validity.py`

Include the conflict branch's pre-action checkpoint in the replay certificate. Add an intentional mismatch test. Maintain the distinction between its initial state and the later collaborator intervention.

**Done when:** All seven branches are certified correctly, and corrupting the conflict branch causes replay validation to fail.

**AC-002 — Enforce field-level revision correctness**

P0

**Files:** `apps/flowboard-web/src/main.tsx`, backend domain/API, schema, browser tests

Introduce non-identifying field revision tokens, detect same-value ownership changes, and perform atomic conditional rebases.

**Done when:** A same-value edit from a second browser cannot be silently overwritten and the first browser retains its unsaved draft.

**AC-003 — Generalize the independent oracle**

P0

**Files:** New contracts/evaluation modules plus `fixtures/tasks/` and recovery tests

Add independent priority/escalation and status/summary task families. Ensure `UNKNOWN`, `CENSORED`, `CONFLICT`, and irreversible outcomes are distinguishable without trusting planner status.

**Done when:** The oracle correctly handles planted positive and negative recovery cases in all three initial families.

The next sprint after these issues should connect an adaptive LLM to the existing Playwright gateway—not begin evolutionary training.

# **11. Final research completion criteria**

I would use the following as the final approval checklist.

| Deliverable            | Required proof                                                                                                  |
| ---------------------- | --------------------------------------------------------------------------------------------------------------- |
| Replay engine          | Multiple workflow families with valid branch reconstruction and placebo tests                                   |
| Causal evaluation      | Intervention-supported action-effect differences                                                                |
| Evolutionary algorithm | Verified boundary archive and equal-budget search baselines                                                     |
| ML dataset             | Strict family holdouts, observable/latent separation, verified labels                                           |
| CRBL model             | Improved held-out prediction over equal-budget counterfactual baseline, or an honestly reported negative result |
| Recovery Shield        | Actual safety outcomes at matched success/intervention budgets                                                  |
| Recovery engine        | Preservation tests and explicit uncertainty classifications                                                     |
| Research dashboard     | Every visual linked to real experimental evidence                                                               |
| Paper                  | Statistical comparisons, ablations, limitations, and reproducibility package                                    |

**The single most important milestone is the first independently discovered, minimal recovery-boundary pair that was not manually planted into the demonstration.** That establishes the search component as something more than replaying a known example.

The next most important is a held-out experiment showing that learning from those discovered pairs helps the shield protect an autonomous agent.

## **Downloadable completion roadmap**

I've also prepared a more implementation-oriented roadmap with specific module paths, task descriptions, acceptance tests, owner assignments, stopping conditions, and instructions for the next coding sprint.

Download AfterClick Complete Implementation Roadmap

**My recommendation:** Approve the existing prototype as Gates 1–3, fix AC-001 through AC-003, then complete the remaining gates in strict scientific dependency order. Preserve the current implementation and its evidence. The goal is not to build the largest agent framework; it is to demonstrate that *recovery-boundary-focused search and learning provide measurable advantages that existing generic counterfactual and recovery methods do not*.

Rendered Mermaid CSS was omitted when archiving this user-supplied request.
