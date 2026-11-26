# Reproduce AfterClick without paid inference

## Source-only validation

At repository root, install Python 3.11+, uv, Node 24, PostgreSQL and Chromium. Use a throwaway local database, not production. The project retains `uv.lock` and the Node lockfile.

```sh
docker compose up -d --wait db
uv sync --frozen --group research
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
uv run playwright install chromium
bash scripts/check.sh
```

These commands need an appropriately configured local Docker environment. Do not initiate a paid endpoint, cloud worker, or `finance --execute`. No automated GitHub workflow is configured by this branch.

## Full saved-data reproduction (archive required)

**A Git checkout is insufficient.** The 637,853,954-byte `AfterClick_v12_Evidence_Release.tar.gz` archive (151,623 files) is not yet available for download from the repository. SHA-256: `c031afd3c46eab822770cc41e684d87f2a2aa786b64cff70eb79f90572667020`.

When the owner publishes the exact archive and its sidecar, first verify it with `shasum -a 256 -c AfterClick_v12_Evidence_Release.tar.gz.sha256`, then extract **to a separate directory**. From the restored `afterclick-v12` root:

```sh
uv sync --frozen --group research
uv run python research_ops/scripts/reproduce_afterclick_v12.py --root . --output /tmp/afterclick-v12-reproduction-NEW
```

Choose a fresh non-existing output directory. The reader maps archived absolute paths *in memory*, checks frozen source/gate hashes, recomputes registered numerical and oracle results, and verifies graphs; it does not rewrite raw data or call a model/provider. It uses numeric tolerance 1e-12 for the recorded comparisons. See the original [release guide](../research_ops/completion_v12/final_package/README.md) and [historical saved-data validation record](../research_ops/completion_v12/final_package/REPRODUCTION_VALIDATION.json).

## Verification honesty

The recorded previous relocated reproduction passed and checked 180 source/gate hashes, but that is **historical evidence**. No fresh pre/post local regression or full saved-data reproduction has been performed as part of this repository-navigation change, since the connector does not provide a local checkout or the raw archive. Run and record both before merging any structural relocation of frozen data. Never substitute compact report copies for raw trial archives.
