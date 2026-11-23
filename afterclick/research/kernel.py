"""Executable finite abstraction; thresholds are benchmark parameters, never model inputs."""

from afterclick.research.recoverability import State, strategy

MECHANISMS = ("notification", "mock_payment_fee", "delegated_authority", "deadline_opportunity")


def point(mechanism, recovery_at):
    if mechanism not in MECHANISMS or type(recovery_at) is not int or not 0 <= recovery_at <= 1535:
        raise ValueError("Bounded benchmark query required")
    state = State(
        owned_source=True,
        pending=True,
        knowledge_observed=mechanism == "notification" and recovery_at >= 200,
        fee_burned=mechanism == "mock_payment_fee" and recovery_at >= 100,
        principal=mechanism == "mock_payment_fee" and recovery_at >= 100,
        child_live=mechanism == "delegated_authority" and 100 <= recovery_at < 1100,
        deadline_missed=mechanism == "deadline_opportunity" and recovery_at >= 100,
    )
    witness = strategy(state)
    return dict(
        unrecoverable=witness is None,
        admissible_recovery=witness,
        target="recoverability at prospective query horizon; fixed clock during recovery",
        evidence="finite abstraction, not a new PostgreSQL/live-policy execution",
    )


def frontiers(archive):
    found = []
    for mechanism in MECHANISMS:
        points = archive.get(mechanism, {})
        for at in sorted(points):
            if at + 1 in points and points[at] != points[at + 1]:
                found.append((mechanism, at, at + 1, "loss" if points[at + 1] else "return"))
    return found
