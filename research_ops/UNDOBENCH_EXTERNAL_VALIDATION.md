# Independent benchmark validation — official UndoBench, local scripted baseline study

Upstream https://github.com/tradertanmay/undobench at commit4a25c4fa0f12bb6c79dc6e0e3a8f31deeb6af21e, cloned unmodified into ignored artifacts/external/undobench-v1; isolated Python3.14.7 venv, pip installation records retained. PackageSDK1.0.0, benchmark1.0.1/protocolV4: do not conflate their version labels. All upstream source/tasks/oracles/scoring unchanged. Original task definitions and public/native schemas used; no final TEST execution enabled.

Official doctor and smoke PASS. Smoke CONTROL succeeds and naive FAULT fails as reported by the diagnostic; this is not a model efficacy result. Smoke outputs are preserved. Five fixed DEV tasks cover messaging(RB-MSG-001/003), payments(RB-PAY-002/003), ticketing(RB-TICK-002). Two declared seeds42/43 yield10paired instances per baseline,20executions each; same instances reused across methods, not50 independent tasks. Five available published baseline wrappers ran with the official default scripted agent. No fresh Qwen generations and no inference cost. The officialEvoUndo adapter failed because evoundo_harness is unavailable; its CLI then raised KeyError control_rate. Failed output is retained and excluded from ranking, not a zero score. No substitute fake implementation was supplied.

| Official baseline | Control pass | FAULT/CRSR/EOR | DER | MER | FAULT local-state correctness |
|---|---:|---:|---:|---:|---:|
| Naive |10/10|2/10|.8|0|6/10|
| Checkpoint |10/10|2/10|.8|0|6/10|
| Saga |10/10|2/10|.8|0|6/10|
| Idempotency |10/10|6/10|.4|0|8/10|
| Verify-before-retry |10/10|4/10|0|.4|4/10|

The official engine serializes final_state_correct, forbidden_effects_absent, required_effects_satisfied, effect_multiplicity_correct, ordering_correct and overall_success in benchmark_hidden_trace.oracle_verdict. Our derived projection reads these existing evaluator records; it is not another oracle or modified official metric. Across100CONTROL/FAULT executions,14local-state/official-full scores disagree, all inFAULT. Looking only at local correctness ranks naive/checkpoint/saga6/10 aboveVBR4/10; official scoring ranksVBR4/10 above them2/10. Idempotency remains highest in both. This is a concrete ranking reversal already captured by official UndoBench. It contradicts novelty based on adding history-aware scoring alone.

AfterClick's existential current-recovery and prevention predicates cannot be computed from these terminal booleans alone. They remain unavailable, not assumed absent from every possible prior framework. A new progressing-time extension would require additional task/event contracts; results would be labeled an extension, not official comparable benchmark scores. Do not rename final_state_correct as recoverability.

Adapter: afterclick/review/undobench_adapter.py is a separate native tools plugin. Default construction refuses network use without caller-injected approved budgeted transport. Offline checks validate arguments, exact tool-result IDs, bounded calls, no response_format/tools mixing and no default paid path. Official recovery wrappers can wrap provided tools unchanged; unsupported staging is not fabricated. The adapter is not live validated, and no genuine model score is reported.

Paid DEV pilot and held-out comparison are BLOCKED by closed collection category/disabledmode and missing applicable new priced allocation. Existing balances and the proposed$20 envelope do not reopen this category. No TEST outcomes opened or final sample selected for favorable results. A future final protocol must be frozen only after DEV qualification and admission; no claim of a completed independent live confirmation.

ToolSandbox remains deferred: primary integration/official local checks work, but primary genuine-model qualification and paid admission have not passed; secondary breadth would not close this gap. No additional environment branch implemented.

Reproduce local baseline commands from w2/trials.jsonl; isolatedCLI doctor/smoke and exact upstream pin/install logs are inw2/raw. Read-only derived comparison: `.venv/bin/python -m research_ops.scripts.compare_undobench_metrics`. This is an independent benchmark implementation but still our local execution, not third-party replication.

Invocation provenance note: the official SDK's generic git metadata may reflect the AfterClick launch working directory. The separately captured upstream commit and unchanged source tree identify the actual benchmark code; official output metadata is not silently rewritten. The final optional shared-transport tests also verify that native external requests count in the same global cap and that proposed/old approvals cannot open a network path. These remain mocks, not inference qualification.

## Superseding authorization/scope note
The latestuser separatelyauthorized20USD for theprospectiveinternaltimingstudy; itis nowexecutedwithrealQwen(172DEV+CONFgenerations),notblockedbydisabledpaidmode. The externalbenchmarkadapter itselfstillhasno genuineQwenorTESTscore. CurrentresearchfocusdidnotspendadditionalGPUonaredundanthistory-scorepilot; itsunmodifiedofficiallocalbaselinechallengealreadyrejectstheproposedrankingnovelty. Do notpresentinternalx-studyasofficialUndoBenchresults.
