# Absolute financial policy — $30 Modal research project

**Reading this file never authorizes paid usage.** User has $30 total available on Modal; first verify the current remaining *applicable* compute-credit balance and any unrelated workspace usage. No paid actions before explicit user approval of a named experiment with a fixed maximum USD, exact model, request cap, and stop rule. Preserve at least $5 for final verification. Earlier approvals do not carry to later runs/retries.

| Category | Maximum credit allocation |
| --- | ---: |
| P1 deployment/smoke | $2 |
| P2 valid live replay pilot | $5 |
| Targeted additional trajectories | $10 |
| Result-driven follow-up | $8 |
| Final validation reserve | $5 |
| TOTAL | $30 |

These maxima are provisional allocations; spend only when an experiment can change a research decision. Keep most search, causal oracle, analysis, and learning workloads local. Use private *Dedicated Endpoints*, billed for compute, only when the user confirms compute-credit applicability. Starter compute credits **exclude** token-priced Model APIs (policy effective September 2026). `Qwen/Qwen3.5-9B` is the initial browser action model, not the risk predictor. A switch to another action model is a new registered arm, not transparent fallback. User should set Workspace usage budget <= available cycle credit and net spend limit $0 for no out-of-pocket charges if possible; thresholds are workspace-wide and metering can lag.

### Before starting any charged run
1. Prepare protocol with run name, max dollar spend, estimated rate, GPU choice, current credits/billing source, price assumptions, tokens, time, count and concurrency caps, retry bound (max one), failure conditions, stop rule.
2. User approves precisely this run and cap. If no recorded approval, fail closed.
3. Confirm private authenticated endpoint, min containers 0, max containers 1; never leave paid idle containers.
4. Log timestamps, request tokens, errors/uncertain requests, model config and approximate GPU/CPU runtime. Stop *before* the cap by a buffer because provider accounting can lag. Stop dedicated endpoint when finished if no longer needed.
5. Reconcile actual usage with dashboard before next paid experiment. If budget is exhausted, move to local-only science; do not silently charge a card.

Source documentation: https://modal.com/pricing ; https://modal.com/docs/guide/budgets ; https://modal.com/docs/cli/latest/endpoint ; https://modal.com/library/qwen/qwen3-5-9b.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

The latest user mandate (AUTHORIZATION.json and source hash) supersedes earlier per-experiment
approval requirements: up to $20 additional, reserve >=$8, category caps 3/3/4/8/2, existing endpoint
ep-NtuMALXsRWKk5JLfZk4BOF only. No out-of-pocket, token-billed API, deployment, fine-tuning or
other provider. Workspace cap raised with authorization from $2 to $3, effective default net spend
$0; all current work is idle. The old approvals remain closed, but are not the authority for new
standing-authorized runs. Emergency stop permission applies only to the named new endpoint.
Positive observed account adjustments are conserved at high-water; later lower billing does not
release budget automatically. Current conservative balance $27.48; newest UI/CLI $27.64. Exact
project invoice unknown. Verify fresh balance/resources before any future billable admission.


## 2026-11-23T20:08:20.737981+00:00 — format-pair control update
Under standingauthorization, cap3→3.5 was saved after no unrelated activeapp/endpoint found, for i1 max0.60 only. Effective defaultnet0 preserved. Latestreportedcredit27.41, highwater-conservative27.39, guardprojection27.0655. No additionalpaidwork queued. No per-run reapprovalroutine undercurrentmandate; future paidruns stillneedfreshprotocol/admission/reserve checks.

## 2026-11-24T01:34:36.848712+00:00 — unified continuation mandate
The latest directive, archived at `artifacts/research_runs/t0-execution-repair-offline-v1/raw/user-directive.txt`, supersedes the narrower $6 sprint-only restriction for NEW experiments. It does not change or reopen that historical sprint. Use existing Supervisor / original baseline / $20 total additional ceiling, all historical charges (1.440697126 conservative USD), unchanged categories 3/3/4/8/2, reserve >=$8 credit and $8 confirmation category. No new endpoint/out-of-pocket/token API/fine-tuning. Exact authority/hash: research_ops/UNIFIED_AUTHORIZATION.json.
