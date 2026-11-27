# Immutable historical research snapshot

The complete prior active tree is preserved by Git commit **31eab61870befc520841d11f422bb1a372ba92b8**, on `codex/afterclick-paper-repo-20261126`. This immutable content identifier preserves all 2,754 original paths: V2–V7 catalogs, original protocols, failed/negative studies, earlier implementations and papers, financial records, and the unchanged historical tests and integrity verifiers. The cleanup branch does not rewrite that history.

`SNAPSHOTS.json` records the frozen protocol hash, original raw archive, audited raw candidate, publication companion and a self-contained local Git bundle. Assets are preserved locally; no new public research release is claimed. `audit/` contains a per-path disposition, dependency edges, dynamic-reference review and validation summary. Archival means removal from the active checkout with exact recovery from this snapshot, never destruction of unique evidence.

## Restore historical source and evidence

From a normal full clone containing the pinned commit:

```sh
python archive/restore.py --output ../AfterClick-history \
  --raw-archive /path/to/AfterClick_v12_Evidence_Release.tar.gz \
  --raw-archive /path/to/AfterClick_Publication_Companion_20261126.tar.gz
```

The audited data candidate may replace the original raw archive. Every supplied archive must match its recorded SHA-256. The procedure exports tracked source/modes directly from Git and extracts only raw `artifacts/` members from evidence archives; raw restoration cannot replace scientific source. It then checks all 180 frozen source/gate hashes without modifying the historical verifier. A source-only restoration reports absent raw gate files explicitly and is not a complete integrity pass.

A shallow clone must first fetch the historical branch:

```sh
git fetch origin codex/afterclick-paper-repo-20261126
```

For offline recovery, verify the Git bundle's hash against `SNAPSHOTS.json`, then use `git clone --branch codex/afterclick-paper-repo-20261126 /path/to/AfterClick_Historical_31eab618.bundle AfterClick-history`. Restore the separately supplied raw archives using the same procedure. Git preserves source history; large raw traces were always separate assets.

## Run unchanged historical analyses and regression

In the restored historical checkout:

```sh
uv sync --frozen --group research
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
uv run --frozen --group research python -m afterclick.oecr.build
uv run --frozen --group research python -m pytest -q --junitxml=artifacts/historical-tests.xml
uv run --frozen --group research python research_ops/scripts/reproduce_afterclick_v12.py \
  --root . --output /tmp/ac-historical-analysis-NEW
```

Use real PostgreSQL on the documented local Compose port and cached/installed Playwright Chromium. Each integration test creates an isolated `ac_*` schema. The original smoke-input fixture under `artifacts/research_runs/p1c-qwen35-9b-smoke-v2/raw/inputs.json` must be restored from raw evidence before running the full historical suite. These commands do not call a model. Completed historical cloud/deployment controllers must not be relaunched as reproduction.

The previously reported independent Linux full run was 395 passes/22 missing-fixture failures, followed by 22 passes after restoring that fixture. That history remains in compact evidence; a later complete local run is a separately identified cleanup validation, not a retroactive change to the Linux run.
