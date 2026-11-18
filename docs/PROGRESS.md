# Implementation progress

Updated November 18, 2026. Current scope: completion-plan sprint **AC-001 through AC-003**.
The historical seven gates and the completion plan's Gates 0–10 use different numbering;
`COMPLETION_GATES.md` is the current map. The original session log is in `history/PROGRESS_V0.md`.

## Completed implementation

- **AC-001:** replay certification now requires all seven pre-action checkpoints, including conflict.
  Negative tests mutate/remove the conflict checkpoint. Its deliberate later collaborator action is
  still allowed to diverge. The original report remains unchanged under `evidence/v0/`.
- **AC-002:** migration 0003 adds non-identifying task field counters and project summary ownership/
  counters. Every touched field advances even for same-value writes. Atomic field CAS allows safe
  nonoverlapping rebases; same-field/ABA changes fail closed. The frontend keeps original tokens,
  retains the unsaved draft on conflict, and never substitutes value equality for history.
- **AC-003:** versioned contracts define goals, authorization, forbidden history, preservation,
  fixtures, horizons and interfaces. Independent task/effect/recovery modules cover review/readiness,
  priority/escalation and status/summary. They accept actual state and a validated reference, not
  planner status. Bounded conditional compensation provides real witnesses for each family.
- Historical irreversible arrival is measured from selected-action logical time. Current recovery
  class is a separate target. A Boolean irreversible annotation alone is insufficient: receipt and
  matching history are required. Missing evidence, unobserved horizons and invalid references fail
  closed; false planner claims cannot certify clean state.
- Added a 24-case planted backend pilot with prefix/placebo validation, raw before/after/reference
  states, independent certificates and retained errors. This is not an adaptive browser benchmark.
- Added a clean-clone Linux validation harness with a separate PostgreSQL container, no host DB
  port, no model credentials, retained logs and isolated resource cleanup. CI now runs the pilot too.
- Archived the supplied completion plan and supporting roadmap; added threat model, novelty matrix,
  draft preregistration and the current gate checklist. Existing architecture is preserved.

## Validation and evidence

The original **39 tests passed again** before modification. The complete current local suite has
**88 passed, 0 failed** (one upstream Starlette/httpx deprecation warning). This includes two-browser
same-value/ABA regressions, concurrent field CAS, legacy migration backfill, all-seven-checkpoint
negative tests, and three-family oracle positives/negatives/preservation/uncertainty tests.

Ruff lint/format checks and the TypeScript/Vite production build passed. The committed seven-branch browser demo and all 24 backend oracle cases passed locally and in a
clean-clone Linux container with a separate PostgreSQL instance. Linux also passed all 88 tests,
frontend build, and Ruff checks. All seven final browser-branch hashes match across environments.

Python dependency audit: no known vulnerabilities reported. npm audit still reports four high
entries through the existing picomatch development-tool advisory; no forced downgrade was used.
Raw audit outputs: `artifacts/sprint-python-audit.json`, `artifacts/sprint-npm-audit.json`.

The v0 prototype and original evidence were committed as `34cc1f0` and tagged `afterclick-v0`.
The v0 report's missing conflict checkpoint is explicitly documented; it is not relabeled as fixed.
Current local test evidence: `artifacts/sprint-tests.log` and `artifacts/sprint-tests.xml`.

## Commands executed / reproducible commands

```sh
.venv/bin/pytest -q --junitxml=artifacts/baseline-tests.xml
.venv/bin/pytest tests/replay tests/integration tests/browser -q
.venv/bin/pytest tests/recovery -q
.venv/bin/pytest -q --junitxml=artifacts/sprint-tests.xml
.venv/bin/ruff check afterclick tests migrations
.venv/bin/ruff format --check afterclick tests migrations
npm run build --prefix apps/flowboard-web
```

Release verification commands (executed successfully from clean revision `dcc4d6b`):

```sh
uv run python -m afterclick.replay.demo --output artifacts/demo
uv run python -m afterclick.evaluation.pilot --output artifacts/oracle-pilot
bash scripts/validate-isolated.sh
```

On this host, uv is available through `.bootstrap/bin/uv` or by prepending `.bootstrap/bin` to PATH.
Container validation uses a separate installed runtime and clean local clone. It is not remote CI
or independent third-party reproduction. Both code and evidence revisions must be recorded honestly.

## Files changed

`afterclick/replay/demo.py`; domain/API/schema; migration 0003; React editor; legacy planner counter
maintenance; new `contracts/` and `evaluation/` modules; `recovery/conditional.py`; three versioned
contracts; replay, field-CAS, browser, migration and oracle tests; isolated validation Docker/Compose
and scripts; CI; research/architecture/reproducibility/continuation documentation. Original v0 oracle
semantics and raw evidence are retained separately.

## Limits and next work

No adaptive LLM, search archive, learned critic/shield, comparative recovery baselines or scientific
improvement is claimed. Three families have planted backend oracle coverage; only the original review
trajectory has browser counterfactual replay. The verifier is bounded witness verification, not an
exhaustive feasibility solver. The serialized scheduler, scripted observer and local application
capability model remain explicit limits. Full image digest pinning and remote CI remain future work.

Next sprint: implement an observable-only configurable LLM policy on the existing Gateway, semantic
branch alignment and explicit feedback interventions, then demonstrate valid fixed/adaptive replay
across the three families and multiple seeds. Preserve invalid trials and usage/cost evidence. Do not
start evolutionary learning before those validity gates. Tinker still needs dataset validation,
current API/model inspection, a costed smoke plan and explicit authorization. No paid model calls
were made; no Tinker credits were spent.

All three current families share the scripted notification receipt as their irreversible mechanism;
this is not evidence of three independently discovered irreversibility mechanisms.


## Final release verification

Implementation revision: `dcc4d6b7561eada3eb6cdef754dd38b860c106f7`. All four run manifests record
that revision with `git_dirty=false`. Their implementation hash matches the current code:
`85f156ab8c37f44a662e61ba7db7ae04b28dfd7eea626b31762a5e769061d4d9`.

| Evidence | Run ID / result |
|---|---|
| Local browser demo | `c2c728655fa64917961f8c3b04f792fb`; seven checkpoint/outcome acceptance checks pass |
| Linux browser demo | `e7fed950e3344ff5b11d18a27874b820`; same final outcome hashes for all seven branches |
| Local oracle pilot | `9c9f0a45f3664ad48a20fac37de63f9e`; 24/24 expected classes |
| Linux oracle pilot | `0a15dec54ad14e8da81cfd778480d775`; 24/24 expected classes |
| Full local suite | 88 passed, 0 failed |
| Full Linux suite | 88 passed, 0 failed |

Raw reports, both JUnit files, the Linux log and dependency audits are versioned in `evidence/sprint1/`.
`manifest.json` hashes those evidence files. Original v0 evidence remains separate and unchanged.
The isolated validation database/containers were stopped and removed; the temporary source clone
was retained for inspection. This is a separate Linux environment on the same Docker host, not
remote CI or a third-party replication.

AC-001, AC-002 and AC-003 pass their bounded sprint acceptance criteria. The code revision above
is the tested implementation; the following documentation/evidence commit does not change it.
The full research project remains incomplete, and no paid training was run.


The normal FlowBoard API/web images were rebuilt and restarted with migration 0003. Read-only
browser/API smoke checks confirmed live updates, non-identifying field tokens, no public research
reset route, and a working artifact explorer. No existing board data was reset during deployment.
