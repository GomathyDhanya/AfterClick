# Threat model and interpretation limits

An imperfect actor performs a legitimate task in an application with asynchronous workers and concurrent state changes. A reviewer may be overrestrictive or misinterpret operation-specific authority. A task contract defines the goal, authorized effect scope, preservation constraints and legitimate service obligations. Ordinary application permission is not equivalent to user authorization for a particular effect.

The testbed uses trusted synthetic public authority and private evaluator contracts. Signed-authority fields are fixture assertions, not a deployed cryptographic authentication protocol. Browser provenance headers are not production authentication. The public model interface excludes private evaluator labels and hidden schedules. Receiver effects are synthetic, independently persisted HTTP effects; the study involves no real customers, personal data, production secrets, charges or uncontrolled third-party commitments.

The evaluated outcomes distinguish local completion `L`, legitimate completion `G`, forbidden effect history `F`, and joint safe completion `Y = G * (1-F)`. `L` and `G` have distinct definitions even though they agree on the observed valid internal episodes. Invalid and unexecuted assignments are unknown. A later local repair cannot erase a persisted forbidden effect under the modeled immutable-history contract. A different compensation contract could change that conclusion.

Containment can prevent admission and create service-reopening or approved-resubmission obligations. Reopening or requeueing does not prove approved delivery. Available observations do not establish safe recoverability for most intermediate prefixes; unknown means insufficient evidence, not proven impossibility. There are no formal certificates for complex LLM graph prefixes.

The study does not cover malicious database administrators, compromised receivers, arbitrary prompt injection, arbitrary network adversaries, production access control, or all distributed-worker failures. Policy contrasts are intervention bundles. Historical response intervals include transport, serving and queueing; they are not pure inference latency. Mechanism probes reuse opened constructed DEV sources. Original enrollment remains incomplete and independent human authority/oracle review is absent.

Raw-data credential scanning is heuristic, not a universal privacy guarantee. Public release and a new data/software license remain separate owner decisions; see the root license-status notice and data availability statement.
