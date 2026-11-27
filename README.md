# AfterClick

**Beyond Action-Level Safety in Asynchronous AI Agents**

AfterClick studies how local task completion, irreversible external-effect history, enforcement timing, and restoration obligations differ in asynchronous agent workflows.



## Verify and reproduce

```sh
uv sync --frozen --group research
uv run --frozen --group research python -m research_ops.publication.program verify-data
bash scripts/build_paper.sh
bash scripts/test.sh
```


## Navigate by research question

| Question | Implementation and evidence |
|---|---|
| RQ1: local completion vs forbidden history | [Normalizer](research_ops/publication/analysis/normalize.py), [analysis](research_ops/publication/analysis/analyze_existing.py), [all 65 case cards](evidence/publication/analysis/cases/) |
| RQ2: enforcement delay and admission boundary | [Controlled analysis](research_ops/scripts/v12_actuator_analysis.py), [independent verifier](research_ops/publication/analysis/verify_actuator.py), [real PostgreSQL/HTTP probe](research_ops/publication/boundary_probe.py) |
| RQ3: restoration debt | [Duty reconstruction](research_ops/publication/analysis/obligation_audit.py), [617 duty records](evidence/publication/obligations/duties.csv) |
| RQ4: reviewer behavior | [Decision analysis](research_ops/publication/analysis/analyze_existing.py), [replay implementation](research_ops/publication/review_replay.py), [completed replay report](evidence/publication/replay/report.json) |
| Supplementary results | [Policy estimator](research_ops/scripts/v12_confirmatory_analysis.py), [external benchmark](research_ops/scripts/v12_external.py), [graph analysis](research_ops/scripts/v12_graphs.py) |

The [evidence index](evidence/index.json) maps each question to scripts, reports and figures. The [claim registry](paper/claim_registry.json) and [claim/evidence matrix](evidence/claim_evidence_matrix.csv) bind claims to source hashes. [Architecture](docs/ARCHITECTURE.md), [threat model](docs/THREAT_MODEL.md), and [data schema](docs/DATA_SCHEMA.md) describe the implementation and its limits.

