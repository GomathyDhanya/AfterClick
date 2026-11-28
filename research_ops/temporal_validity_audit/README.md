# AfterClick independent temporal validity audit

Executed on `audit/temporal-validity` with zero paid inference. Start with
[SCIENTIFIC_VERDICT.md](SCIENTIFIC_VERDICT.md) and [AUDIT_REPORT.md](AUDIT_REPORT.md).
The complete numerical reconstruction is in [report.json](report.json).

All preliminary counts reproduce. The 137 prohibited-pending P0 executions have
137 pending-specific violations, one late protection proposal, zero rejected or
skipped protective proposals, and zero timely protection. Admission precedes the
first response in 56/137. Sixty executions commit ordinary business work before
admission; none proposes protection before admission. At a 2000 ms conservative
headroom margin, 34 retain demonstrated execution opportunity.

The historical native protection path is functional in newly executed controls.
The primary A–J controls have 83 attempts, 80 technically valid trials, three retained invalid setup
attempts, and one valid version-conflict manipulation miss. Historical outcomes,
exploratory retrospective analyses and scripted diagnostics are separate.

## Reproduce

Use the existing locked research environment and local real PostgreSQL described
in [the repository reproducibility guide](../../docs/REPRODUCIBILITY.md). No Docker
volume reset is required. The controls create and drop only fresh `ac_*` schemas.
Chromium must be installed. The source restoration is from Git, not the active
implementation. The original local archives and bundle must remain available at
the locations in `archive/SNAPSHOTS.json`.

```sh
uv sync --frozen --group research
bash research_ops/temporal_validity_audit/REPRODUCE.sh
```

The full command verifies all archives, restores relevant raw evidence, performs
the independent extraction, resumes absent scripted controls, regenerates
statistics/cases/figures/reports, runs tests and verifies hashes. Already completed
valid controls are read rather than rerun. Original invalid attempts are retained
alongside separately named retries. To execute fresh controls again, preserve the
existing `controls/` directory under a new name before invoking the full command;
new timings will differ. Do not overwrite the original diagnostic evidence.

The source-only restoration reports missing raw gate files until `integrity.py`
restores them. The full first extraction encountered disk exhaustion; its failure
log remains. The reproducible selective restoration needs about 2 GB, instead of
duplicating unrelated raw studies and nested archive copies. It retains all Git
source and all internal TEST runs relevant to this audit.

```sh
# Recompute from saved diagnostic evidence, including raw-hash verification:
bash research_ops/temporal_validity_audit/REPRODUCE.sh --saved-only

# Regenerate only figures:
bash research_ops/temporal_validity_audit/REPRODUCE.sh --plots-only

# Actual control execution entrypoint (no provider client):
.venv/bin/python research_ops/temporal_validity_audit/positive_controls.py
```

Set `AUDIT_PYTHON` to an absolute Python executable if using another environment.
The controls intentionally use a 4000 ms admission offset, not the historical
0/2000/8000 ms design. E uses a real collaborator-version race, so its manipulation
must be checked from the observed 409 rather than assumed from its condition ID.

## Artifact map

