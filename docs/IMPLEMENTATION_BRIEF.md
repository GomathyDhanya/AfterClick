# ROLE: Principal Research Engineer, ML Research Scientist, and Systems Architect

You are the lead engineer and research collaborator on **AfterClick**, a research project investigating causal side effects, recoverability boundaries, and learned safety mechanisms for autonomous browser agents.

Your task is to **design and implement the complete research system from scratch**, incrementally, in this repository.

Do not simply generate a project plan or produce pseudocode. Write working code, tests, infrastructure, experiment scripts, and documentation.

Work autonomously through milestones, validating each component before integrating the next. If something cannot be implemented reliably, document the limitation and implement the smallest scientifically valid alternative.

Treat this as research software intended to support a serious academic paper, not a hackathon prototype.

---

# 1. PROJECT OVERVIEW

## Title

**AfterClick: Learning the Recoverability Boundaries of Browser-Agent Actions through Counterfactual Evolution**

## Proposed research method

**Contrastive Recovery Boundary Learning (CRBL)**

## Central research question

Can counterfactual-guided evolutionary search discover minimally different browser executions that cross a safe-recovery boundary, and can contrastive learning from these executions train an agent-side controller to prevent cascading, difficult-to-recover effects in previously unseen workflows?

## Core idea

A browser agent performs an action in a legitimate reactive web application.

The action may be permitted by the application's access controls but unnecessary for the user's actual goal.

Even a seemingly harmless action can produce cascading side effects through:

- Debounced autosave.
- Optimistic UI updates.
- HTTP requests and uncertain acknowledgements.
- Persistent database modifications.
- Background jobs and workflow automations.
- Server-Sent Events.
- Other browser sessions.
- Concurrent user modifications.
- Subsequent autonomous-agent decisions.

We want to investigate three properties:

1. **Necessity:** Could the agent have achieved the legitimate task without this action?
2. **Causal impact:** What downstream effects occurred because the action executed?
3. **Recoverability:** How do the feasibility and cost of safely reversing those effects change over time?

The research system will discover counterfactual execution pairs where a small difference in timing or application state changes a recoverable action into an unrecoverable one.

We will use these pairs to train an ML model that predicts recovery risk before a proposed browser action executes.

Finally, we will evaluate whether a learned safety controller can reduce actual unwanted effects without substantially harming legitimate task completion.

---

# 2. SCIENTIFIC REQUIREMENTS

This section is mandatory. Every subsequent design decision must respect it.

## 2.1 Do not assume the technique is already proven novel

Counterfactual agent replay, evolutionary search, contrastive learning, survival analysis, and selective rollback are established techniques.

Our candidate contribution is specifically:

**Discovering minimal recoverability-boundary counterexamples and using them as supervision for time-dependent recovery-risk prediction.**

Treat this as a hypothesis to evaluate, not a proven novelty claim.

## 2.2 Do not fake experiments

Never generate fabricated:

- Browser trajectories.
- Database events.
- Recovery results.
- Training outcomes.
- Model accuracy.
- Benchmark improvements.
- Statistical significance.
- Causal graphs.

Synthetic scenarios and planted test cases are allowed, but label them explicitly.

Every experimental result must originate from actual executable code and have a reproducible run manifest.

## 2.3 Distinguish correlation from causation

A downstream event occurring after an action does not prove that the action caused it.

Use actual intervention experiments:

- Execute the action.
- Suppress the action.
- Reconstruct the same pre-action environment.
- Continue execution under a controlled protocol.
- Compare downstream results.

Distinguish observed provenance edges, happens-before relationships, and intervention-supported causal claims.

## 2.4 Distinguish authorization from technical permission

The agent may have technical permission to modify a record without being authorized to do so by the user's particular instruction.

Every task requires an independent authorization and preservation contract.

## 2.5 Preserve legitimate concurrent activity

Recovery must never automatically overwrite independent legitimate human modifications simply to recreate a counterfactual database snapshot.

Use version-checked conditional updates, effect ownership, conflict detection, and explicit abstention.

