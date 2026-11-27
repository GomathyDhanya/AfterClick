# Targeted related-work audit — 26 November 2026

Primary sources were opened on 26 November 2026. This is a targeted scope audit, not a systematic literature review. Paper abstracts and relevant full-text sections were consulted where available. Numeric performance claims from other papers are not adopted as AfterClick results.

| Work and verified primary source | Established overlap | Scope of the current paper |
|---|---|---|
| [UndoBench, arXiv v1](https://arxiv.org/html/2610.05622v1) | Competence versus recovery, paired controls, state and wire-level effect-history oracles, mutation phases and lost acknowledgments | State/history mismatch is not a novel evaluation principle. The 240-condition official subset is separate and uses the released history-aware evaluator. Strategy wrappers are not claimed to reproduce whole published systems. |
| [Cordon, arXiv v1](https://arxiv.org/html/2606.17573v1) | Task-level semantic transactions, staging irreversible effects, lineage, recovery metadata, enforcement boundaries | P5 is a suspension-first queue-hold proxy, not an implementation or comparison against Cordon. The new probes validate legacy admission semantics, not a new transaction abstraction. |
| [Async-RBench, arXiv v1](https://arxiv.org/html/2610.32429v1) | Asynchronous arrivals, response obligations, preservation and reverification, process versus task success | AfterClick does not invent asynchronous obligations; its narrow contribution is the measured effect/admission/restoration audit in this testbed. |
| [When to Intervene? / ReInBench, arXiv v1](https://arxiv.org/html/2610.36471v1) | Error events, self-recovery, prediction and intervention selection | A local-completion endpoint is not labelled self-repair without an observed corrective operation. No competing recovery predictor is evaluated. |
| [Safe to Resume?, arXiv v1](https://arxiv.org/html/2608.29381v1) | Rollback and external-dependency inconsistency; secure continuation | No claim that a local snapshot restores an externally valid execution. No production rollback attacks are reproduced here. |
| [AgentTrust, arXiv v1](https://arxiv.org/html/2605.04785v1) | Runtime tool interception, rules and LLM judgments | Sequential-review results are a policy bundle; no demonstrated improvement over AgentTrust is claimed. |
| [Basin, Juge, Klaedtke, Zalinescu, POST 2012](https://doi.org/10.1007/978-3-642-28641-4_17) | Enforceability distinguishes controllable and observable actions, including timing constraints | Admission/receipt separation is a measured instance of an established enforcement-boundary issue, not a new impossibility theorem. Publisher abstract and author metadata verified; direct author-hosted PDF fetch failed and is not claimed as read. |

The empirical scope is a bounded measurement/reproducibility paper. Claims of a general controller winner, first history-aware oracle, novel concurrency-control theory, model-scale causation, or production security validation are excluded. Independent human workload/policy review remains unperformed.

Model-license provenance: [Qwen3.5-9B pinned LICENSE](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/LICENSE) identifies Apache-2.0. Weights are not redistributed. This does not grant a license to the AfterClick source or research data.
