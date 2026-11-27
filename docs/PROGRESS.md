# Current artifact progress — 26 November 2026

The canonical paper is the supplied 17-page LaTeX manuscript, now at `paper/main.tex` with compiled `paper/AfterClick.pdf`. The active artifact is separated from exact frozen history. All prior development logs, including the complete former progress document, remain in source snapshot `31eab61870befc520841d11f422bb1a372ba92b8`.

Completed cleanup work:

- Preserved and verified a self-contained Git bundle of all 2,754 prior tracked paths. Restored source and raw gate evidence; all 180 original frozen source/gate hashes verify unchanged.
- Removed the 1,445 V2–V6 catalog paths from the active tree, retaining V7. Archived obsolete TCOPE, OECR, model-sprint, earlier research/replay/review implementations and corresponding tests by exact pinned source revision.
- Kept current benchmark and shared dependencies, including the UndoBench adapter and small browser test HTTP server. Removed all obsolete compatibility wrappers and migrated their surviving callers.
- Promoted one canonical LaTeX manuscript. Eight plots read verified reports directly; ten numerical tables and claim mappings are generated from the same evidence. Earlier manuscripts, renderers, plots, planning files and operational handoffs are recovered through the archive index.
- Added one authoritative evidence index mapping the four research questions and supplementary analyses. Original compact reports, assignment denominators, invalid/unknown outcomes and all-case evidence remain unchanged.
- Reconciled existing CI and shell entrypoints; no new workflow or paid activity introduced.

Executed validation: all 39 active tests pass; the unchanged historical regression passes 417/417 in a separately restored source environment with its original raw fixture. The two-application real PostgreSQL/HTTP demonstration passes 12/12. Current normalization, independent pointer checking, statistical analysis, duty reconstruction and actuator verification reproduce five compact reports byte-identically; all 34 late-receipt cases also pass separate temporal verification. Historical frozen analysis reproduces statistics and both graph cohorts after all 180 integrity checks. The canonical LaTeX manuscript compiles to 17 pages and all rendered pages have been visually checked. Final fresh-clone validation remains pending; see `archive/audit/VALIDATION.json` for terminal status.

Reproducible current commands:

```sh
uv sync --frozen --group research
python -m research_ops.publication.program verify-data
bash scripts/build_paper.sh
bash scripts/test.sh
bash scripts/demo.sh /tmp/ac-demo-NEW
```

See `docs/REPRODUCIBILITY.md` and `archive/README.md` for source/raw restoration, isolated PostgreSQL prerequisites and separate historical regression. Original research-program status remains incomplete: 1,425 unexecuted assignments and documented causal/human-review gaps. Cleanup adds no study outcomes.