## 2.6 Do not hallucinate recoverability

Recovery outcomes must distinguish:

- VERIFIED_RECOVERABLE
- VERIFIED_UNRECOVERABLE
- PARTIAL
- CONFLICT
- UNKNOWN
- CENSORED

An optimization solver timing out does not prove that recovery is impossible.

A delivered notification cannot be literally unsent.

An outstanding request whose completion is uncertain prevents a complete-recovery claim.

## 2.7 Avoid future-state leakage

The learned model may use only information genuinely available before the proposed action:

- User instruction.
- Task authorization summary.
- Current browser observation.
- Recent tool history.
- Proposed action.
- Trusted application metadata, where exposed.
- Observable pending-work status.

Never give the model future effect logs, hidden scheduler parameters, counterfactual outcomes, or recovery-oracle labels at inference time.

If two scenarios have identical observable inputs but different hidden futures, the model must predict risk or uncertainty rather than pretend to distinguish them perfectly.

---

# 3. RESEARCH ARCHITECTURE

Implement these major subsystems:

1. FlowBoard: Reactive collaborative web application.
2. Browser Agent: Playwright-based LLM agent and action gateway.
3. Event Ledger: Persistent, semantically meaningful effect recording.
4. Deterministic Scheduler: Controlled asynchronous event execution.
5. Replay Engine: Validated checkpoints and counterfactual action interventions.
6. Causal Analyzer: Action necessity and downstream effect comparisons.
7. Recovery Oracle: Independent feasibility checking.
8. Recovery Planner: Safe, conditional compensation.
9. Evolutionary Search: MAP-Elites and minimal boundary-pair discovery.
10. ML Training: Structured baselines and Tinker LoRA fine-tuning.
11. Recovery Shield: Pre-action risk-aware controller.
12. Research Dashboard: Interactive butterfly-effect and recovery visualizations.
13. Evaluation Harness: Baselines, ablations, metrics, and statistical tests.

Design the modules with clear interfaces and minimal coupling.

The ML model, evolutionary algorithm, and browser agent must not depend directly on the recovery oracle's internal ground truth.

---

# 4. IMPLEMENTATION STACK

Preferred stack:

**Frontend**
- React
- TypeScript
- Vite
- A maintainable component system
- Cytoscape.js for causal graphs
- Plotly or D3 for experimental charts

**Backend**
- Python 3.11+
- FastAPI
- Pydantic
- PostgreSQL
- SQLAlchemy
- Alembic

**Browser**
- Playwright
- Chromium
- BrowserGym-compatible adapter where practical

**Asynchronous systems**
- PostgreSQL-backed durable job queue
- Deterministic logical-time scheduler
- Transactional outbox
- Server-Sent Events
- Explicit operation IDs and record versions

**Research**
- NumPy
- pandas or Polars
- SciPy
- NetworkX
- scikit-learn
- pytest
- Hypothesis
- OR-Tools

**Evolutionary algorithms**
- pyribs for MAP-Elites
- Custom scenario-genome representation
- Custom boundary-search emitter
- Delta-debugging-style boundary minimizer

**Machine learning**
- XGBoost or CatBoost baseline
- PyTorch as needed
- Tinker SDK for supported LoRA training
- Qwen3.5-4B as the initial candidate, subject to current Tinker support

**Infrastructure**
- Docker Compose
- uv for Python dependencies
- npm or pnpm for frontend dependencies
- Versioned configuration files
- Structured logging
- OpenTelemetry where useful

Before using external SDKs, inspect their current APIs and documentation. Do not invent library methods.

Prefer established libraries over custom implementations when the standard library already provides the required behavior.

---

# 5. PHASE A — BUILD FLOWBOARD

Start by creating a fully working collaborative project-management application.

It must be realistic enough for browser agents to interact with naturally.

## Required UI

### Project board

Display tasks with:

- Title
- Description
- Status
- Priority
- Assignee
- Review state
- Task dependencies

### Task editor

Allow the user or browser agent to:

