# AfterClick v12 evidence release

Read `RELEASE_INDEX.json` for the measured completion status. **A frozen target is not an executed result.** The complete `FROZEN_MATRIX_RECONCILIATION.csv` retains every registered TEST assignment, including invalid and unexecuted cases. If the index reports missing assignments, the confirmatory research program is incomplete.

## Entry points

- Manuscript source: `paper/v12/AFTERCLICK_V12_MANUSCRIPT.md`; rendered manuscript and appendix: `output/pdf/`.
- Full benchmark: `research_ops/completion_v12/candidate_contracts_v7/` and `TASK_CATALOG.csv`.
- Actual qualification: `artifacts/research_runs/v12-20-qualified-cohort-v7/` (576 safe reference completions).
- Separate oracle implementation/mutations: `artifacts/research_runs/v12-40-independent-verifier-v2/` (10,944 rejections).
- Pre-TEST freeze, exact manifests, model revisions, seeds, limits, source hashes and budget revision: `research_ops/completion_v12/proposed_protocol_v4_final_credit_bound/`.
- Final numerical reports, graph verification, complete trace inventory, forensic ledgers, interval diagnostics and vector timeline atlases: the `evidence_root` in `RELEASE_INDEX.json`.
- Raw TEST jobs: `v12-43-frozen-larger-test-v1`, `v12-44-frozen-primary-test-v1`, and any admitted, explicitly registered finite continuations. See the index for actual roots.
- Original engineering/DEV cohorts, failed reference and serving attempts, regression failures, old oracle labels, and old/new financial ledgers remain in their original locations.

## Saved-data reproduction (no inference or provider calls)

Create a Python 3.11 environment from the repository lock. Run from the extracted repository:

```sh
uv sync --frozen
uv run python research_ops/scripts/reproduce_afterclick_v12.py --root . --output /tmp/afterclick-v12-reproduction-NEW
```

The reader maps archived absolute paths in memory. It does not rewrite a frozen registration or model trace. It re-runs the frozen estimators, independent outcome checker, graph builder and raw-reference verifier, then compares assignment/outcome/interval results. Numeric tolerance is 1e-12; content hashes remain exact. `reproduction-report.json` records what actually passed.

Additional offline figures and trace provenance:

```sh
python research_ops/scripts/render_afterclick_v12.py --analysis PATH_TO_PRIMARY_ANALYSIS/report.json --actuator artifacts/research_runs/v12-37-complex-actuator-analysis-v1/report.json --output paper/v12/figures
python research_ops/scripts/render_afterclick_v12.py --graphs PATH_TO_GRAPHS --output /tmp/afterclick-v12-atlas-NEW
python research_ops/scripts/inventory_afterclick_v12_traces.py --runs ACTUAL_RUN_ROOTS --graphs PATH_TO_GRAPHS --output /tmp/afterclick-v12-traces-NEW
```

For PDF rendering, use the bundled workspace Python (ReportLab) with `research_ops/scripts/render_afterclick_pdf.py SOURCE.md OUTPUT.pdf`. The repository carries the permitted DejaVu fonts and license. Inspect rendered pages; source extraction alone does not verify layout.

## Interpretation rules

Observed edges, actual executed sibling continuations, bounded formal certificates, historical violations and UNKNOWN states are distinct. Exact mid-trajectory reconstruction and exact worker-read/SQL-commit frontiers are not claimed. The separate finite models do not certify the live application graphs. A safe sibling witnesses one realized safe continuation, not a generally deployable recovery policy.

P5 is operationally suspension-first: a pending-service queue-hold proxy for staging. It is not Cordon. Read `PROTOCOL_REPORTING_ERRATA.md` for the frozen vocabulary mismatch, singleton bootstrap limitations and timestamp scope. Invalid and missing cases are never silently removed from registered denominators. Received model generations, known HTTP failures and transport-unknown responses are counted separately.

## Paid execution and financial closure

Saved-data reproduction never calls `finance --execute` or the finite-tail script. Those are live-research entry points and require fresh credits and the independent ledger. A closed job cannot be automatically relaunched. Only never-started assignments can enter a new finite continuation; an unsuccessful or response-uncertain episode is retained, not retried.

All new program compute is guarded against the explicit $18 cap and $0 cash authorization. Conservative guard accounting is not an isolated invoice. Dedicated serving bills GPU wall time, so a response can remain scientifically unknown after its finite financial lifecycle is closed with stopped-producer/idle-container/billing evidence. Any such accounting adjustment is append-only, preserves the original reservation and unknown-response count, and has a before-ledger snapshot and proof. It does not fabricate a model output.

No Tinker fine-tuning was performed. No public publication, push, email or message to another person was performed. Original v11 data and failed/negative results remain preserved. The legacy 60-branch actuator implementation is additionally byte-preserved as `afterclick/completion_v12/enforcement_legacy.py`; the complex actuator implementation has a separate registry and must not be confused with that earlier experiment.
