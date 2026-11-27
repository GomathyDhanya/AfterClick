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
