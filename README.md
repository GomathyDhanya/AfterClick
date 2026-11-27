# AfterClick

AfterClick measures local task completion, irreversible external-effect history, enforcement timing, and legitimate restoration in asynchronous agent workflows.

The current deliverable is an **anonymous bounded empirical paper**, supported by all-case evidence audits, a controlled actuator study, 72 new PostgreSQL/HTTP mechanism probes, and 264 new retrospective 9B reviewer-prompt replays. These new probes and replays do not complete the original frozen evaluation: **1,479 of 2,904 assignments have terminal records; 1,425 remain unexecuted**.

- [Current manuscript](paper/current/MANUSCRIPT.md) · [PDF](output/pdf/AFTERCLICK_CURRENT_MANUSCRIPT.pdf)
- [Experimental appendix](paper/current/APPENDIX.md) · [PDF](output/pdf/AFTERCLICK_CURRENT_APPENDIX.pdf)
- [Evidence and limitations](evidence/publication/README.md) · [Claim registry](paper/current/CLAIM_REGISTRY.json)
- [Reproduction guide](docs/PUBLICATION_REPRODUCIBILITY.md) · [Exact publication status](research_ops/publication/PUBLICATION_STATUS.json)

Install the existing locked environment and verify the compact evidence:

```sh
uv sync --frozen --group research
uv run --frozen --group research python -m research_ops.publication.program verify-data
uv run --frozen --group research --with reportlab==4.4.9 python -m research_ops.publication.program generate-paper
```

The saved-data commands do not invoke a model or create cloud resources. Full analyses require the separately supplied raw archive; a source-only clone can build the paper from compact reports. See the [data availability and license status](research_ops/publication/DATA_AVAILABILITY.md). No public raw-data upload or DOI is claimed.

The new source audit corrects a prior interpretation: legacy admission and protection already share a schema-level database lock. The observed late effects involve tickets admitted before containment, rather than evidence of an unlocked database race. Missing information/restoration causal controls, exact mid-trajectory counterfactuals, independent human review, and low clean competence remain explicit limitations.

Runtime code remains under `afterclick/`; the two applications use real PostgreSQL schemas and synthetic HTTP receivers. [Architecture](docs/ARCHITECTURE.md), [original research specification](docs/RESEARCH_SPEC.md), [current progress](docs/PROGRESS.md), and [Git publishing guide](docs/GITHUB_PUBLISHING.md) retain their history. The [previous landing page](research_ops/history/README_20261125.md), [v12 paper](paper/v12/AFTERCLICK_V12_MANUSCRIPT.md), prior frozen studies, failed trials, original data, and financial records are preserved.

## Repository organization

`afterclick/`, `apps/`, `migrations/`, `fixtures/`, `tests/` and `scripts/` retain the runtime and test interfaces. Current scientific code is in `research_ops/publication/analysis/`, immutable run registrations in `registration/`, and scientific scope documents in `protocols/`. The generated `claim_evidence_matrix.csv` connects claims, evidence hashes and explicit gaps. `evidence/README.md` indexes datasets; `paper/current/` is authoritative, while `paper/history/` indexes preserved versions and pinned legacy paths. See `research_ops/publication/LAYOUT_MIGRATION.json` for the actual moves and compatibility wrappers.

`LICENSE` records the existing no-new-license-grant status; an open-source/data license has not been chosen on the owner's behalf.
