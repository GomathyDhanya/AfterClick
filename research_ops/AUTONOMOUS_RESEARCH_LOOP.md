# Autonomous research loop — execution rules and state transitions

The goal is **conditional, self-adjusting scientific progress** across many Codex sessions. It is **not** indefinite unsupervised runtime, uncontrolled paid compute, or a guarantee of a positive finding.

## Per-iteration contract

1. Load `research_ops/STATE.json`, `NEXT_EXPERIMENT.md`, `EXPERIMENT_REGISTRY.jsonl`, claim ledger, and most recent *valid* run artifacts.
2. Confirm current branch/revision and state invariants; refuse to resume if a holdout was touched or there is an unresolved protocol change.
3. Identify key uncertainty. Write an analysis of at least two mechanisms that could explain the previous result.
4. Rank 2–4 possible experiments by expected discrimination, execution cost, reversibility, and validity risks. Choose one and document rationale.
5. Pre-register the chosen experiment (inputs, seeds, baseline, estimand, controls, endpoints, stop rule, budget).
6. Implement minimal needed change, run tests, run the smallest pilot, and checkpoint raw outputs incrementally.
7. Generate a scripted analysis using persisted data. Include attempted/valid/invalid/censored denominator and uncertainty, outcome breakdown by mechanism and model, resource cost.
8. Update claim ledger, decisions, progress, current state, and one next experiment.
9. Continue to next **local safe** experiment if gate passes and remaining bounded session budget permits. Otherwise stop with a user-action request.

## State machine

`NOT_STARTED` -> `AUDITING` -> `READY_LOCAL` -> `RUNNING_LOCAL` -> `ANALYZING` -> `GATE_DECISION` -> (`READY_LOCAL` | `WAITING_PAID_APPROVAL` | `BLOCKED` | `READY_FINAL`) -> `COMPLETE`.

State transitions must be atomic and idempotent. `STATE.json` records phase, phase_version, current_run_id, approved_run_id, approval_ceiling_usd, human_approval_required, last_valid_run_id, frozen_holdout_hash, initial and remaining credits (use null if unknown), and continuation_command. An approval applies to exactly one named paid protocol/version, never to a later retry/model swap.

## Mandatory stops

- P0 completion: stop for human evidence review before configuring Modal.
- Any paid compute or new external provider; budget or applicable credits unverified.
- Protocol/holdout change after freeze; before release or public posting.
- Causal oracle disagreement or failed placebo/reconstruction; repeated unclassified transport uncertainty.
- An experiment would use real recipients, third-party systems, or money movement.
- Same failure repeats after two focused repair attempts without new evidence; write the blocker instead of cycling endlessly.
- An analysis would require guessing data missing from logs; record as missing.
- No evidence supports proposed research direction: write an honest pivot memo, do not fabricate success.

## Resume instruction for any new Codex session

"Read AGENTS.md, research_ops/AGENT_MASTER_PROMPT.md, research_ops/STATE.json, research_ops/SESSION_HANDOFF.md, and research_ops/NEXT_EXPERIMENT.md. Audit their claims against saved artifacts, continue the next **unblocked local** evidence-gated experiment, preserve all logs and approval boundaries, and stop at any paid/holdout/publication gate."

## Anti-hacking checks

Compare each candidate method against random + strong simple baselines at matched budgets; count *attempted* evaluations including failures; prevent reused descendant trajectories leaking across splits; audit no-hidden-state features; distinguish no observed event from right-censoring; keep statistical units independent and clusters intact; require real receipt witnesses for irreversible events; record failure and false-positive examples in final paper.
