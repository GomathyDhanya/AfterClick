# Current publication program

- `analysis/`: canonical saved-data normalization, independent verification, statistics, claim matrix, figures and manuscript generation.
- `registration/`: immutable copies of executed registrations/protocols, with exact source hashes and scope.
- `protocols/`: retrospective analysis specification, methodological correction and related-work scope audit.
- `claim_evidence_matrix.csv`: generated support/limitations matrix, including unsupported full-study and human-review claims.
- `program.py`: supported front door for saved-data reproduction, paper generation, tests and a separately labelled database demonstration.
- Root compatibility modules preserve older `python -m research_ops.publication.NAME` invocations; their implementations live in `analysis/`.
- Endpoint, finance and finite cloud lifecycle tools remain separately identifiable. They are optional, require explicit execution, and must not relaunch a completed run.

Use `python -m research_ops.publication.program verify-data` and `python -m research_ops.publication.program generate-paper`. See `docs/PUBLICATION_REPRODUCIBILITY.md` for dependencies and raw restoration. These commands do not create cloud resources.

`PUBLICATION_STATUS.json` is authoritative: the anonymous paper is complete; the original full research matrix and several causal/human validation requirements remain incomplete. Historical source and raw evidence are preserved. `LAYOUT_MIGRATION.json` maps physical moves and compatibility paths.