| Artifact | Meaning |
|---|---|
| `registration.json`, `registration_amendments.json` | Exploratory plan and disclosed changes; not a historical preregistration |
| `integrity_report.json`, `provenance/` | Archive/source/gate checks, inventories, raw input hashes, manifests and logs |
| `executions.csv` | All 1239 terminal internal executions, including 166 invalid; contract authorization and independent outcomes |
| `episode_timing.csv` | All 207 valid P0 stress executions; filter `eligible_prohibited=True` for the 137 |
| `decision_opportunities.csv` | All 3812 raw actor decisions from the 207 P0 stress episodes, including 2463 eligible decisions |
| `browser_actions.csv` | Request/native-call/gateway/operation-ID joins and transaction return bounds |
| `protection_proposals.csv` | Native protective proposals and exact observed dispositions |
| `all_valid_internal/` | Supplementary scan of all 19977 actor responses in all 1073 valid internal executions; seven protective proposals in five episodes (including one malformed P3 proposal) |
| `reviewer_recommendations.csv` | All 264 reviewer JSON recommendations, retaining 39 downstream-invalid episodes and separating the reviewer role from native actor proposals |
| `invalid_executions.csv`, `invalid_protection_proposals.csv` | Reasons for all 166 invalid executions and their raw protective proposals, without assigning missing outcomes |
| `failure_attribution.csv` | No proposal vs late dispatch, without treating absent proposals as rejected proposals |
| `unknown_cases.csv` | Structural measurement gaps and any unresolved joins; absence is distinct from UNKNOWN |
| `matched_pairs.csv` | 132 valid eligible P0/P1 pairs and pending-specific outcomes |
| `positive_controls.json`, `controls/` | All diagnostic attempts and raw browser/network/database/receiver evidence |
| `control_conditions.csv`, `control_timings.csv` | Control manipulation checks and measured enforcement intervals |
| `sensitivity.json`, `stratified_metrics.json`, `uncertainty.csv` | Conservative margins, strata and task-cluster bootstrap summaries |
| `action_sequences.csv`, `clustering.json` | Exploratory edit-distance sequence shapes and source-subsample stability |
| `case_studies/` | Rule-selected actual trajectories, including a safe P1 sibling |
| `figures/` | Eight vector PDFs and 300-dpi PNGs, source tables and provenance |
| `experiment1_revised.tex` | Verified replacement section; original manuscript unchanged |
| `tests/`, `provenance/*tests*` | Audit and repository test results |

CSV booleans are `True`/`False`; blank numerical fields are unavailable. Explicit
`UNKNOWN` classifications mean insufficient measurement, not a negative outcome.
`BEFORE`/`AFTER` ordering fields describe **admission relative to the named event**.
The 1 ms guard band and additional sensitivity margins are assumptions applied to
audit markers, not invented exact database read or commit times. The public
observation-handoff proxy does not reveal when the provider consumed the context.
Ever-proposed protection differs from protection proposed before admission.

The frozen source is an ignored, reproducibly restored dependency under
`provenance/historical/`. Original archives remain outside this audit. All newly
authored code, diagnostic raw evidence, outputs and failure logs are confined here;
only the required continuation entry is added to `docs/PROGRESS.md`.

The full valid-internal scan finds seven protective proposals. Six dispatch and
commit: four after actual admission, two after an already-blocked admission
decision under another policy. One string-encoded P3 suspension proposal is
rejected by syntax, also after admission. None is skipped after another action. This supplement preserves the distinction between actual admission and
a blocked admission decision; it does not replace the 137-episode P0 analysis.
All 132 matched P0/P1 source-cut digests also agree independently.

The invalid-run audit retains 147 finite-job guard failures, 16 closed-page/browser
failures and three HTTP read timeouts. It examines 2,182 actor requests with 2,179
recorded responses and three unknown responses. One P1 suspension receives HTTP
200 in an invalid execution; its complete outcome remains UNKNOWN. These records
are separate from the seven proposals in valid executions and are not silently
excluded from the raw proposal inventory.

The stock `scripts/test.sh` wrapper encountered missing `uv`. The retained log is
`provenance/repository_checks.log`; equivalent compact verification, full-tree
Ruff check/format and pytest passed using `.venv` executables. The audit's
reproduction script uses that environment directly.

Eight additional `--ticket-window` controls are in `ticket_window_controls.json`
and `ticket_window_timing.csv`: suspension returns after admission but before
receipt, and all eight physical effects still occur. Across both diagnostic
suites there are 91 attempts / 88 valid / three invalid. The conservative
response-time subset has 62 client-dispatchable responses; a separate syntactic
count of 63 retains the one response with an invalid first business argument.
