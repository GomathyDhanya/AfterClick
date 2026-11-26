# Public release audit and cleanup decisions

Maintainer for this release documentation: **GomathyDhanya**. Existing Git history, historical authorship, original experiments and third-party licenses remain unchanged.

## Inventory and method

Base commit: `2080c4263bce4bebb31fbe7674ac05e1d1924087` on `main`. The GitHub recursive tree contained **2,494 tracked blobs** and was not truncated. See [the complete file-by-file manifest](FILE_CLEANUP_MANIFEST.csv) for each original path, action, Git blob SHA and byte count. `candidate_contracts_v2` through `v7` contain 289 files each; v5 and v6 have identical blob SHA values for all 289 matched relative paths.

## Changes

- Replaced the landing README with conservative current-v12 navigation and accurate experimental status.
- Added a public architecture/benchmark guide, reproduction guide, archive index and explicit evidence publication/checksum instructions.
- Kept existing `paper/v12/` as the **current-paper directory** rather than copying or renaming frozen source paths.
- Removed only `.github/workflows/ci.yml` from this review branch at the owner's request. This disables repository-stored GitHub Actions CI once merged; manual checks remain documented.
- No scientific source, frozen specification, task catalog, preregistration, outcome label, paper figure, old finance ledger or evidence blob was moved, deleted, regenerated, or edited.

## Deliberately deferred

Candidate catalog consolidation, relocation of old papers/generated figures, and any rewriting of absolute evidence paths are **not safe on a tree-only inspection**. Preserving every historical path avoids broken hashes and frozen or executable references. The release manifest is a navigation layer, not a deduplicated evidence tree.

## Verification record

- **Performed:** recursive Git tree inventory; catalog v5/v6 Git SHA comparisons (289/289); inspection of source-only reproduction script, existing acceptance audit, historical reproduction-validation record, release index and raw evidence publication state.
- **Previously recorded only:** 330 passing tests in the base README; historical saved-data reproduction `passed=true`, 180 source/gate hashes checked and zero provider calls. These are not fresh tests of this branch.
- **Not performed in this session:** local before/after regression, downloaded raw-archive checksum verification, full saved-data numeric reproduction, and runtime smoke tests. Connected GitHub read/write tools do not mount a checkout; the raw archive is not published. No paid inference was rerun.

Do not merge based only on this documentation/structural review. Before merging, perform the source-only full suite on both refs and full archive-backed reproduction on an isolated checkout; compare results, exact hashes, assignment counts and frozen paths. Verify there are no unexpected changes beyond the documented workflow deletion and documentation additions.
