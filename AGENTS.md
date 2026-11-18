# AfterClick continuation instructions

At the start of a session, read `README.md`, `docs/RESEARCH_SPEC.md`,
`docs/ARCHITECTURE.md`, and `docs/PROGRESS.md`; inspect Git status and continue the earliest
incomplete milestone. The user-supplied implementation brief is in `docs/IMPLEMENTATION_BRIEF.md`.

Preserve validated foundations. Do not report proposals or unexecuted checks as completed work.
Use real PostgreSQL for integration/replay/recovery evidence. Keep experiments in isolated `ac_*`
schemas; never use snapshot restoration as a live recovery primitive. Keep invalid and failed
trials in the artifacts. Models must not receive oracle results or hidden scheduler state.

Run relevant tests, update `docs/PROGRESS.md`, and preserve a reproducible command at the end of
each meaningful development session. Read `docs/REPRODUCIBILITY.md` for environments and artifacts.

Do not spend Tinker credits automatically. Before any paid fine-tuning, inspect the current API and
supported model, validate the dataset, prepare the script and tiny smoke configuration, estimate
cost, document environment variables, and obtain explicit user authorization. Never commit secrets.
