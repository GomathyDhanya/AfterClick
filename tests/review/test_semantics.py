from afterclick.research.recoverability import State, strategy
from afterclick.review.semantics import Evidence, score


def result(state, history=False, local=True, independent=True):
    return score(Evidence(state, local, history, True, independent))


def test_expired_authority_does_not_erase_issuance():
    r = result(State(child_live=False))
    assert r["current_state_recoverable"] is True
    assert r["full_history_contract_recoverable"] is False
    assert r["safe_task_complete"] is False


def test_expired_authority_does_not_erase_external_access():
    r = result(State(child_live=False), history=False)
    assert r["local_rollback_success"] is True
    assert r["current_state_recoverable"] is True
    assert r["full_history_contract_recoverable"] is False


def test_refunded_principal_keeps_nonrefundable_fee():
    r = result(State(principal=False, fee_burned=True))
    assert r["current_state_recoverable"] is False
    assert r["local_rollback_success"] is True


def test_reverted_values_keep_delivered_notification():
    r = result(State(knowledge_observed=True))
    assert r["local_rollback_success"] is True
    assert r["current_state_recoverable"] is False


def test_independent_edit_is_not_an_admissible_overwrite():
    s = State(owned_source=True, foreign_owner=True)
    assert strategy(s) is None
    assert result(s, history=True, local=False)["full_history_contract_recoverable"] is False
    assert result(State(), history=True, independent=False)["safe_task_complete"] is False


def test_failed_procedure_has_alternative_solution():
    s = State(owned_source=True, pending=True, principal=True)
    r = result(s, history=True, local=False)
    assert r["current_state_recoverable"] is True
    assert r["local_rollback_success"] is False
    assert set(r["admissible_witness"]) == {
        "compensate_source",
        "cancel_pending",
        "refund_principal",
    }


def test_unknown_history_and_prevention_are_not_inferred():
    r = result(State(), history=None)
    assert r["current_state_recoverable"] is True
    assert r["full_history_contract_recoverable"] is None
    assert r["prevention_feasible"] is None
    r = score(Evidence(State(), True, False, True, True, epistemic="UNKNOWN"))
    assert r["current_state_recoverable"] is None
    assert r["safe_task_complete"] is None


def test_recovery_feasibility_does_not_mean_actual_safe_completion():
    r = result(State(owned_source=True), history=True, local=False)
    assert r["current_state_recoverable"] is True
    assert r["full_history_contract_recoverable"] is True
    assert r["legitimate_task_complete"] is True  # Description-goal witness alone.
    assert r["current_contract_satisfied"] is False
    assert r["safe_task_complete"] is False