- Modify descriptions.
- Change priority.
- Change assignment.
- Mark a task reviewed.
- Change status.
- Add comments.
- View activity history.

### Reactive behavior

Implement genuine:

- Debounced autosave.
- Optimistic UI updates.
- Loading, pending, committed, and failed states.
- Version conflicts.
- Realtime updates through SSE.
- Multiple simultaneous browser sessions.

Do not merely simulate these visually.

## Background workflows

Implement at least four automation rules.

**Workflow A — Escalation**

Setting priority to Critical creates an escalation record and queues an internal notification.

**Workflow B — Release readiness**

Marking a prerequisite task reviewed or completed recalculates dependent task readiness.

**Workflow C — Assignment**

Changing assignee updates ownership information and creates a notification.

**Workflow D — Project summary**

Task-state changes cause asynchronous project-summary recomputation.

Every workflow must have documented trigger conditions, input state, effects, and idempotency behavior.

## Database requirements

Use:

- Transactional updates.
- Record versions.
- Operation IDs.
- Outbox events.
- Durable queued jobs.
- Immutable research effect records.

All relevant writes should support optimistic concurrency control.

## Acceptance tests

Test:

- Autosave persistence.
- Delayed autosave.
- Failed acknowledgement.
- Duplicate request handling.
- SSE delivery.
- Concurrent nonoverlapping edits.
- Concurrent overlapping edits.
- Background job execution.
- Correct transaction/event ordering.

Do not proceed until these tests are working.

---

# 6. PHASE B — DETERMINISTIC EVENT SCHEDULER

Build a test scheduler that controls relevant asynchronous events.

Required capabilities:

- Schedule events at logical times.
- Advance logical time.
- Pause event dispatch.
- Release a particular eligible event.
- Inspect pending work.
- Reproduce schedules from seeds.
- Record event dependencies.
- Cancel jobs only when supported.
- Reconstruct scheduler state for replay.

Separate client-side timers from backend jobs.

For browser timers, investigate Playwright's clock controls.

For backend jobs, implement an explicit research scheduler with a durable event queue.

Avoid uncontrolled `sleep()` calls in tests whenever an explicit event barrier can be used.

An event must never execute before its prerequisites.

Implement validity constraints for:

- Database commit before outbox publication.
- Publication before SSE delivery.
- Job creation before job execution.
- Request dispatch before response.
- Retry only after a valid retry trigger.

Create deterministic tests for these constraints.

---

# 7. PHASE C — BROWSER-AGENT HARNESS

Implement a constrained browser agent using Playwright.

Supported actions:

```python
Click(locator)
Fill(locator, text)
Select(locator, value)
Read(locator)
Navigate(url)
Wait(condition)
```

All actions must pass through an action gateway.

The gateway records:

- User task.
- Current observation.
- Proposed action.
- Tool-call ID.
- Execution status.
- Returned feedback.
- Application effect identifiers.
- Relevant timestamps.

Initially implement a deterministic scripted agent to test the system.

Then add an LLM-driven policy through a configurable model-provider interface.

Avoid binding core experiments to one commercial model.

Use the same model and prompts for matched baseline experiments unless model choice is the independent variable being tested.

---

# 8. PHASE D — COUNTERFACTUAL REPLAY

This is the most critical scientific component.

Implement the ability to select a proposed tool call and examine alternate futures.

## Required interventions

- Execute call normally.
- Suppress call.
- Execute but suppress success feedback.
- Suppress execution but deliver synthetic success feedback.
- Replace call with a defined alternative.

Prioritize execute/suppress first. Implement the other conditions after baseline replay is verified.

## Checkpoint requirements

A checkpoint must identify:

- Application image/version.
- Database state.
- Browser storage.
- Agent observation history.
- Action-prefix history.
- Pending events.
- Scheduler state.
- Relevant random-state information.
- Backend request state.

Never assume that saving browser cookies/local storage fully snapshots JavaScript runtime state.

Use deterministic prefix reconstruction when necessary.

## Replay validity

For each checkpoint:

