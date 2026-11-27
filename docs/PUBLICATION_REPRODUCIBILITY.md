# Current manuscript reproduction

Use `paper/current/` for the current anonymous paper. Earlier papers and frozen studies remain evidence/history. The full original research matrix remains incomplete.

## Compact verification and paper generation

From the repository root:

```sh
uv sync --frozen --group research
uv run --frozen --group research python -m research_ops.publication.program verify-data
uv run --frozen --group research --with reportlab==4.4.9 python -m research_ops.publication.program generate-paper
uv run --frozen --group research python -m research_ops.publication.program test
```

Paper generation uses only compact saved reports and makes no model/provider calls. ReportLab is an additional rendering dependency; the existing scientific lock is preserved. The exact local rendering version and Python are recorded in the PDF QA report. Figures are available as SVG, PDF and PNG. Generated numeric claims link to source files and hashes in `paper/current/CLAIM_REGISTRY.json`.

## Full raw verification and fresh-path restoration

The source repository does not contain the large raw archive. Locally supplied candidates are listed in `research_ops/publication/DATA_AVAILABILITY.md`; no public download URL is invented. To verify without extracting:

```sh
python -m research_ops.publication.program verify-data --archive PATH_TO_EVIDENCE.tar.gz
```

To restore into a new directory, never over an existing tree:

```sh
python -m research_ops.publication.program verify-data --archive PATH_TO_EVIDENCE.tar.gz --restore-to /tmp/ac-restored-new
```

The restored baseline tree is `/tmp/ac-restored-new/afterclick-v12`. The original archive predates the publication analysis code. Use the new source checkout with its `artifacts/` populated from the restored baseline, or apply the publication companion's verified overlay into a fresh restored tree. Do not rewrite old registrations, trace inventories, frozen source, or raw files. The new reader maps archived absolute paths in memory and still checks their original hashes.

```sh
python -m research_ops.publication.program reproduce-existing --output /tmp/ac-existing-new
python -m research_ops.publication.program analyze --output /tmp/ac-analysis-new
```

The first command regenerates original outcome statistics, independent oracle checks and evidence graphs; all 180 frozen source/gate hashes must match. The second builds the full normalized tables, independent pointer verification, RQ statistics, duty DAG/exposure analysis and actuator receipt/restoration checks. All destinations must be new directories. Failures remain visible and unknown outcomes are not imputed.

## Live database demonstration

```sh
docker compose up -d --wait db
uv run --frozen playwright install chromium
python -m research_ops.publication.program demo --output /tmp/ac-boundary-new
```

The demonstration uses real isolated PostgreSQL schemas and HTTP receivers. It executes 12 engineered schedule probes on reused DEV sources, not a fresh model study. It saves evidence before dropping its own schemas. No snapshot is used as live repair.

## Full regression prerequisites

The original evidence archive supplements a complete source checkout; it omits `fixtures/` and generated OECR frontend assets. Before the full historical suite, use the complete source tree and build both clients:

```sh
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
python -m afterclick.oecr.build
python -m pytest -q
```

Use Node 22.12.0 or a compatible version required by the locked Vite package. The independent corrected Linux image records its exact runtime and build. The source Git snapshot, original data archive and publication overlay are distinct inputs; the archive-only 78-failure result remains recorded.

## Paid work is separate

No supported command above creates an endpoint, runs inference, or creates a cloud resource. The separately recorded readiness, retrospective replay and independent Linux lifecycle require explicit `--execute` entrypoints, finite registrations and a workspace-specific credit ledger. Do not relaunch a completed run directory. Original $18 finances are preserved; the new account's total authorization is $28 and net cash spend authorization is $0.

Independent Linux machine execution is automated by the same research process. The evidence reports distinguish initial failures, reader-only correction, numerical agreement, full regression outcomes, and later diagnostic checks. No independent human review or independent researcher operation is claimed.
