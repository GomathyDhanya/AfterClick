# P1C gate FAIL; local integration PASS

HEAD `1fa4f02610a4e556b84a3984dc1e650b2b78cca7`, uncommitted. Current full suite212 passed
(156.76s,one upstream warning). P1A adapter/test integration passes. P1C is incomplete: one live
legitimate task passes, but the independently checked two-action task fails. No complete live
counterfactual case exists. No action model is qualified for trajectory collection.

| Existing-endpoint run | Metadata | Generations | Decision-valid | Browser task result | Replay |
| --- | --- | --- | --- | --- | --- |
| p1c-existing-4b-validation-v1 | 503 | 0 | not measured | unattempted | unattempted |
| p1c-existing-4b-validation-v2 | 200 after fresh warming | 1 | 0/1 | unattempted | unattempted |
| p1c-existing-4b-validation-v3 | 200 after fresh warming | 11 | 11/11 | single goal PASS; two-action FAIL | unattempted |

V2 returned valid JSON with a forbidden nonempty read value. Its runtime rejection stays invalid.
V3 is a separate conditional-schema/prompt arm. Read-only smoke passed; a legitimate Description
update passed in2decisions. Multiaction task emitted8Description fills, including7repeats after the
field visibly satisfied its goal, never changed Priority or terminated. Independent task successfalse;
no unauthorized semantic events in the two task traces. This is a task failure, not invalid JSON,
a recovery class, an irreversible event or a population harm/completion estimate. Stop-first-failure
prevented replay collection. All11 live responses used12781tokens;0cachehits/uncertaincalls/retries.

p1f-20261123-recorded-task-audit confirms all11 exact request/config/output replays. Priority-to-High
instruction/goal and visible Normal were present; every request hash differs. This excludes omitted
task state and adapter cache for this trace. Model planning, prompt salience and installed grammar
behavior remain alternatives. Simple Python schema admits select Priority High; this does not prove
live grammar reachability. No bypass or posthoc relaxation of the failed task is accepted.

Historical9B/private4B attempts all made0generation before startup deadlines; they do not measure
model quality. User-owned existing public4B was reused only under explicit user authentication
exception and separate approvals. Temporary min1 warming worked. After v3,min0/max1/buffer0/idle2
and idle0containers verified; endpoint retained, never stopped/deleted. All approvals are closed.
Conservative account observation: creditsused$1.42/remaining$28.58,cap$2/headroom$0.58,billed$0.
UI lagged atused$1.24; both observations retained. Approximate v3 account credit delta$0.28; exact
per-run invoice null. No new paid request is authorized. See P1_COST_REPORT.md.

Local blinded conditional mock passed15requests,12real-PG/Chromium branches,6recorded placebos,
null and committed lost-ack checks. Original3-family mock36branches used legacy unblinded feedback;
those old results cannot establish blinded model behavior. Neither mock is a live policy sample.
Full212suite plus101targeted agent checks and5finance QA pass; these are separate batches.
Scoped source/test/helper lint passes. Broader helper lint records an unchanged legacy
research_ops/scripts/modal_smoke.py formatting issue; it was neither run nor reformatted.

P2 local mechanism prerequisite independently passes48enumerated backend cases (36known,6UNKNOWN,
6CENSORED,0invalid). It does not unlock live collection. C1/C2/C3, novelty, organic unauthorized
mistake frequency, matched-utility safety and held-out generalization remain untested.
No training/holdout/push/publication. Full raw artifacts and source snapshots preserved.

Repro `.venv/bin/pytest -q`; offline P2 command is in P2_FINAL_REPORT.md and SESSION_HANDOFF.md.
Next preferred: exact-input schema-only diagnostic, with prompt held fixed, prepared as paired
payloads in p1f/raw/paired-schema-probe-inputs.json. Any live execution needs a separately prepared
bounded controller, protocol and explicit dollar approval; no silent retry/model switch.


## 2026-11-23T17:45:40.517270+00:00 — bounded study checkpoint

**P1C — minimum hybrid live replay PASS**

p1c-new-endpoint-live-v1:16 valid model decisions, simple task PASS, multi-action FAIL, one invalid case (6/7 valid branches). p1c-new-endpoint-live-v2:19 valid model decisions, simple task PASS, multi-action FAIL, one valid 12/12-branch case. Visible Retry save guard is a separately declared hybrid arm. The selected consequential action is planted. No general agent competence or organic-error claim.

Authoritative synthesis: paper/PAPER.md; raw run IDs in evidence/research-20261123/index.json.


## 2026-11-23T20:06:10.697972+00:00 — native interaction and observability extension

New i1 comparison: native2requests PASS twofieldtask; JSON3requests repeatedsatisfied Description twice/incomplete. Bothschema-valid, allactions throughGateway, matchingtool_call_ids/results. Preferred newdriver native, originalJSON/frozenreplaypreserved. n1/mode, fixedorder, cache/warm/prompt confounding: provisionalworkflowchoice, not reliabilityestimate. Native counterfactualreplay notyetvalidated. No further interfaceoptimization.
