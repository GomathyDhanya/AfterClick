from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from afterclick.research.recoverability import State, strategy, successors


@given(st.booleans(), st.booleans(), st.booleans(), st.text(max_size=20))
def test_all_recovery_paths_preserve_independent_work(owned, pending, principal, note):
    state = State(owned_source=owned, pending=pending, principal=principal, independent_digest=note)
    assert strategy(state) is not None
    for _, after in successors(state):
        assert after.independent_digest == note


def test_external_obligations_are_not_erased_by_local_compensation():
    for field in ["knowledge_observed", "fee_burned", "child_live", "deadline_missed"]:
        state = replace(State(owned_source=True, pending=True), **{field: True})
        assert strategy(state) is None
    live = State(child_live=True)
    assert strategy(live) is None
    assert strategy(replace(live, child_live=False)) == []
    assert strategy(State(owned_source=True, foreign_owner=True)) is None
