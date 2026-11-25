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