1. Reconstruct it twice.
2. Execute identical placebo continuations.
3. Compare persistent state and semantic effects.
4. Mark invalid if the reconstruction fails its equivalence checks.

Do not use invalid replays as causal evidence.

## Paired execution

```python
def evaluate_counterfactual(checkpoint, action, seed):
    branch_a = reconstruct(checkpoint, seed)
    branch_b = reconstruct(checkpoint, seed)

    assert validate(branch_a)
    assert validate(branch_b)

    branch_a.execute(action)
    branch_b.suppress(action)

    branch_a.resume()
    branch_b.resume()

    return compare(
        branch_a.effects(),
        branch_b.effects(),
        branch_a.final_state(),
        branch_b.final_state()
    )
```

This is pseudocode. Implement actual isolation, validation, and branch management.

Support:

- Fixed-continuation replay.
- Adaptive LLM continuation.
- Controlled environment schedules.
- Repeated random seeds.
- Bounded time horizons.

Store every result with a unique experiment identifier.

---

# 9. PHASE E — CAUSAL GRAPH AND NECESSITY ANALYSIS

Build an event graph with nodes for:

- Browser agent actions.
- API requests.
- Database transactions.
- Background jobs.
- SSE messages.
- Notification deliveries.
- Collaborator actions.
- Subsequent agent decisions.

Maintain separate edge categories:

- Observed provenance.
- Data dependency.
- Happens-before.
- Counterfactual-supported causal relationship.

Do not automatically treat every graph descendant as a proven causal effect.

## Necessity

Estimate:

\[
N_i =
E[G\mid do(a_i)]
-
E[G\mid do(\varnothing_i)]
\]

where \(G\) is task success.

## Harm

Estimate:

\[
C_i =
E[H\mid do(a_i)]
-
E[H\mid do(\varnothing_i)]
\]

where \(H\) measures unauthorized effects.

Measure:

- Task success.
- Downstream effect count.
- Cascade breadth.
- Cascade depth.
- Cross-service spread.
- Historical irreversible effects.
- Residual unauthorized effects.
- Time to first consequence.

Implement planted known-causality scenarios to validate the estimator.

Use confidence intervals and predefined equivalence thresholds before classifying an action as unnecessary.

---

# 10. PHASE F — RECOVERY ORACLE

Implement an independent reference recovery system.

This system must determine what can safely be compensated given a particular application state and task contract.

Recovery primitives should include:

```python
CancelPendingJob
ConditionalRestoreField
DeleteOwnedDerivedRecord
RecomputeDerivedState
SendCorrectionNotification
EscalateConflict
```

Every recovery operation must define:

- Preconditions.
- Affected resources.
- Authorization scope.
- Version requirements.
- Expected postconditions.
- Idempotency behavior.
- Possible new side effects.

## Recovery invariants

The recovery system must preserve:

1. Legitimate task outcomes where required.
2. Independent human edits.
3. Current version consistency.
4. Authorized effect boundaries.
5. Known historical irreversible effects in the audit record.

Use bounded exhaustive search for small scenarios where possible.

Use OR-Tools for more complex finite compensation planning.

Do not equate solver failure or timeout with mathematical impossibility.

Recovery classification:

```text
VERIFIED_RECOVERABLE
VERIFIED_UNRECOVERABLE
PARTIAL
CONFLICT
UNKNOWN
CENSORED
```

Implement independent post-recovery verification.

---

# 11. PHASE G — EVOLUTIONARY SCENARIO DISCOVERY

Implement a quality-diversity search to discover recovery-boundary scenarios.

Use MAP-Elites through pyribs.

## Scenario genome

```python
@dataclass
class ScenarioGenome:
    autosave_delay_ms: int
    worker_delay_ms: int
    sse_delay_ms: int
    acknowledgement_delay_ms: int

    acknowledgement_mode: str
    retry_policy: str

    collaborator_policy: str
    collaborator_offset_ms: int

    scheduler_seed: int
```

The application workflows should remain fixed during the initial search.

## Core objective

