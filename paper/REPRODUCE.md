# Reproducing AfterClick's bounded study

The authoritative paper is `paper/PAPER.md`. This is a local artifact; no deployment, model API,
new paid request or public release is needed for the numerical study. The historical live calls
are preserved evidence, not deterministic outputs promised by a replay. All causal database checks
require real PostgreSQL and use fresh isolated `ac_*` schemas.

## Environment

Use Python 3.11, Node 24, Docker Compose and uv. Original environment: Python 3.11.14;
scientific dependencies are locked in `uv.lock`, including scikit-learn 1.8.0 and matplotlib 3.10.8.
Existing application package versions were retained when adding the research dependency group.

```sh
uv sync --frozen --group research
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
docker compose up -d --wait db
.venv/bin/python -m playwright install chromium
.venv/bin/pytest -q
```

The default database is loopback test PostgreSQL. Never point `DATABASE_URL` at production.
The bounded reproduction runner rejects non-loopback database hosts. Its schema creation does not
restore snapshots into a live world. Ordinary FlowBoard data are not reset.

## Verify preserved evidence and regenerate without collecting data

Unpack the local evidence archive at the repository root so it restores `artifacts/research_runs/`.
Archive SHA-256 is in its adjacent `.sha256` file and the source checkpoint index is in
`evidence/research-20261123/index.json`. This archive is a local handoff, not a public data release.

```sh
.venv/bin/python research_ops/scripts/verify_evidence.py
.venv/bin/python research_ops/scripts/render_research.py --output /tmp/afterclick-review-20261123
```

Choose a fresh output path. Rendering reads saved metrics, final rows and a frozen local model;
it does not fit models, open new holdouts, query PostgreSQL, or call an endpoint. Load joblib models
only from this trusted local package. Six PNG/SVG figures, five CSV/Markdown tables and input hashes
are regenerated. `paper/generated/` contains the delivered copies.

## Bounded local repetition

Inspect the plan first. It performs no experiment without `--execute`:

```sh
.venv/bin/python research_ops/scripts/reproduce_research.py --replica review-20261123 --max-cycles 3 --max-wall-minutes 45 --paid-mode disabled
```

Then run the same command with `--execute`. It executes at most three of six local phases per call:
48-case oracle pilot, 54-case capability pilot, finite closure audit, matched search, model fitting,
and the fixed confirmation protocol. Invoke again with the same replica ID to resume after a
completed phase. State and registry are in `artifacts/reproductions/review-20261123/`.
An interrupted/failed phase is preserved and refused on resume: diagnose it, then use a fresh ID.
No infinite loop, scheduler, paid mode, new claims or endpoint launch exists in this runner.
The complete runner was checked in dry-run mode with guard tests; its six-phase orchestration was
not redundantly executed end to end. Individual scientific phases were executed in the original study.

For repeated results, use:

```sh
.venv/bin/python research_ops/scripts/render_research.py --runs-root artifacts/reproductions/review-20261123 --output /tmp/afterclick-replica-figures
```

These repeats reuse the now-known test law and protocol. They are reproductions, not new independent
confirmation. The original final run is protected by an opening marker and must never be rerun or
used for tuning. A fresh scientific extension requires a new protocol, instances and holdout.

## Evidence map and scope

- `p1c-new-endpoint-live-v1/v2`: original failure and hybrid 12-branch case, redacted model journals.
- `p2-20261123-distinct-mechanisms-v1` + `p2-capability-diversity-v1`: 102 SQL pilot cases.
- `p3-formal-recovery-v1`: reuses those 102 cases; 63 known assertions, 256 abstract states.
- `p4-matched-search-v1`: 14,400 attempted finite queries; ten new SQL endpoint witnesses.
- `p6-risk-study-v1`: 16,384 finite acquisition queries, data/models, original freeze error and repair.
- `p7-visible-collision-v1`: full public-input hashes and two contrary SQL outcomes.
- `p8-gateway-enforcement-v1`: two browser/SQL enforcement tests with a stub risk scorer.
- `p9-locked-confirmation-v1`: 2,048 finite rows, 64 source clusters, 16 new SQL spot cases.
- `p10-synthesis-v1`: saved-data rendering, final 239-test report, billing reconciliation.

Do not add reused audits to independent sample counts. UNKNOWN, CENSORED, CONFLICT, PARTIAL and
replay-invalid have different meanings. The final cohort has explicit synthetic authorization and
no inserted collaborator edits; its preservation field is a structural assumption. The source,
protocol and model hashes, not the earlier dirty-checkout Git HEAD alone, identify executed code.
The local source commit is a later reproducibility checkpoint, not a claim experiments ran from it.
