# AfterClick

**Beyond Action-Level Safety in Asynchronous AI Agents**

AfterClick is the implementation and reproducibility artifact for the [current paper](paper/main.tex), with [compiled PDF](paper/AfterClick.pdf). It studies how local task completion, irreversible external-effect history, enforcement timing, and restoration obligations differ in asynchronous agent workflows.

The bounded study reports 65 local-completion/history mismatches among 1,073 valid internal episodes; a 288-branch fixed-recommendation timing experiment (287 valid); 72 engineered PostgreSQL/HTTP admission-boundary probes; 617 reconstructed restoration duties; and 264 historical reviewer responses plus 264 retrospective replays. These findings do **not** complete the original research program: **1,479 of 2,904 registered assignments are terminal; 1,425 remain unexecuted**. Unknown and invalid outcomes are retained. The paper makes no universal controller-superiority or pure neural-latency causal claim.

## Verify and reproduce

```sh
uv sync --frozen --group research
uv run --frozen --group research python -m research_ops.publication.program verify-data
bash scripts/build_paper.sh
bash scripts/test.sh
```

Building the paper requires Tectonic or an equivalent LaTeX environment; the Python plotting dependencies use the existing lock. Plots and numerical tables read checked JSON/CSV evidence directly. Saved-data commands do not initialize an endpoint or call a model. A source-only checkout verifies compact evidence and rebuilds the paper; raw analyses additionally require the separately supplied archives. See [reproduction instructions](docs/REPRODUCIBILITY.md).

## Navigate by research question

| Question | Implementation and evidence |
|---|---|
| RQ1: local completion vs forbidden history | [Normalizer](research_ops/publication/analysis/normalize.py), [analysis](research_ops/publication/analysis/analyze_existing.py), [all 65 case cards](evidence/publication/analysis/cases/) |
| RQ2: enforcement delay and admission boundary | [Controlled analysis](research_ops/scripts/v12_actuator_analysis.py), [independent verifier](research_ops/publication/analysis/verify_actuator.py), [real PostgreSQL/HTTP probe](research_ops/publication/boundary_probe.py) |
| RQ3: restoration debt | [Duty reconstruction](research_ops/publication/analysis/obligation_audit.py), [617 duty records](evidence/publication/obligations/duties.csv) |
| RQ4: reviewer behavior | [Decision analysis](research_ops/publication/analysis/analyze_existing.py), [replay implementation](research_ops/publication/review_replay.py), [completed replay report](evidence/publication/replay/report.json) |
| Supplementary results | [Policy estimator](research_ops/scripts/v12_confirmatory_analysis.py), [external benchmark](research_ops/scripts/v12_external.py), [graph analysis](research_ops/scripts/v12_graphs.py) |

The [evidence index](evidence/index.json) maps each question to scripts, reports and figures. The [claim registry](paper/claim_registry.json) and [claim/evidence matrix](evidence/claim_evidence_matrix.csv) bind claims to source hashes. [Architecture](docs/ARCHITECTURE.md), [threat model](docs/THREAT_MODEL.md), and [data schema](docs/DATA_SCHEMA.md) describe the implementation and its limits.

## Active artifact and immutable history

The active tree contains the V7 contracts (216 TEST, 72 DEV), current benchmark and shared infrastructure, paper analyses, compact evidence, and current scientific tests. Module paths remain stable where moving them would add needless risk. The active package is not the original frozen checkout.

Superseded catalogs, TCOPE/OECR/model-sprint implementations, older papers, full historical tests, negative results, financial ledgers and original source paths remain recoverable at pinned commit `31eab61870befc520841d11f422bb1a372ba92b8`. [Archive restoration](archive/README.md) records that snapshot, checksummed local assets, and the unchanged 180-file integrity procedure. Large raw evidence is preserved separately and has not been publicly uploaded. The archive index contains pointers and audit reports, not another loose copy of the historical tree.

[Data availability](research_ops/publication/DATA_AVAILABILITY.md) and [LICENSE](LICENSE) state the current release and licensing status. The paper is anonymous; the public repository identifies its owner.
