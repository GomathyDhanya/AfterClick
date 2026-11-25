# 03 — Preregistered full experimental program

**Status:** all counts below describe a future design, not results. Freeze final counts and tasks before any TEST model outcomes are inspected.

## Unit structure and core TEST cohort

216 independent TEST task specifications (6 families × 3 levels × 2 apps × 6 different task contracts). For each task, create 3 timing regimes (generous, intermediate, tight) × 3 independently seeded worlds per regime: **1,944 matched stress worlds**, nested in 216 tasks. Each world receives four primary policies, with real new agent continuations:

| Arm | Definition | Main contrast |
|---|---|---|
| P0 — Actor-only | Same legitimate application permissions, no extra AfterClick controller | Treatment-free baseline |
| P1 — Fast rule | Best validated deterministic, public-authorization-aware stage/cancel/revoke policy | Value of timely intervention |
| P2 — Fast verify | Public service verification immediately followed by deterministic authorization-aware action, with no extra model call | Information value vs timing cost |
| P3 — Verify + Qwen | Same public verification capability, plus one fresh Qwen decision before applying protection | Incremental deliberation cost/value |

Run **7,776** stress branches (1,944 × 4). Additionally run 3 clean baseline replicates per task, using independently seeded but nonstressful schedules: **648 clean episodes**. Total **8,424 core executed episodes** for the primary model.

These episode counts may change only through a written **pre-TEST design revision** justified by feasibility/power; don't change them after seeing TEST results. Record every started, failed, invalidated, censored, missing, and retried episode.

## Two focused, preselected interaction studies

- **Restoration:** select **72 task contracts before TEST** (balanced across app, family, level, authorization/restoration eligibility). Across each task's 9 stress worlds, add P4 = P1 plus a public-obligation-status query/feedback. This is **648 extra episodes**, compared with the existing P1 sibling. Do not use hidden oracle status as feedback.
- **Stage-first independent supervision:** a separately preregistered **72-task** balanced subset, same 9 worlds each: add P5 = immediate feasible staging (or predeclared fallback), then independent Qwen safety recommendation. **648 extra episodes**, compared with P1/P3. Only count the model's advice when schema-valid; preserve fallback incidence. Never attribute safe fallback outcomes to the LLM.

**Total prospective primary-model enrollment if all three studies execute: 9,720 episodes** (8,424 core + 648 restoration + 648 supervision). This excludes development, local deterministic replay sweeps, cross-model replication, and official external benchmarks. The size is substantial by design; use scientific analysis/power checks to justify it rather than treating count itself as novelty.

## Model generalization

- Primary model: existing `Qwen/Qwen3.5-9B`, pinned exact revision and native tool format, unless that revision cannot be reproduced.
- Require **one independently sourced, materially stronger or differently trained agent model** on the *entire core matrix* (preferably same 216 tasks, 1,944 stress worlds, four arms and 648 clean trials), if the serving interface can faithfully implement the same tools and observations. Pin version, hardware, decoding, and server stack. Do not invent a model endpoint; verify availability and licensing.
- If a full second-model replication is technically impossible, record exact reason and downgrade any model-general claim. A prechosen smaller replication subset may be reported as supplementary, never silently upgraded to a full replication.
- Supervisor model may share the actor model for an explicitly controlled same-model study; don't equate that with independent-model generalization.

## Randomization, selection, and freezing

- Keep DEV and TEST fixtures/graphs/wording/IDs separate. Use the 72 DEV contracts for complete implementation/calibration; do not optimize models against TEST outputs.
- Freeze TEST source manifest: hashed tasks, hidden oracles, public policies, worker schedule seeds, model revisions, tool schemas, arm order, gateway versions, admission rules, retry rules, source cut certificates, primary endpoints, and analysis plan.
- Randomize/counterbalance arm order per source-world. Clone from equivalent user-visible/client/worker state and certify before execution; invalid clone is not an agent failure.
- Randomize trials within timing stratum with declared generator; do not cherry-pick favorable seeds or tune deadlines to a preferred controller's latency.
- Tune scheduler regimes using DEV measured distributions. In TEST, classify a source world as opportunity-present, frontier-near, or already-beyond-frontier independently from hidden oracle; never drop impossible worlds post hoc.

## Primary and secondary hypotheses

Primary estimand: **paired difference P3 − P2 in joint safe task completion** across the registered population of TEST tasks/worlds. It can be positive, negative, or indistinguishable from zero.

Key secondary comparisons:
1. P2 − P1: net value (accuracy less latency cost) of verification.
2. P1 − P0: fast protection's safety and task cost.
3. P4 − P1: public restoration-obligation feedback.
4. P5 − P1 and P5 − P3: stage-first oversight vs fast rule and sequential deliberation.
5. Clean competence vs stressed task competence (describe changes carefully; not the same environment).
6. Effect modification by task depth, mechanism, app, evidence ambiguity, authorization status, and slack.

Use one primary comparison, preregistered secondary families and adjustment strategy, and full reporting. Avoid unfocused pairwise testing of every subgroup.

## Required causal substudies (not optional if claiming mechanism attribution)

1. **Real deadline sweep:** randomize eligible effect admission around expected controller timing in DEV and fixed TEST conditions; execute real external-worker receipts. Avoid fake outcomes generated by subtracting inference from historical traces.
2. **Verification-information factorial:** cases where public verification changes what authorization should be; negative controls where information is redundant. Match observation content and enforcement tools.
3. **Decision-to-enforcement decomposition:** replay identical certified cuts with early gateway action, normal gateway action, and controlled gateway delay; preserve actual independent worker progression.
4. **Pre-dispatch vs already-in-flight effect:** distinguish cases where waiting inherently holds an undispatched action, versus cases where an external process keeps progressing during review.
5. **Restoration obligations:** explicit feedback vs no feedback, legitimate and forbidden restore variants; verify outcomes using hidden oracle only offline.
6. **Graph-oracle validation:** bounded states with known exact reachability, actual successful sibling witnesses, unobserved states marked UNKNOWN; compare with history-aware baseline metrics.

## Sample size and stopping

Before freeze, estimate paired discordance and minimal scientifically relevant difference from **DEV only**, and perform cluster-level power simulation over 216 source tasks. Report power for 5, 10, 15 point effects with a prespecified family/depth model, including intratask correlation. Increase fixed TEST population **before exposure** if power is insufficient. Use a registration date/hash and preserve revisions.

No significance-based peeking, effect-dependent stopping, or expansion after seeing confirmatory results. Complete all registered trials, with infrastructure retry exceptions predeclared and tracked. If technical barriers persist, report `INCOMPLETE`; do not rename the fragment a successful confirmation.

## Credit and compute authorization

The new user instruction supersedes the earlier $20 **credit ceiling**. Codex is authorized to consume research credits needed for the declared work, with no arbitrary research-credit dollar cap. Keep metering and runaway-process controls, cost/per-episode reports, finite workloads, scale-to-zero configurations, and explicit final totals. Do not erase previous finance records. Do not use real customer services or assume permission for out-of-pocket cash charges once credits are depleted; if only cash spend remains, request explicit authorization for that distinct payment method.
