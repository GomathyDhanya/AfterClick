# Unified recoverability paper reproduction

The main manuscript is paper/AFTERCLICK_RECOVERABILITY_PAPER.md; earlier studies remain frozen. Start with the shared environment in REPRODUCIBILITY.md and the phase-specific guides. No command below makes a model request or starts an endpoint.

```sh
.venv/bin/python research_ops/scripts/verify_evidence.py
.venv/bin/python research_ops/scripts/verify_observability.py
.venv/bin/python -m research_ops.scripts.standardize_recoverability
.venv/bin/python -m research_ops.scripts.render_research --output /tmp/recoverability-original-NEW
.venv/bin/python -m research_ops.scripts.render_observability --output /tmp/recoverability-observability-NEW
.venv/bin/python -m research_ops.scripts.reproduce_tcope --output /tmp/recoverability-tcope-NEW
.venv/bin/python -m research_ops.scripts.reproduce_oecr --output /tmp/recoverability-oecr-NEW
```

Use unused destinations. The standardizer rewrites only derived CSV/new-figure outputs, never raw runs or frozen files. Its input hashes and raw protocol details are retained in the inventory; new figure provenance is paper/recoverability-generated/provenance.json. Old renderers regenerate into fresh paths; compare numerical CSVs with the matching original paper directories. No saved model output becomes a new generation.

To build the PDF, use Python with ReportLab 4.4.9 (a formatting dependency outside the scientific execution environment):

```sh
python3 research_ops/scripts/format_recoverability_paper.py --output output/pdf/AFTERCLICK_RECOVERABILITY_PAPER.pdf
```

Executed with the Codex bundled Python at `/Users/gomathydhanya/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`. pypdfium2 rendered each final page for visual review when the local Poppler binaries stalled. PDF layout is venue-neutral, single-column; it has no asserted named-conference template compliance. Use a venue template later without changing the scientific claims.

The fresh standardization run v0 records partial/failed checks: original executable reproduction completed one phase then was interrupted; fresh full tests stopped after207passes/1navigationtimeout; that isolated test passed on recheck. Independent observability reproduction completed both phases and all13savedCSVtables match. The earlier complete305-test pass remains historical. Read RECOVERABILITY_REPRODUCTION_REPORT.md before interpreting status.

A local tar.gz package includes tracked source, all sealed historical/audit runs, the two known-seed replica directories and opt-in generated OECR build. Its separate package-verification JSON supplies digest, size, member count and checksum comparison. It preserves previous archives and excludes the user's unrelated untracked ZIP/script, virtual environments and node_modules. Package creation and streaming member verification use no network or provider. No public release or paper submission is performed.

## Reviewer-response v10

Use `research_ops/scripts/reproduce_review_response.py --output FRESH_PATH` to reproduce the versioned102case scoring, with0modelcalls. `compare_undobench_metrics.py` reads official local baseline results; it does not launch a model. New plots use `render_review_response.py`. Official benchmark installation and source pin are in `UNDOBENCH_EXTERNAL_VALIDATION.md`; its isolated optional dependencies are not changes to the frozen AfterClick environment.

Fresh local evidence w3:320collectedtests pass and all6knownprotocolphases complete/numericallymatch. Later amended predicates/transport/Gateway checks are separate targeted runs; no claim of a324testfullsuite is made. `REVIEW_REPRODUCIBILITY_REPORT.md` records original mapper failures, supersededderivedscoring, dependency failure, timing scope and final targeted successes. The first two serialized/scoring defects are preserved rather than repaired inside old runs.

The new officialbenchmark scores use its defaultscriptedagent, not Qwen. New native model adapter and progressing A/B Gateway code are offline/local qualified; all real-model DEV/confirmation remains blocked. No copied protocol or adapter construction authorizes endpoint requests. The default agent refuses missing approved transport, and the explicit review allocation gate refuses old/proposed approvals. Shared ledger charging stays in the existing contingency category, with a versioned allocation_id, so future legacy reservations cannot silently double-spend a transferred category allowance.

## 2026-11-25 prospective study
Fresh330tests/1warningpass493.92s;12frozenQwensources/36validbranches145actualgenerations,DEVseparate27. Safe11/12vs10/12inconclusive;0vs2harmand1legitimateomission. Read research_ops/REVIEW_REPRODUCIBILITY_REPORT.md for exact saved-evidence verification/regeneration commands. New guard2.779124USD fromseparate20authority,cash0,idle. No paidrerunornewcollectionqueued. Old raw/frozenstudiesunchanged; allnewexperimental sourcearchivesbinddirtycheckoutbyexacthash.

## Latest supervision reproduction status
c0:all30newtests pass; combined360attempt358pass/2legacytimingfailures786.78s, no interruption; original rawfailures preserved. Fresh all330pre-extensiontests pass567.64s (UTCwrapper574.75s),1upstreamwarning. No assertions or frozen runtime changed. c1:all6newgenuineQwenbranchesre-scoreidentically,47archivedruntimefilesverify;27knownrequests,3/6validreviewrecommendations,not6/6. GenuineLLMevidenceisDEVonly,independentconfirmationNOTRUN. Numericalreproduction/figureverificationis saved-data evidence,notadditionalinference.

No-paid commands:
```sh
.venv/bin/python -m research_ops.scripts.verify_supervision --runs artifacts/research_runs/c1-supervisor-development-v1
.venv/bin/python -m research_ops.scripts.analyze_supervision --run artifacts/research_runs/c1-supervisor-development-v1 --output /tmp/afterclick-supervision-NEW.json
.venv/bin/python -m research_ops.scripts.render_supervision --data /tmp/afterclick-supervision-NEW.json --output /tmp/afterclick-supervision-figures-NEW
```
No closed live lifecycle may be resumed. Use fresh output destinations.
