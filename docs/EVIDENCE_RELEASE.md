# Evidence release manifest and download instructions

**Publication status: raw evidence archive not uploaded.** No public raw-evidence download URL is currently verified. The Git checkout contains only compact preserved reports and their [SHA-256 manifest](../evidence/v12/MANIFEST.json).

| Artifact | Recorded value |
|---|---|
| Archive | `AfterClick_v12_Evidence_Release.tar.gz` |
| Size | 637,853,954 bytes |
| Files | 151,623 |
| SHA-256 | `c031afd3c46eab822770cc41e684d87f2a2aa786b64cff70eb79f90572667020` |
| Source of record | [Publishing instructions](GITHUB_PUBLISHING.md) and [v12 evidence README](../evidence/v12/README.md) |

The archive remains outside Git and retains complete trials, negative and invalid cases, model trace bodies, snapshots and graph nodes. Once the repository owner attaches the exact bytes plus `.sha256` and verification sidecars to a GitHub release, add **the actual verified link** here; do not invent one.

Download the archive and sidecar from that future owner-provided release, run `shasum -a 256 -c AfterClick_v12_Evidence_Release.tar.gz.sha256`, extract to a fresh directory, and follow the [offline reproduction guide](PUBLIC_REPRODUCTION.md). The owner must validate the release asset checksum after upload. Do not silently reconstruct or replace uncollected data.