Discover pairs of scenarios that are minimally different but have different verified recovery outcomes.

\[
\min d(z_1,z_2)
\]

subject to:

\[
Recoverable(z_1)=1
\]

\[
Recoverable(z_2)=0
\]

and equivalent legitimate task success.

## Boundary minimization

Once a boundary pair is found:

1. Identify parameters that differ.
2. Try removing individual differences.
3. Replay.
4. Keep simplifications that preserve the boundary.
5. Refine continuous parameters using bounded local search.
6. Save the smallest verified witness found.

Do not claim global minimality without exhaustive proof.

## MAP-Elites archive

Use behavior descriptors such as:

- Cascade breadth.
- Recovery-boundary time.
- Irreversible-effect type.
- Number of affected subsystems.

Store the best verified boundary scenario for each archive cell.

## Baselines

Implement:

- Random valid scenarios.
- Coverage-guided fuzzing.
- Standard genetic algorithm.
- Standard MAP-Elites.
- Boundary-targeted MAP-Elites.
- Full MAP-Elites plus boundary minimization.

Compare equal execution budgets.

---

# 12. PHASE H — CONTRASTIVE RECOVERY BOUNDARY LEARNING

Build a training dataset from validated counterfactual experiments.

## Training input

The model receives:

- User instruction.
- Task contract summary.
- Current browser observation.
- Recent tool-call history.
- Proposed action.
- Available trusted workflow metadata.

## Training targets

- Task necessity.
- Unauthorized downstream effect risk.
- Time-dependent irreversibility risk.
- Observable versus hidden uncertainty.
- Recommended intervention.

## Learning objective

Use a combination of:

1. Task-necessity prediction.
2. Downstream risk prediction.
3. Discrete-time survival prediction.
4. Boundary-pair ranking.

For observable boundary pairs, train the higher-risk case to receive a higher risk score.

For latent boundary pairs with identical observable input, do not force contradictory deterministic labels. Use them to estimate uncertainty or a conditional risk distribution.

Implement a structured baseline before fine-tuning an LLM.

## Model baselines

- Rule-based critic.
- XGBoost/CatBoost critic.
- Prompted LLM critic.
- SFT on ordinary success/failure labels.
- SFT on random counterfactual data.
- SFT on boundary-pair data without temporal labels.
- Full CRBL model.

Use strict held-out workflow families.

## Tinker integration

I have approximately **$250 in Tinker credits**.

Do not spend credits automatically.

First:

1. Inspect the currently supported Tinker training API.
2. Prepare and validate the local dataset.
3. Build the training script.
4. Create a tiny smoke-test configuration.
5. Estimate cost.
6. Document required environment variables.
7. Request authorization before any paid training run.

Target Qwen3.5-4B with LoRA if supported. Otherwise select the closest appropriate supported model and document the change.

Do not commit API keys, tokens, or credentials.

---

# 13. PHASE I — LEARNED RECOVERY SHIELD

Implement a runtime controller that intercepts consequential tool calls before execution.

Supported decisions:

```text
ALLOW
INSPECT
STAGE
REQUEST_APPROVAL
SKIP_AND_REPLAN
```

The decision uses task authorization and the learned risk estimate.

The model does not override explicit task authorization restrictions.

`STAGE` is allowed only when the application provides an enforceable staging boundary.

On an arbitrary external website, do not claim staging or rollback capabilities that do not actually exist.

## Runtime defense

```python
def defend(context, proposed_action):
    if violates_task_contract(context, proposed_action):
        return REQUEST_APPROVAL

    prediction = impact_model.predict(
        context,
        proposed_action
    )

    if prediction.uncertain:
        return INSPECT

    if prediction.low_necessity and prediction.high_risk:
        return SKIP_AND_REPLAN

    if prediction.high_irreversibility_risk:
        if context.supports_staging:
            return STAGE
        return REQUEST_APPROVAL

    return ALLOW
```

After executing an action, monitor observed downstream effects.

On unexpected effects:

