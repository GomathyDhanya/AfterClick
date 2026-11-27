# Reproducibility

## Locked active environment

```sh
uv sync --frozen --group research
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
uv run --frozen --group research playwright install chromium
docker compose up -d --wait db
```

The existing `uv.lock` and npm lock remain authoritative. PostgreSQL is `postgres:17.7`, bound to loopback port 55432 with synthetic local credentials from Compose. Integration work uses isolated `ac_*` schemas; do not reset the user's database volume. On Linux use Playwright's `--with-deps` option. The current frontend and two runtime HTML assets must be available.

## Compact verification, figures, tables and paper

```sh
uv run --frozen --group research python -m research_ops.publication.program verify-data
bash scripts/build_paper.sh
bash scripts/test.sh
```

`evidence/index.json` hashes the current compact evidence and maps RQ1–RQ4 and supplements to their analyses, registrations and results. The claim registry validates source hashes and JSON pointers; the claim/evidence CSV uses the same sources. Both original compact manifests remain unchanged. Verification of compact files does not verify unavailable raw files.

`paper/figures.py` reads verified JSON/CSV reports for all eight principal plots; `paper/tables.py` generates ten numerical LaTeX tables and claim mappings from the same evidence. No transcribed experimental arrays are used. Architecture coordinates, labels and display ordering are presentation constants. `paper/main.tex` is the single current manuscript, including its appendix; `paper/AfterClick.pdf` is its compiled output. The supplied 17-page paper/source and older papers remain preserved in archival assets.

Install Tectonic for `scripts/build_paper.sh`, or set `TECTONIC` to its executable path. The TeX engine may download ordinary typesetting packages; it creates no model endpoint or paid workload. Python plotting dependencies use the existing research lock. Build logs are under ignored `artifacts/paper-build/`. The current paper is based on compact reports; rebuilding plots is distinct from raw-data reanalysis.

## Raw-data analysis and exact frozen reproduction

The raw archives are local separately supplied research assets, not publicly downloadable files. Restore them with the exact source procedure in [archive/README.md](../archive/README.md). With that historical source and data available:

```sh
uv run --frozen --group research python -m research_ops.publication.program reproduce-existing \
  --historical-root ../AfterClick-history --output /tmp/ac-frozen-NEW
uv run --frozen --group research python -m research_ops.publication.program analyze \
  --raw-root ../AfterClick-history --output /tmp/ac-current-analysis-NEW
```

The first command runs the unchanged historical 180-file integrity checks and frozen statistics/oracle/graph programs in the restored source. The second uses current read-only publication adapters against the restored evidence and regenerates normalization, independent pointer verification, all-case analysis, restoration duties and actuator verification. Use fresh output directories; failure and invalid records must remain. The `rq1`, `rq2`, `rq3` and `rq4` entrypoints share that normalized population to preserve denominators. Supplementary estimator/external/graph locations are indexed in `evidence/index.json`.

## Local mechanism demonstration

```sh
bash scripts/demo.sh /tmp/ac-two-app-demo-NEW
```

This runs 12 engineered DEV probes across FlowBoard and OpsConsole, three orders and two commands using real PostgreSQL and synthetic HTTP receivers. It checks protection/admission/receipt behavior, not agent competence, new TEST results, or population deadlines. Model and provider calls are zero. These probes wrap supported transaction methods and never use snapshot replacement as live recovery.

## Active and historical tests

Active tests cover the surviving applications, scheduler, browser acknowledgment/SSE protocol, V7 benchmark controls, outcome oracles, scientific estimators, archive integrity and evidence/presentation loading. Tests tied exclusively to archived implementations are preserved with those implementations in the historical snapshot; they were not weakened to obtain an active pass. Run the historical suite with all original fixtures and OECR build prerequisites as documented in `archive/README.md`.

The historical independent Linux record remains 395/22 followed by 22 passing fixture rechecks, across 417 distinct tests; it is not rewritten as a single clean full run. Cleanup validation records its own fresh-source tests separately in `archive/audit/VALIDATION.json`. No model-provider calls or new paid cloud activity are part of these procedures. Optional paid replay/external runners are explicit execution tools and are never invoked by saved-data or test commands.
