# Commit and publish AfterClick

The repository is `https://github.com/GomathyDhanya/AfterClick.git`. The local `origin` points there. This preparation does not create a commit, push a branch, publish a release, or upload data.

## Author identity

Repository-local Git configuration is:

```text
user.name=GomathyDhanya
user.email=gomathydhanya142@gmail.com
user.useConfigOnly=true
```

Both `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT` resolve to that identity. Existing reachable commits also use it; no Codex coauthor trailer was found. Commit attribution is separate from the branch name or the software used to prepare files. No history rewrite is needed.

## What to commit

`docs/GIT_COMMIT_FILES.txt` lists every staged added/modified path, one per line. `docs/GIT_REPOSITORY_FILES.txt` lists the complete resulting tracked tree. The index is prepared for review.

| Include in ordinary Git | Reason |
|---|---|
| `afterclick/`, `apps/`, `migrations/`, `fixtures/`, `configs/`, `docker/`, `scripts/`, `tests/` | Application, agents, benchmark, oracles, infrastructure and verification code |
| Project metadata, dependency locks, Compose files and `.github/` | Install/build/CI reproducibility |
| `docs/`, `README.md`, `AGENTS.md` | Specification, actual progress, architecture and operating instructions |
| `research_ops/` | Research specifications, all contract versions, protocol freezes, analysis scripts, negative results, finance ledgers and history |
| `paper/`, `output/pdf/` | Manuscript, appendix, figures, fonts/licenses and earlier research documents |
| `evidence/` | Original compact evidence plus byte-identical v12 report copies and archive checksum |
| `.gitignore`, `.gitattributes` | Exclude local files; preserve frozen bytes and classify generated media correctly |

Earlier candidate contract sets, failed/deprecated research and historical papers are intentionally retained. They are part of the research record. No original scientific or frozen source is edited to prepare this publication.

The ignore rules exclude `.venv/`, bootstrap tooling, caches, `node_modules/`, build output, browser diagnostics, `.env` and secret/key files, local process state, `tmp/` (including the relocated checkout), the redundant root input ZIP, and `artifacts/`. They do not delete any local data. `.gitattributes` disables line-ending conversion to preserve frozen hashes, marks PDF/media as binary, and preserves generated CSV/SVG/manuscript and third-party license formatting verbatim. The extracted completion-kit documents remain in `research_ops/completion_v12/`.

## Review, commit and push

From the repository root:

```sh
git diff --cached --stat
git diff --cached --name-only
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
git commit --author="GomathyDhanya <gomathydhanya142@gmail.com>" -m "Add AfterClick v12 benchmark, analysis, and research deliverables"
git push -u origin HEAD:main
```

The push command publishes the current commit and its existing history as `main`; it does not use a force push. The target repository was empty when inspected. GitHub write authentication must be supplied by your Git credential setup. The connected GitHub application reported read-only access, so connector access alone cannot perform this push.

## Raw data is a separate release asset

Raw evidence is scientifically relevant. It is excluded from ordinary Git because it includes large generated datasets, model traces and duplicate experiment archives. The full verified archive remains locally at:

```text
artifacts/AfterClick_v12_Evidence_Release.tar.gz
artifacts/AfterClick_v12_Evidence_Release.tar.gz.sha256
artifacts/AfterClick_v12_Evidence_Release.tar.gz.verification.json
```

The archive is 637,853,954 bytes (about 608 MiB), contains 151,623 verified files and has SHA-256:

```text
c031afd3c46eab822770cc41e684d87f2a2aa786b64cff70eb79f90572667020
```

GitHub [blocks ordinary Git files above 100 MiB](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). A [release asset may be under 2 GiB](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases), so this archive can be attached to a release without adopting Git LFS.

After pushing, open the repository's Releases page and create a release, for example tag `v12-evidence-20261125`, titled “AfterClick v12 evidence — incomplete evaluation.” Attach the archive and both sidecars. State that 1,479/2,904 assignments have terminal records and 1,425 remain unexecuted, with additional specification gaps documented. These files have **not yet been uploaded**. After uploading, add the actual release/download link to `evidence/v12/README.md` and update its manifest's publication status.

Verify the downloaded archive in the directory containing its sidecar:

```sh
shasum -a 256 -c AfterClick_v12_Evidence_Release.tar.gz.sha256
```

For full saved-data reproduction, extract into a separate directory so the archived snapshot does not overwrite a newer Git checkout:

```sh
mkdir -p ../AfterClick-evidence
tar -xzf artifacts/AfterClick_v12_Evidence_Release.tar.gz -C ../AfterClick-evidence
cd ../AfterClick-evidence/afterclick-v12
uv sync --frozen --group research
uv run python research_ops/scripts/reproduce_afterclick_v12.py --root . --output /tmp/afterclick-v12-reproduction-NEW
```

Use a fresh output directory. This command makes no model/provider calls. The archive is the pre-publication snapshot; its raw evidence and frozen source hashes are authoritative for reproducing those results. A source-only Git clone lacks the raw evidence until the separate archive is obtained.

## Research status

Publishing these files does not complete the study. Preserve the prominent incomplete status in the README, manuscript, acceptance audit and full assignment matrix. Do not rename unexecuted assignments as completed trials or discard invalid and negative outcomes.
