# AfterClick

**Research code and preserved evidence for task restoration under progressing asynchronous effects.**

**v12 status: incomplete.** Of 2,904 preregistered TEST assignments, 1,479 have terminal records and 1,425 remain unexecuted; see the [acceptance audit](research_ops/completion_v12/final_package/FINAL_ACCEPTANCE_AUDIT.json). A terminal record is not necessarily a valid trial. The reported performance does not establish a generally superior or novel controller. No paid inference is needed to inspect this release.

## Start here

- [Current manuscript](paper/v12/AFTERCLICK_V12_MANUSCRIPT.md) · [appendix](paper/v12/AFTERCLICK_V12_APPENDIX.md) · [methods](paper/v12/METHODS.md)
- [Architecture and benchmark](docs/PUBLIC_ARCHITECTURE_AND_BENCHMARK.md)
- [Exact reproduction and limitations](docs/PUBLIC_REPRODUCTION.md)
- [Archive and historical research index](docs/ARCHIVE_INDEX.md)
- [Evidence release and SHA-256](docs/EVIDENCE_RELEASE.md)
- [File-by-file cleanup record](docs/FILE_CLEANUP_MANIFEST.csv) · [audit decisions](docs/PUBLIC_RELEASE_AUDIT.md)

## What was actually built

Two different application worlds (FlowBoard and OpsConsole), with PostgreSQL, Chromium, progressing asynchronous workers and HTTP-effect receivers, form the v12 evaluation. The contracts cover 72 DEV and 216 TEST tasks across six families and three complexity levels. Separately implemented software oracles verify business obligations and forbidden histories. The frozen, credit-capped TEST matrix is only partially executed; failures, invalid trials, censoring, uncertainty and missing assignments remain explicit.

The source checkout includes compact checked evidence, frozen protocols and reproducibility code **but not the complete raw evidence archive**. The full archive is not uploaded. Do not claim that cloning this repository alone reproduces all measured results. See [evidence release](docs/EVIDENCE_RELEASE.md).

## Local checks (no paid inference)

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), Node 24 and Docker/PostgreSQL for integration tests:

```sh
uv sync --frozen --group research
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
bash scripts/check.sh
```

Run `docker compose up -d --wait db` before database-backed tests and install Chromium using `uv run playwright install chromium` if needed. See the [reproduction guide](docs/PUBLIC_REPRODUCTION.md) for exact source-only and raw-data requirements. These commands are **instructions**, not claims of freshly executed regression tests for this documentation-only branch.

## Preservation rules

Do not rewrite frozen manifests, task outcomes, source hashes, research finances or historical papers. The v5 and v6 candidate catalogs each contain 289 files with pairwise identical Git blob hashes, but both paths remain because catalog identities can be provenance-bearing. Existing historical authorship and original trial evidence are retained. New release/navigation documentation is maintained under **GomathyDhanya**.
