# Current artifact progress — 26 November 2026

The canonical paper is the supplied 17-page LaTeX manuscript, now at `paper/main.tex` with compiled `paper/AfterClick.pdf`. The active artifact is separated from exact frozen history. All prior development logs, including the complete former progress document, remain in source snapshot `31eab61870befc520841d11f422bb1a372ba92b8`.

Completed cleanup work:

- Preserved and verified a self-contained Git bundle of all 2,754 prior tracked paths. Restored source and raw gate evidence; all 180 original frozen source/gate hashes verify unchanged.
- Removed the 1,445 V2–V6 catalog paths from the active tree, retaining V7. Archived obsolete TCOPE, OECR, model-sprint, earlier research/replay/review implementations and corresponding tests by exact pinned source revision.
- Kept current benchmark and shared dependencies, including the UndoBench adapter and small browser test HTTP server. Removed all obsolete compatibility wrappers and migrated their surviving callers.
- Promoted one canonical LaTeX manuscript. Eight plots read verified reports directly; ten numerical tables and claim mappings are generated from the same evidence. Earlier manuscripts, renderers, plots, planning files and operational handoffs are recovered through the archive index.
- Added one authoritative evidence index mapping the four research questions and supplementary analyses. Original compact reports, assignment denominators, invalid/unknown outcomes and all-case evidence remain unchanged.
- Reconciled existing CI and shell entrypoints; no new workflow or paid activity introduced.

Executed validation: all 39 active tests pass; the unchanged historical regression passes 417/417 in a separately restored source environment with its original raw fixture. The two-application real PostgreSQL/HTTP demonstration passes 12/12. Current normalization, independent pointer checking, statistical analysis, duty reconstruction and actuator verification reproduce five compact reports byte-identically; all 34 late-receipt cases also pass separate temporal verification. Historical frozen analysis reproduces statistics and both graph cohorts after all 180 integrity checks. The canonical LaTeX manuscript compiles to 17 pages and all rendered pages have been visually checked. Fresh-clone validation at cleanup commit `317b2180` also passes all 39 active tests, compact verification, locked frontend build, eight-figure/ten-table generation, 17-page LaTeX compilation and all 12 two-application probes. The optional official engine and retained adapter import successfully from its archived pinned SDK, with zero model calls. The documented restoration script was actually executed with both raw archives and verifies all 180 original frozen hashes. See `archive/audit/VALIDATION.json` for the separate terminal records.

Reproducible current commands:

```sh
uv sync --frozen --group research
python -m research_ops.publication.program verify-data
bash scripts/build_paper.sh
bash scripts/test.sh
bash scripts/demo.sh /tmp/ac-demo-NEW
```

See `docs/REPRODUCIBILITY.md` and `archive/README.md` for source/raw restoration, isolated PostgreSQL prerequisites and separate historical regression. Original research-program status remains incomplete: 1,425 unexecuted assignments and documented causal/human-review gaps. Cleanup adds no study outcomes.

Final active inventory: **632 files**, down from 2,754 (77.1% reduction). Exactly 2,174 original paths are archived in the pinned snapshot; 52 current artifact/audit/license paths are added. The archive audit contains both inventories, exact removed-path list, import/dynamic-reference reports, test results and numerical agreement. No original scientific evidence or history is destroyed.

## Verification of the pushed artifact

Rechecked pushed commit `a9ead3d7` from a fresh local clone. Executed the documented `scripts/test.sh`, `scripts/reproduce.sh` and `scripts/demo.sh` commands: 39 tests pass, lint/format and compact verification pass, the frontend builds, all 12 real PostgreSQL/HTTP two-application probes pass, and the paper rebuild has 17 pixel-identical rendered pages with ten byte-identical tables. Re-executed `program reproduce-existing` against the documented restoration: all 180 frozen hashes, original numerical/assignment results and both trajectory graph checks pass. Python compilation, shell syntax and Compose configuration pass. No model/provider calls or paid activity occurred.

Fixed the only observed defect: `evidence/README.md` still linked to the pre-consolidation claim-matrix location and described archived directories as active. All current relative Markdown links now resolve. GitHub Actions returned no run for the checked commit; hosted CI is not represented as passing. Details are appended in `archive/audit/VALIDATION.json`; complete local logs are under `artifacts/verification-20261126-222713/`.

## Independent temporal validity audit — 27 November 2026

Executed the user-requested audit separately on `audit/temporal-validity`. All new
code and outputs are under `research_ops/temporal_validity_audit/`. Original source,
registrations, raw archives, outcomes, financial records and main remain unchanged.
No workflow, provider/model call, GPU provisioning or paid activity was introduced.

