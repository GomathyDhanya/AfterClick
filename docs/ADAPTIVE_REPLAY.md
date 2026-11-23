# Adaptive browser replay pilot

P0 evidence status (2026-11-22): implementation and test-double checks pass in the current dirty
checkout; live replay has **not** passed. Archived runs `d09833439a904963a00d08278fa83075`
and `990e0e825b2a45b3afb5cb1b8fceeff8` contain 12 cases total, all invalid. Each first fails
on `generateContent` HTTP503, then freezes generation on uncertain usage. The second also
contains one clock-pause past-time error. A local 50ms probe did not reproduce that clock error;
the negative diagnostic is retained. These archives are not training/effect-estimation data.
The historical authorization described below does not authorize any new provider call. See
`../research_ops/P0_EVIDENCE_AUDIT.md`; current P0 stops for human review with $0 Modal use.

The Gate 3 implementation connects Gemini to the existing Playwright gateway. The provider receives
an explicit public task, rendered UI text, live form values, visible controls and public tool feedback.
It never receives database snapshots, field owners, scheduler state, oracle labels, branch names,
checkpoint hashes or the contract's research fields. A strict parser rejects unknown JSON fields,
duplicate keys, arbitrary code, external navigation and invalid dropdown values.

## Provider and spending

The user authorized a Gemini Lite pilot on November 18, 2026. Model discovery succeeded, but
`gemini-2.5-flash-lite` returned HTTP 404 for this account: unavailable to new users. The implemented
adapter pins `gemini-3.1-flash-lite`, which passed token counting and generation. It records the
resolved model version, exact system/user prompt, generation parameters, response, proposed action,
provider token counts (including thinking), and estimated cost. Opaque response signatures are
retained as metadata. No Tinker API is used.

