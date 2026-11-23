"""Finite admissible-strategy closure at a fixed clock, independent of recovery planner."""

from collections import deque
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class State:
    owned_source: bool = False
    pending: bool = False
    principal: bool = False
    knowledge_observed: bool = False
    fee_burned: bool = False
    child_live: bool = False
    deadline_missed: bool = False
    foreign_owner: bool = False
    independent_digest: str = "preserved"

    def acceptable(self):
        return not any(
            (
                self.owned_source,
                self.pending,
                self.principal,
                self.knowledge_observed,
                self.fee_burned,
                self.child_live,
                self.deadline_missed,
            )
        )


def successors(state):
    if not state.foreign_owner:
        if state.owned_source:
            yield "compensate_source", replace(state, owned_source=False)
        if state.pending:
            yield "cancel_pending", replace(state, pending=False)
    if state.principal:
        yield "refund_principal", replace(state, principal=False)


def strategy(initial):
    """Return an admissible witness, or None after exhausting the complete bounded closure."""
    queue = deque([(initial, ())])
    seen = {initial}
    while queue:
        state, actions = queue.popleft()
        if state.acceptable():
            return list(actions)
        for action, next_state in successors(state):
            assert next_state.independent_digest == initial.independent_digest
            if next_state not in seen:
                seen.add(next_state)
                queue.append((next_state, (*actions, action)))
    return None