Verified all three named archive hashes and the Git bundle; restored all 2,754
historical tracked source files and audit-relevant raw TEST evidence separately.
All 180 frozen source/gate hashes, 141 compact manifest files, and 23 internal
execution payload source inventories agree. Initial full extraction exhausted
disk; that failed attempt is retained and the final selective restoration is
documented. It omits redundant copies of unrelated raw studies, preserving the
original archives intact.

Independent outcome reconstruction reproduces 1,073 valid / 166 invalid internal
executions, 207 P0 stress executions, 137 prohibited pending requests with 137
pending-specific forbidden effects, one suspension transition, 62 legitimate
completions, and the 132/132 P0 versus 2/132 P1 matched forbidden histories.
There are no independent L/G/F/Y scoring disagreements. All 3,812 raw actor
responses in the 207 P0 stress executions were examined, including 2,463 eligible
decision points. Only one native protection proposal occurs; it dispatches and
commits after admission. No historical eligible protective proposal is rejected
or skipped by batching.

Admission precedes the first actor response in 56/137; five cross admission while
waiting in the recorded infrastructure queue. Sixty executions commit ordinary
business work before admission; none proposes protection before admission.
Thirty-four retain demonstrated execution headroom at a 2,000 ms sensitivity
margin. These are retrospective descriptive indicators, not counterfactual
prevention guarantees or causal measures of temporal competence. Exact historical
authorization reads, commit instants and provider-internal latency components
remain unrecorded.

Executed ten scripted native-response conditions across two applications, two
families and two seeds using the exact restored runner, real Chromium,
PostgreSQL `ac_*` schemas, workers, HTTP receiver and offline evaluator. All 80
planned conditions have technically valid trials; all 83 attempts remain,
including three invalid setup/deadline attempts. Early suspend/cancel each prevent
the effect in 8/8 trials. Same-batch invalid arguments and seven real version
conflicts skip later suspension; separate native calls execute it. One valid
version-race trial did not produce conflict and remains a manipulation miss.
All eight deliberately late suspensions commit without preventing the effect.

Validation: 14 audit tests, 39 active tests and 10 relevant unchanged historical
tests pass. Eight vector PDF/300-dpi PNG figures, rule-selected cases, task-cluster
uncertainty, sequence stability diagnostics, a ten-question scientific verdict,
and a separate verified Experiment 1 replacement are generated. The conclusion
rejects interpreting all autonomous failures as evidence of temporal reasoning
deficits and rejects batch-abort suppression as the observed cohort's explanation.

Executed/reproducible command (zero inference):

```sh
bash research_ops/temporal_validity_audit/REPRODUCE.sh --saved-only
```

The full entrypoint additionally verifies/restores archives and resumes only
missing diagnostic conditions. See the audit README and retained failure logs.

The supplementary scan examines all 19,977 actor responses in all 1,073 valid
internal executions: seven suspension proposals in five episodes. Six
parse/dispatch/commit; one string-encoded P3 proposal is rejected by syntax,
after admission. None is skipped after an earlier action. A vocabulary
cross-check found and corrected the initial supplemental omission; its log and
a regression test are retained. The primary P0 findings are unchanged. Four successful transactions follow
actual admission; two follow an already-blocked admission decision under other
policies. Separately, all 264 reviewer JSON recommendations are suspension and
receive HTTP 200, including 39 in downstream-invalid episodes (225 valid).
All 132 matched P0/P1 initial source-cut semantic hashes independently agree.
The stock test wrapper could not locate `uv`; equivalent compact verification,
full-tree lint/format and pytest checks passed using the existing `.venv` tools.

Separate invalid-run accounting preserves 147 finite-job request-guard failures,
16 closed-browser/page failures and three HTTP read timeouts, all without
completed scores. Their 2,182 actor requests contain 2,179 recorded responses and
three unknown responses. One additional P1 suspension has an HTTP 200 observation
in an invalid episode; its complete outcome remains UNKNOWN and is not pooled
with the seven proposals in valid episodes. No invalid P0 protective proposal is
recovered. The final verifier also checks all 1,073 valid worker-error logs and
all 2,754 historical Git blobs after diagnostics.

Eight additional native I controls use longer effect lag to test admitted but
undelivered work: all eight are technically valid, suspension returns after
admission and before independent receipt, and the pending physical effect still
occurs. Total new diagnostics: 91 attempts / 88 valid / three retained invalid.
Response opportunity is conservatively client-dispatchable: 62 episodes, versus
63 with syntactically valid browser-action responses. The excluded-from-B response
has an invalid first business argument; its raw evidence and syntactic count remain.
The 60 demonstrated execution opportunities and 34 at 2,000 ms remain unchanged.
