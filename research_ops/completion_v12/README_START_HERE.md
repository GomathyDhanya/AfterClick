# AfterClick — Codex research completion kit (prospective v12)

**Prepared:** 2026-11-25. **Source archive:** `684_final 11.zip` (must be reconciled with live checkout). **Status:** protocol and execution handoff; none of the proposed v12 experiments is claimed to have run.

## What to do

1. Copy this entire directory into the actual AfterClick checkout as `research_ops/completion_v12/` (or give Codex its location).
2. Paste the full text of `CODEX_MASTER_PROMPT.md` into Codex and point it at that checkout. It must read these documents first.
3. Let Codex work through complete implementation, qualification, preregistration, genuine model trials, independent analysis, and paper creation. Do not treat a small success demonstration as the full evaluation.
4. Require a final handoff with actual run IDs and evidence paths. Read `09_ACCEPTANCE_AND_AUDIT.md` before accepting completion.

## Supporting files

| File | Role |
|---|---|
| `CODEX_START_MESSAGE.txt` | Short message to paste when supplying the whole kit to Codex |
| `CODEX_MASTER_PROMPT.md` | Full authoritative execution directive |
| `01_SCIENTIFIC_CHARTER.md` | Claims, RQs, falsifiable hypotheses, prior-work distinction |
| `02_BENCHMARK_SPECIFICATION.md` | Authentic task diversity, two applications, complexity, adversarial schedules, task oracles |
| `03_PREREGISTERED_STUDY.md` | Frozen trials, arms, randomization, primary endpoints, study size, model replication |
| `04_RECOVERABILITY_GRAPH_AND_ORACLES.md` | Graph schema, counterfactual provenance, existential vs robust feasibility, certificates |
| `05_LATENCY_AND_INTERVENTION_ABLATIONS.md` | Timing, information, enforcement, staging, restoration experiments |
| `06_MEASUREMENT_AND_STATISTICS.md` | Scoring, statistics, intervals, power, interpretability, failure attribution |
| `07_ENGINEERING_AND_EXECUTION_RUNBOOK.md` | Repo-specific integration, local qualification, full execution, records, resumability |
| `08_PAPER_AND_VISUALIZATION_PLAN.md` | Evidence-backed figures, manuscript, prior-work comparisons |
| `09_ACCEPTANCE_AND_AUDIT.md` | Definition of complete, data checks, noncompletion categories, publication readiness |
| `templates/task_contract.schema.json` | Task contract shape for Codex to implement/validate |
| `templates/task_contract_example.json` | Illustrative **design example**, not a completed tested task |
| `manifests/task_design_slots_216.csv` | 216 TEST enrollment slots; **not authored task content** |
| `manifests/task_design_slots_72_dev.csv` | 72 DEV enrollment slots; not authored task content |
| `manifests/prospective_counts.json` | Arithmetic and planned study sizes; no experiments executed |
| `references/*` | Earlier evidence syntheses and v12 proposal; provenance, not new results |

## Existing v11 record to preserve

- Frozen live intervention: **12 independent source tasks, 36 valid branches, 145 genuine Qwen3.5-9B generations**. Immediate protection **11/12** safe completions, verify-first and delayed containment **10/12** each; no demonstrated superiority.
- Two-source independent-supervisor DEV: **27 generations**, **6 valid branches**; fast deterministic protection and stage-first **2/2** safe, sequential **1/2**. Only **3/6** structured supervisor outputs passed validation. **Not confirmation**.
- Exact original finite model has **256 abstract states** with **10** states admitting an admissible repair, **relative to its fixed-time operation set**; not an empirical deployment rate.
- 102 historical backend cases, 78 determinate. Local rollback disagrees with full historical recoverability in **42/78**. The existing UndoBench evaluator already checks history; do not claim that as a new invention.
- Two legacy timing tests failed in the previous combined 360-test attempt. Neither should be hidden or silently relaxed.
- V11 heldout hashes, archived traces, source fingerprints, analysis, and manuscripts must remain immutable. Branches across a common source are **not independent samples**.

## Updated resource authorization

The user has **explicitly removed the previous $20 research-credit ceiling for the new completion program**. Codex may use the credit resources necessary for the scientifically justified preregistered studies. It must still measure and log usage, guard against infinite loops or broken deployments, and stop if spending would leave available credits and create cash charges not explicitly authorized. Do **not** alter historical spend records or pretend the previous experiments are included in a new allocation. Unbounded credits are not permission to destroy data, use real customer systems, or create unlimited unscientific repeats.

## Paper positioning

Working title: **AfterClick: When Safe Decisions Fail to Produce Safe Outcomes**. Proposed subtitle: **An Empirical Study of Time, Irreversible Effects, and Task Obligations in Tool-Using Agents**.

This is a hypothesis-driven empirical evaluation. If the new results justify a narrower title or demonstrate a genuinely new graph technique, revise the title **after** evidence analysis—not before. In particular, never equate a failure by one controller with proof that recovery is impossible.
