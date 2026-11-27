# Data and license status

The original release is preserved locally:

- `artifacts/AfterClick_v12_Evidence_Release.tar.gz`
- 637,853,954 bytes; SHA-256 `c031afd3c46eab822770cc41e684d87f2a2aa786b64cff70eb79f90572667020`.
- 151,623 original payload files plus the original release manifest.

The independently auditable local candidate is:

- `artifacts/publication-release/AfterClick_v12_Public_Evidence_Candidate.tar.gz`
- 645,459,203 bytes; SHA-256 `d82178a963b3fe1a4f39d72727c39a5648de8383e8e8bda09b8740779734d509`.
- 263,779 expanded outer/nested members audited; zero credential-pattern findings; zero original payloads changed. Tar metadata and compression differ, and audit metadata is added.
- Full source-to-derived mapping is in its `PUBLIC_DERIVATIVE_MANIFEST.json` and adjacent local `.audit.json`.

The original remains preserved. No public upload, tag, release URL or DOI is represented as completed. The scanning policy is heuristic and does not prove absence of arbitrary sensitive information. Public release requires approval of the concrete asset and a license choice. No new blanket open-source/data license has been applied. Existing third-party licenses/notices remain operative. Model weights are not included.

The local `artifacts/AfterClick_Publication_Companion_20261126.tar.gz` adds new source, model prompt/response traces, failed attempts, boundary evidence, derived data, reproduction logs, figures and manuscript. Its adjacent `.verification.json` and `.sha256` record the actual hash and independent payload read-back. It references the separately supplied original-data candidate. The current repository includes compact copies only. See `docs/PUBLICATION_REPRODUCIBILITY.md`.