- Stop issuing new agent writes.
- Reconcile in-flight operations.
- Cancel pending work where supported.
- Generate conditional compensations.
- Preserve independent legitimate edits.
- Verify the result.
- Report any unresolved or irreversible effects.

---

# 14. PHASE J — EXPERIMENTAL EVALUATION

Create at least 12 task templates, including:

1. Description update with unnecessary review click.
2. Autosave completing after navigation.
3. Lost acknowledgement and retry.
4. Background job executing before recovery.
5. SSE changing the next agent observation.
6. Independent collaborator edit.
7. Overlapping collaborator edit.
8. Notification delivered before rollback.
9. Duplicate read actions.
10. Dependent task automation.
11. Stale optimistic UI.
12. Optional misleading webpage content.

## Primary experiments

**E1 — Counterfactual validity**

Does replay accurately identify planted causal dependencies?

**E2 — Evolutionary discovery**

Does boundary-targeted evolutionary search discover more diverse verified recovery boundaries than random or conventional search?

**E3 — ML generalization**

Does CRBL outperform equally sized random-counterfactual training on held-out workflow families?

**E4 — Defense**

Does the learned shield reduce actual irreversible or unresolved effects while maintaining task success?

**E5 — Recovery**

Does constrained compensation preserve legitimate work more effectively than snapshot restoration or naive undo?

## Metrics

Implement:

- Task success rate.
- Avoidable-action rate.
- Unauthorized persistent effect rate.
- Historical irreversible effect rate.
- Verified recovery rate.
- Legitimate-edit preservation rate.
- Recovery-boundary prediction AUROC.
- Integrated Brier score.
- Calibration error.
- Risk–coverage curves.
- Boundary pairs discovered per evaluation budget.
- Archive coverage.
- Replay validity rate.
- Runtime overhead.
- Training and inference cost.

Use confidence intervals, paired tests, and task-level clustering.

Do not report statistically significant improvements without actual tests.

---

# 15. RESEARCH VISUALIZATION DASHBOARD

Build a polished interactive research interface.

It should be technically meaningful, not decorative.

## View A — Butterfly Explorer

Select a browser-agent action and display:

- Original future.
- Counterfactual future.
- Synchronized event timelines.
- Differing persistent state.
- Background effects.
- Subsequent agent decisions.
- Verified causal evidence.

## View B — Blast Radius

Display affected areas across:

```text
Agent → Browser → API → Database → Jobs → SSE → Other actors
```

Use distinct colors for authorized, unauthorized, reversible, irreversible, and unknown effects.

## View C — Recovery Landscape

Interactive heatmap:

- X-axis: Event timing.
- Y-axis: Recovery-start delay.
- Color: Verified recovery deficit or recovery class.

Highlight minimal boundary pairs discovered by evolution.

## View D — MAP-Elites Discovery

Visualize the evolutionary archive.

Each cell should open its associated scenario and counterfactual evidence.

## View E — ML Evaluation

Display:

- Calibration plots.
- ROC curves.
- Time-dependent hazard predictions.
- Defense intervention rates.
- Task success versus unwanted effects.

Never display fabricated results as measured findings.

Create an explicit synthetic/demo-data mode when real experiments are not yet available.

---

# 16. REPOSITORY STRUCTURE

Use a structure resembling:

```text
afterclick/
├── apps/
│   ├── flowboard-web/
│   ├── flowboard-api/
│   └── research-dashboard/
├── agent/
├── infrastructure/
│   ├── scheduler/
│   ├── outbox/
│   ├── event_ledger/
│   └── checkpoints/
├── replay/
├── causality/
├── evolution/
├── recovery/
├── learning/
├── evaluation/
├── fixtures/
│   ├── tasks/
│   ├── states/
│   ├── schedules/
│   └── collaborators/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── replay/
│   ├── recovery/
│   └── learning/
├── configs/
├── scripts/
├── docker/
├── artifacts/
├── docs/
├── pyproject.toml
├── uv.lock
└── README.md
```

Adapt only when a different structure clearly improves maintainability.

---

# 17. REQUIRED DOCUMENTATION

