# Next action — independent local reproduction only

The bounded research loop is closed. No further live experiment is justified or queued. Preferred check: run `.venv/bin/python -m research_ops.scripts.reproduce_oecr --output /tmp/afterclick-oecr-resume-01` from the repository, using a never-existing output path. Prediction: all frozen seals and both saved summaries/four figures match exactly; a mismatch falsifies reproducibility and must be investigated without rewriting the sealed evidence. Resources: local CPU/files only, $0 Modal, no model calls or holdout access. Gate: ordinary local work authorized.

Fallback if artifacts/dependencies are unavailable: restore the local OECR evidence package and follow docs/OECR_REPRODUCIBILITY.md; do not regenerate paid data. Full regression command: `.venv/bin/python -m pytest -q` with local PostgreSQL/Chromium available.

Future broader research would need an independent multi-application cohort, controlled identifier streams and repeated serving samples. This is a limitation and reversal criterion, not an automatic next experiment or authorization. The trajectories spending category is closed after the documented overrun.