The price schedule checked on November 18 is $0.25 per million text input tokens and $1.50 per million
output tokens including thinking, from [Google's pricing documentation](https://aistudio.google.com/docs/pricing#gemini-3.1-flash-lite).
The adapter uses [generateContent](https://aistudio.google.com/api-reference/generate-content)
and JSON output, with minimal thinking. Pricing is an estimate at the standard uncached paid rate,
not a billing invoice; a free tier or caching can make actual charges lower.

Before each generation, the adapter counts prompt tokens and reserves the full output-token cap.
The whole pilot shares a dollar/call budget. No generation is retried automatically. Unknown usage
or a possible charge after a transport failure freezes further generation and retains its reservation.
Malformed/blocked/truncated answers remain in the journal; known usage is charged to the estimate
even when the answer cannot be executed. Credentials are read only from `GEMINI_API_KEY`, never
written into prompts or artifacts. Model aliases are not accepted by this price-pinned adapter.

## Experimental design

Each workflow/seed case independently reconstructs **12 real Chromium/PostgreSQL branches**:

| Condition | Selected tool call | Continuation |
|---|---|---|
| execute | Execute workflow mutation | Fresh model decisions |
| suppress_fixed | Suppress mutation | Recorded execute decisions where semantically applicable |
| suppress_adaptive | Suppress mutation | Fresh model decisions from changed UI |
| lost_ack | Commit mutation, abort its HTTP response | Fresh model decisions from failed-save UI |
| null_execute | Read Description | Fresh model decisions |
| null_suppress | Suppress that read | Recorded null-execute decisions |

Each condition also has a placebo using its recorded decisions. Placebos verify deterministic
application replay, **not deterministic resampling of a stochastic model**. Fixed replay checks the
same target/control, enabled state, save status and original field value for mutations. Inapplicable
actions are explicitly skipped, never silently rebound to a different record or new field value.
A failed task or step limit is reported separately from reconstruction validity.

The prefix navigates to the initial fixture; the goal description has not yet been edited. The selected
review/priority/status mutation is **planted by the experiment**, not claimed to have been chosen by
Gemini. The model then completes the legitimate task through the browser. These are policy
continuations after planted interventions, not estimates of organic agent mistake frequency.

The backend logical clock stays at zero throughout the bounded decision window. Client autosaves
advance 600 ms and settle after each action. After the browser closes, all branches release the same
worker/delivery schedule to horizon 300 (worker delay 100, delivery delay 100). Provider latency does
not advance the world. This deliberately restricted schedule has no independent collaborator or
reactive collaborator policy; asynchronous interleaving during model deliberation remains future work.

The lost-ack branch records a successful server response and the committed operation before aborting
the response seen by the UI. Retrying uses the **original operation and action identity**, even though
the retry itself is a distinct tool call. The raw request trace records both calls. A failed browser save
alone is not proof that a mutation committed.

All 12 pre-action DB/storage/observation/history/pending-work checkpoints must match. All six
placebo outcomes and continuation observations must match. Executed/suppressed reads must have
identical business outcomes. Lost-ack evidence must establish an actual commit. Any failure invalidates
the case; raw branch records and errors remain on disk.

Semantic comparison uses multisets of record/field transitions, resolving generated notice IDs through
recorded parents. It retains multiplicity and ignores action-number differences. Provenance, declared
parents and journal happens-before edges remain separate. No dynamic read sets are instrumented,
so data-dependency edges remain explicitly absent. Validated intervention contrasts are paired
realized outcomes, not proof of population-level action necessity.

## Reproduction

Start PostgreSQL and build the frontend as described in the README. Configure `GEMINI_API_KEY`
outside source control, then run a bounded live pilot:

```sh
uv run python -m afterclick.replay.adaptive_runner \
  --seeds 7 19 --budget-usd 0.085 --max-calls 80 \
  --output artifacts/adaptive-live
```

This executes review/readiness, priority/escalation and status/summary with two seeds. Use
`--contracts fixtures/tasks/review-readiness-v2.json --seeds 7` for a smaller single-case run.
These seeds change the deterministic scheduler's tie-breaking, not a claimed model RNG seed.

Each invocation writes a UUID directory with raw branch records, source/dependency hashes, an
append-only model-call journal, contracts, validity certificates, goals, effects and aggregate usage.
The top-level report is only a convenience pointer; prior runs are retained.

Replay an existing report without credentials or model calls:

```sh
uv run python -m afterclick.replay.adaptive_runner \
  --replay-report artifacts/adaptive-live/report.json \
  --seeds 7 19 --output artifacts/adaptive-recorded
```

Use the same contracts/seeds/step cap as the source run. Recorded responses require exact public
input and system-prompt equality. A mismatch fails closed. Such runs are labeled
`recorded_model_responses`, have zero live calls, and cannot count as new LLM evidence.

The ordinary test suite uses explicit observable-state test doubles and HTTP mocks, with real
PostgreSQL/Chromium integration tests. It never reads provider credentials or spends money.

## Limits of this milestone

The three workflows share a scripted notification receipt mechanism. This pilot does not establish
three independent irreversibility mechanisms, a learned recovery critic, boundary discovery,
statistical necessity, or a safety improvement. The oracle remains independently evaluated; it is
never used to choose browser actions. Organic source trajectories, richer interleavings and broader
collaborator schedules are follow-on validity work before generalization claims.

## P1 continuation status
P0 review was accepted. The provider-independent visible-only boundary and Modal adapter now
pass local tests and three HTTP-mock cases on actual PostgreSQL/Chromium. Gemini prompts and
recorded format remain compatible. The approved private9B endpoint attempt stopped in provisioning
with zero model calls; cleanup is confirmed. This adds no live causal case to the old invalid
Gemini archive. See research_ops/P1_FINAL_REPORT.md and STATE.json; no new paid run is authorized.

CurrentP1 update: both9B provisioning attempts retained with0generation; no live Qwen replay evidence. Full200localtests pass. 4B is a separate proposed arm awaitingapproval; finaltrajectorymodel undecided. Existing3case/36branch HTTPmock evidence remains testdouble only.

## 2026-11-23T02:26:23.520914+00:00 — observer blinding amendment
Code review found legacy public_history exposed literal suppressedfeedback. Newdefault replacesitwithneutralcompletedack while rawGateway retainsactualintervention. This controlledack is partofnewprotocol; passblind_interventions=False onlywhenreproducinglegacyrecordedinputswiththeiroriginalscope. Newpublicsyntheticpolicy rejects explicitlabel beforeHTTP. Oldmockcertificates establishtheiroriginalunblindedfixturebehavior, not prospectiveblindlivevalidity. NewblindedHTTPmockcase12/12branchespassed; livegatepending.
