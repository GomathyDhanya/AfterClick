# Current publication threat boundary

The current two-application study uses public browser observations and declared pending-service authorization rules. Evaluator-private contract choices, scheduler details, oracle outputs, debt labels and retrospective graph labels are not model inputs. Effects are real HTTP/SQL-persisted synthetic effects, not real customer messages or production disclosure. The legacy admission/controller transactions share a schema lock; admitted tickets are not recalled by later containment. Historical exact authorization-read/commit instants remain unknown.

The current [manuscript](../paper/current/MANUSCRIPT.md), [schema](DATA_SCHEMA.md), [methodological correction](../research_ops/publication/protocols/METHODOLOGICAL_CORRECTION.md) and [reproduction guide](PUBLICATION_REPRODUCIBILITY.md) define the measured scope and limits. Independent human policy validation and broad production security claims are absent. The earlier bounded threat-model text below is preserved as historical context; its future-tense agent statements do not describe the current publication phase.

## Historical bounded threat model

# Threat model

This controlled application models accidental consequential actions, stale clients, ambiguous
acknowledgements, and scripted collaborator edits. Application permission is distinct from task
authorization. Contracts are independent of the evaluated policy. A malicious database administrator
or research controller is outside the trust boundary.

Public field revision counters are freshness tokens, not identity or access-control credentials.
Each accepted write advances touched counters even for identical values. Conditional patches compare
original tokens and current record version atomically. Legacy requests retain strict record-version
checking. Clients must not discard original preconditions; the shipped editor never does so.

The oracle trusts persisted semantic history and the scripted-observer inbox. Irreversibility needs
both receipt and matching event evidence under the contract's forbidden-history scope. A planner
claim, unsupported action, timeout, or risk flag is not proof. Reset is a research-only fixture
operation; snapshot restoration is never a live recovery primitive.

The deterministic writer remains serialized per world. Three bounded workflows and one selected
root mutation are supported by the new verifier. Arbitrary concurrent histories, external delivery,
human awareness, distributed workers, arbitrary JS snapshots, and public-website staging are not
claimed. UNKNOWN, PARTIAL, CONFLICT, and CENSORED remain distinct.

Full contract files include research-only fixture/seed data. A future LLM must receive an allowlisted
task/authorization summary, never the full contract, hidden schedule, oracle certificate or future
trace. No adaptive model consumes the new evaluator's output today.

Fixture credentials are intentionally public. Normal Docker ports are loopback-only; isolated
validation exposes no database port. This is not a production security certification.
