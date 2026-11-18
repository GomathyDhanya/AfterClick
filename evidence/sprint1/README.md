# Sprint 1 validation evidence

Implementation revision: `dcc4d6b7561eada3eb6cdef754dd38b860c106f7`.
The manifests in all four reports record that revision with a clean working tree. This archive was
committed afterward; it does not pretend to have been present in the implementation revision.

- Local macOS: 88 tests, seven browser branches, 24 planted oracle cases passed.
- Clean-clone Linux container: the same suite/demo/pilot passed against a separate PostgreSQL instance.
- All seven final browser outcome hashes match between environments. Source hashes also match.
- `manifest.json` contains SHA-256 hashes for the raw reports, JUnit results, log, and dependency audits.

The oracle pilot uses actual PostgreSQL executions but is backend-only. Its cases are planted,
including explicitly injected false planner claims; they are not search discoveries or LLM results.
The Docker environment is isolated on the same host, not an independent remote replication. No model
credentials were mounted and no paid inference/training was invoked. Original v0 evidence remains
in the sibling directory and is not relabeled as corrected evidence.