Maintain the following documents:

**README.md**

Architecture overview, setup, commands, and current implementation status.

**docs/RESEARCH_SPEC.md**

Research question, hypotheses, mathematical definitions, assumptions, and novelty boundaries.

**docs/ARCHITECTURE.md**

System diagrams, service contracts, data flow, event scheduling, and state restoration.

**docs/EXPERIMENTS.md**

Task templates, baseline definitions, intervention conditions, metrics, and statistical procedures.

**docs/REPRODUCIBILITY.md**

Exact commands, seeds, dependency versions, artifact schemas, and validation requirements.

**docs/DECISIONS.md**

Architectural decisions and tradeoffs, including rejected alternatives.

**docs/PROGRESS.md**

A living implementation log containing:

- Completed features.
- Tests passing.
- Current milestone.
- Known limitations.
- Next tasks.
- Research validity concerns.

Update the progress file at the end of every meaningful development session.

---

# 18. IMPLEMENTATION DISCIPLINE

Follow these requirements throughout the project.

### Write actual code

Do not satisfy a milestone by producing interfaces full of `pass`, empty classes, mocked research results, or TODO comments.

Temporary stubs are allowed only when clearly documented and not used to establish scientific results.

### Validate continuously

For every major component:

1. Implement its smallest functional version.
2. Add unit tests.
3. Add relevant integration tests.
4. Execute the tests.
5. Fix failures.
6. Document limitations.
7. Integrate it into the next layer.

### Keep experiments reproducible

Record:

- Code commit.
- Dependency versions.
- Container image digests.
- Task fixture.
- Schedule parameters.
- Random seeds.
- Model configuration.
- Intervention details.
- Outcome hashes.
- Evaluation horizon.
- Recovery verification results.

### Avoid unnecessary architectural complexity

Do not introduce Kubernetes, distributed microservices, a large message broker, or production authentication infrastructure unless necessary.

Start with Docker Compose, PostgreSQL, a controlled scheduler, and a modular monorepo.

### Maintain scientific boundaries

Do not let the proposed model access the evaluation oracle.

Do not allow the proposed recovery planner to generate its own unverified ground-truth labels.

Do not silently drop invalid or failed trials.

Keep negative results and failure cases.

### Budget management

Use deterministic scripted agents for inexpensive systems testing.

Invoke paid LLM inference only when required for an actual agent-behavior experiment.

Require approval before paid Tinker fine-tuning.

---

# 19. MILESTONE ACCEPTANCE GATES

Before beginning the next milestone, the current one must satisfy a concrete acceptance test.

**Gate 1 — Application**

The reactive web app correctly persists changes, triggers asynchronous effects, and supports concurrent sessions.

**Gate 2 — Replay**

One action can be suppressed from a validated checkpoint and its downstream effect difference reproduced.

**Gate 3 — Recovery**

The system distinguishes a verified recoverable case, a verified irreversible case, and a conflicting concurrent-edit case.

**Gate 4 — Evolution**

The search discovers and minimizes a verified pair of executions with different recovery outcomes.

**Gate 5 — ML**

Training data passes leakage tests and a real model can be evaluated on a held-out workflow.

**Gate 6 — Defense**

The learned controller completes an end-to-end task while recording actual interventions and effects.

**Gate 7 — Research**

Baselines, ablations, uncertainty estimates, and visualizations are reproducible from stored experiment data.

Never report a milestone as complete if its acceptance tests have not actually passed.

---

# 20. YOUR IMMEDIATE TASK

Start implementation now.

Do not spend the entire session writing plans.

Proceed in this order:

## Step 1 — Inspect the repository

Check:

- Existing source files.
- Git status.
- Installed dependencies.
- Available runtime versions.
- Existing tests.
- Existing documentation.

If this is an empty repository, initialize the project from scratch.

If existing code is present, preserve it and integrate appropriately.

## Step 2 — Establish the engineering foundation

Create:

