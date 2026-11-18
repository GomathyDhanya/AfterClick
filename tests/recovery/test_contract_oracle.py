import ast
from copy import deepcopy
from pathlib import Path

import pytest

from afterclick.contracts.authorization import authorized
from afterclick.contracts.schema import TaskContract, load_contract
from afterclick.evaluation.pilot import CONTRACT_PATHS, EXPECTED, run_case
from afterclick.evaluation.recovery_reference import verify_recovery
from afterclick.evaluation.task_oracle import evaluate_task


@pytest.mark.parametrize("path", CONTRACT_PATHS)
@pytest.mark.parametrize("mode", EXPECTED)
def test_measured_recovery_cases_for_three_families(db, path, mode):
    contract = load_contract(path)
    result = run_case(db, contract, mode)
    assert result["reference_certificate"]["valid"]
    assert result["passed"], result["certificate"]
    certificate = result["certificate"]
    assert certificate["goal_preserved"]
    assert certificate["independent_edits_preserved"]
    assert certificate["first_verified_irreversible_time"] == (200 if mode == "late" else None)
    if mode == "conflict":
        assert result["before"] == result["after"]
    if mode == "false_success":
        assert certificate["residuals"] and not certificate["irreversible_witnesses"]


@pytest.mark.parametrize("path", CONTRACT_PATHS)
def test_oracle_rejects_fabricated_clean_state_and_invalid_reference(db, path):
    contract = load_contract(path)
    result = run_case(db, contract, "late")
    forged = deepcopy(result["reference"])
    certificate = verify_recovery(
        contract,
        result["before"],
        forged,
        result["reference"],
        "selected",
        reference_validated=True,
        requests_quiescent=True,
        horizon_complete=True,
    )
    assert certificate["classification"] == "VERIFIED_UNRECOVERABLE"
    assert any("Immutable" in issue for issue in certificate["preservation_errors"])
    invalid = verify_recovery(
        contract,
        result["before"],
        result["after"],
        result["reference"],
        "selected",
        reference_validated=False,
        requests_quiescent=True,
        horizon_complete=True,
    )
    assert invalid["classification"] == "UNKNOWN"


@pytest.mark.parametrize("path", CONTRACT_PATHS)
def test_false_preservation_and_unsupported_interfaces_never_verified(db, path):
    contract = load_contract(path)
    result = run_case(db, contract, "preservation")
    forged = deepcopy(result["after"])
    forged["tasks"][0]["description"] = "API v2 with human addition lost"
    certificate = verify_recovery(
        contract,
        result["before"],
        forged,
        result["reference"],
        "selected",
        reference_validated=True,
        requests_quiescent=True,
        horizon_complete=True,
    )
    assert certificate["classification"] == "PARTIAL"
    assert not certificate["independent_edits_preserved"]
    limited = contract.model_copy(update={"supported_compensations": ()})
    unknown = verify_recovery(
        limited,
        result["before"],
        result["after"],
        result["reference"],
        "selected",
        reference_validated=True,
        requests_quiescent=True,
        horizon_complete=True,
    )
    assert unknown["classification"] == "UNKNOWN"


def test_contract_goal_and_permissions_do_not_depend_on_task42(db):
    contract = load_contract(CONTRACT_PATHS[1])
    data = contract.model_dump()
    data["goals"][0]["record_id"] = "TASK-43"
    data["authorized_effects"][0]["resource"] = "TASK-43"
    contract = TaskContract.model_validate(data)
    result = run_case(db, contract, "early")
    assert result["passed"] and evaluate_task(contract, result["after"])["success"]
    goal_event = next(e for e in result["after"]["effect_events"] if e["action_id"] == "goal")
    root_event = next(
        e
        for e in result["after"]["effect_events"]
        if e["action_id"] == "selected" and e["kind"] == "task.updated"
    )
    assert authorized(contract, goal_event)
    assert not authorized(contract, root_event)


def test_oracle_modules_cannot_import_planner_model_or_mutation_code():
    for name in ("recovery_reference", "effect_oracle", "task_oracle"):
        tree = ast.parse(Path(f"afterclick/evaluation/{name}.py").read_text())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.ImportFrom):
                modules = [node.module or ""] + [a.name for a in node.names]
            elif isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            assert not any(
                any(word in module for word in ("planner", "conditional", "domain", "learning"))
                for module in modules
            )


def test_incomplete_evidence_or_false_horizon_claim_cannot_be_verified(db):
    contract = load_contract(CONTRACT_PATHS[0])
    case = run_case(db, contract, "censored")
    result = verify_recovery(
        contract,
        case["before"],
        case["after"],
        case["reference"],
        "selected",
        reference_validated=True,
        requests_quiescent=True,
        horizon_complete=True,
    )
    assert result["classification"] == "UNKNOWN"
    missing = deepcopy(case["after"])
    del missing["notification_deliveries"]
    result = verify_recovery(
        contract,
        case["before"],
        missing,
        case["reference"],
        "selected",
        reference_validated=True,
        requests_quiescent=True,
        horizon_complete=True,
    )
    assert result["classification"] == "UNKNOWN"


def test_irreversible_flag_alone_is_not_a_proof(db):
    contract = load_contract(CONTRACT_PATHS[1])
    case = run_case(db, contract, "false_success")
    for state in (case["before"], case["after"]):
        for event in state["effect_events"]:
            if event["action_id"] == "selected":
                event["irreversible"] = True  # deliberately corrupted annotation
    result = verify_recovery(
        contract,
        case["before"],
        case["after"],
        case["reference"],
        "selected",
        reference_validated=True,
        requests_quiescent=True,
        horizon_complete=True,
    )
    assert result["classification"] == "PARTIAL"
    assert not result["irreversible_witnesses"]
