# Evidence index

The current anonymous paper uses [`publication/`](publication/README.md) and the unchanged historical compact reports in [`v12/`](v12/README.md). `publication/MANIFEST.json` binds every compact copy to its raw artifact path and SHA-256. The [claim/evidence matrix](../research_ops/publication/claim_evidence_matrix.csv) records supported claims and explicitly unsupported completion/human-review claims.

Older `v0/`, `sprint1/`, `research-20261123/`, and `observability-20261123/` directories retain their own study semantics. They are not pooled as independent tasks in the current analysis.

Large raw data, request/response traces, invalid and failed trials, and full derived tables remain in the separately supplied local archives under ignored `artifacts/`. The publication companion supplements the original-data candidate; it does not silently replace the old missing assignments. No public upload or DOI has been performed.

See [data availability](../research_ops/publication/DATA_AVAILABILITY.md), [schema](../docs/DATA_SCHEMA.md), and [reproduction](../docs/PUBLICATION_REPRODUCIBILITY.md). A source-only clone can build the paper from compact reports; full raw verification requires the separately restored archive. Default supported commands make no model/provider calls.
