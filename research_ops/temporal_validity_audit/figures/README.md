# Executed audit figures

Every figure is available as vector PDF and 300-dpi PNG. Rebuild with `../REPRODUCE.sh --plots-only` or `python plot.py`. `provenance.json` binds each figure to its source data and plotting-script hashes.

**01_enrollment** — Observed opportunities are retrospective bounds. Branches overlap; proposal counts are not a nested continuation of the execution subset.

**02_admission_response** — All observations retained. Right panel uses a symmetric log x scale to show long trajectories; diagonal is equality in seconds. Left red mark identifies the episode with a later proposal, not a protective first response.

**03_protection_outcomes** — A successful late suspension transaction does not undo an admitted pending effect. No proposal is distinct from a rejected/skipped proposal.

**04_queue_http_intervals** — HTTP interval includes transport and provider serving/queueing; it is not pure neural inference latency. Queueing crosses admission in five episodes.

**05_recorded_trajectories** — Cases selected by explicit rules in enrich.py and supplementary.py, including a safe actually executed P1 sibling. A sibling is not a P0 mid-trajectory counterfactual. Times are audit/response markers, not exact commits.

**06_opportunity_conditioned_rates** — 95% task-cluster percentile bootstrap intervals. Ever-proposed and ever-dispatched protection are distinct from proposals before admission (zero). Degenerate bootstrap intervals do not bound unseen tasks. Margins are sensitivity assumptions, not known historical enforcement delays.

**07_exploratory_sequence_shapes** — Average-linkage normalized Levenshtein clustering, k=2–5 silhouette comparison; task-subsample ARI stability reported in clustering.json. Small clusters and timing/length confounding preclude mechanistic interpretation.

**08_scripted_controls** — Primary A–J: 83 attempts, 80 technically valid trials; three invalid setup-deadline attempts preserved. One E trial did not induce the intended version conflict and remains valid. Controls use real PostgreSQL, browser, HTTP worker and receiver paths.