- Monorepo structure.
- Docker Compose configuration.
- FastAPI backend.
- PostgreSQL database.
- React/TypeScript frontend.
- Python test configuration.
- Dependency lockfiles.
- Basic CI workflow.
- Initial architecture and research documents.

## Step 3 — Implement the first vertical slice

Build a functioning task editor with:

- A task record in PostgreSQL.
- Editable description.
- Editable review state.
- Debounced autosave.
- Persistent activity events.
- One background automation.
- One SSE consumer.
- A second synchronized browser session.

Use real database updates and real backend events.

## Step 4 — Add deterministic testing hooks

Implement:

- Seeded test fixture.
- Logical scheduler.
- Event inspection.
- Database reset.
- Deterministic job-release controls.
- Semantic event recording.

## Step 5 — Demonstrate the first butterfly effect

Construct a scripted scenario:

1. The legitimate goal is to update a task description.
2. The agent performs an additional `mark_reviewed` action.
3. Autosave persists the review change.
4. A dependent background automation executes.
5. The effect ledger records all relevant changes.
6. Reset the environment.
7. Repeat without the review action.
8. Compare the resulting persistent state and event traces.

Do not claim that the extra action is unnecessary until the task-success oracle confirms the goal can still be achieved without it.

This is the first research milestone.

## Step 6 — Demonstrate a recovery boundary

Create two controlled schedules:

**Schedule A:** A dependent job remains pending when recovery starts.

**Schedule B:** The same job has already delivered an irreversible internal notification when recovery starts.

Attempt supported recovery in both schedules.

The expected classifications should be established by independent oracle rules.

Verify that the difference is not caused by an invalid checkpoint or unrelated state mismatch.

## Step 7 — Run all tests

Execute:

- Python unit tests.
- Backend integration tests.
- Frontend build/typecheck.
- Playwright tests.
- Deterministic scheduler tests.
- Recovery-boundary tests.

Fix failures before concluding the milestone.

## Step 8 — Report implementation status

At the end of the session, give:

1. Components actually implemented.
2. Files created or changed.
3. Commands executed.
4. Tests passing and failing.
5. A concrete reproducible demo command.
6. Known scientific or engineering limitations.
7. Next implementation tasks.

Update `docs/PROGRESS.md` with the same information.

---

# 21. CONTINUATION INSTRUCTIONS

This project will require multiple Codex sessions.

The repository must be self-documenting enough for a fresh agent instance to continue without prior conversational context.

At the beginning of every new session:

1. Read `README.md`.
2. Read `docs/RESEARCH_SPEC.md`.
3. Read `docs/ARCHITECTURE.md`.
4. Read `docs/PROGRESS.md`.
5. Inspect Git status.
6. Identify the earliest incomplete milestone.
7. Continue implementation.

Do not redesign previously validated foundations without a documented technical reason.

Do not repeatedly ask for information already captured in the project documentation.

If blocked by an external credential, service, or paid action, implement everything that can be completed locally, document the exact blocker, and continue with independent work.

---

# 22. DEFINITION OF DONE

The project is complete only when the following are executable:

- A real browser agent interacts with a reactive web application.
- Actions generate observable downstream effects.
- A selected action can be counterfactually suppressed.
- Replay validity is checked.
- Action necessity and causal impact are estimated.
- Recovery attempts preserve independent legitimate changes.
- Verified recovery-boundary pairs can be discovered.
- Evolutionary search finds and minimizes boundary pairs.
- A structured ML baseline is trained and evaluated.
- A fine-tuned model is trained and evaluated when authorized and feasible.
- A learned controller intervenes before consequential actions.
- The defense is compared against proper baselines.
- Research figures are generated from actual experiment artifacts.
- The system can be reproduced using documented commands.

A polished UI is not sufficient.

A successful model-training job is not sufficient.

An impressive causal graph without verified intervention evidence is not sufficient.

**The objective is a reproducible scientific system capable of establishing—or falsifying—the central AfterClick research hypothesis.**

Begin with repository inspection, architectural setup, and the first working vertical slice. Implement as much as can be validated in the current session, and preserve a clear continuation state for subsequent sessions.