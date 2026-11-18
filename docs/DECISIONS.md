# Engineering decisions

1. **Single modular Python package, React app, PostgreSQL.** Keep deployment simple and imports
   maintainable. The requested component directory structure is represented by real modules; do not
   create empty ML/evolution services. JSON artifacts stand in for research tables until schema needs
   are validated. No SQLite substitute is used to establish results.
2. **Per-experiment PostgreSQL schemas.** Real branch isolation without repeatedly starting database
   containers. Reset refuses the ordinary app schema. Full snapshots cannot be used to recover a
   live collaborator's work.
3. **Serialized transaction writer with explicit logical event release.** Deterministic and easy to
   audit. Versions still enforce stale-client conflicts. This does not evaluate multiple concurrent
   dispatcher workers or distributed commit races; add those only with dedicated validity tests.
4. **Field ownership plus version checks.** Restore owned fields while preserving independent edits
   elsewhere in a record. A same-value human write is still ownership transfer and blocks recovery.
5. **Read-only oracle in a separate module.** Planner status is never used as its label. The current
   oracle is fixture-specific; generalized oracle validation is required before learning begins.
6. **Scripted observer receipt as the first irreversible effect.** Executable and auditable under an
   explicit capability model; it is not claimed to measure human observation. SSE alone is not
   irreversible under the current contract and cannot silently become a backend write trigger.
7. **Prefix reconstruction with two placebo pairs.** Reject arbitrary browser snapshots as unsafe.
   Browser clocks and backend scheduling are separate. Only committed, quiescent checkpoints are
   supported initially. Excluding random transport receipt identities is explicit, narrow, and tested.
8. **No paid model use.** Evolution, dataset validation, structured critic, and shield follow systems
   validation. Before any Tinker run, inspect current supported API/models, validate data, prepare a
   tiny config and cost estimate, document environment variables, then request user authorization.
9. **Preserve original specifications verbatim.** `RESEARCH_SPEC.md` and `IMPLEMENTATION_BRIEF.md`
   are user-supplied proposals, not implementation-completion claims. Prior-work URLs and proposed
   2026 paper claims have not been independently verified; a literature audit remains necessary.
10. **Local/offline visuals.** No remote fonts or image services are required. The artifact explorer
    reads measured JSON only; there are no fabricated ML charts or archive cells.

## References consulted for implementation

- [Playwright clock controls](https://playwright.dev/python/docs/clock): install before application timers;
  explicitly pause/advance frontend debounce.
- [SQLAlchemy version counters](https://docs.sqlalchemy.org/en/20/orm/versioning.html): version checking
  semantics. This implementation uses explicit Core conditional UPDATE predicates.
- [FastAPI custom responses](https://fastapi.tiangolo.com/advanced/custom-response/): streaming responses
  for SSE transport.

Current locked dev dependencies have an npm audit advisory for picomatch 4.0.7 and transitive
Vite/fdir/tinyglobby exposure (GHSA-fc5q-39xc-vjpf). The registry's latest picomatch during this session
was 4.0.7. Do not blindly downgrade Vite to an old major to silence audit. This affects build/dev
tooling; the production web image serves static assets through nginx. Recheck for a patched release
and validate any upgrade before broader deployment. No production security claim is made.


## Completion sprint decisions

- Field freshness is represented by non-identifying monotone counters, not ownership IDs or value
  equality. The server performs the rebase in one conditional UPDATE; the browser never refreshes
  away its original field preconditions. Existing exact-record-version requests remain supported.
- Keep the v0 oracle and raw evidence intact. New contract oracles are versioned separately and
  validate executed witnesses across three bounded workflows. They are not general feasibility solvers.
- Historical arrival time is the survival target; current recovery class remains nonmonotone.
- The 24-case oracle pilot is explicitly backend-only and planted. It is not LLM data or a search result.
- The dependency audit found no known vulnerabilities in the audited Python dependencies. npm still
  reports four development-tool entries through picomatch; raw audit results are retained locally.
- Clean-clone Linux validation uses an isolated PostgreSQL container and no model credentials. It
  supplements local checks; it does not imply remote CI or independent third-party reproduction.
