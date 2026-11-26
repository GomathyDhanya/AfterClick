import copy
import json
from pathlib import Path

import pytest

from afterclick.completion_v12.benchmark.oracle import evaluate as original
from afterclick.completion_v12.oracle_v2 import evaluate
from research_ops.scripts.v12_independent_audit import check


@pytest.mark.parametrize("application", ["flowboard", "opsconsole"])
def test_observed_legal_idempotent_receipt_reconciliation_and_missing_evidence(application):
    fixture = json.loads(
        (
            Path(__file__).parent
            / "fixtures"
            / f"observed-implicit-reconciliation-{application}.json"
        ).read_text()
    )
    contract, snapshot = fixture["contract"], fixture["snapshot"]
    assert original(contract, snapshot)["joint_safe_completion"] is False
    assert evaluate(contract, snapshot)["joint_safe_completion"] is True
    assert not check(contract, snapshot)
    bad = copy.deepcopy(snapshot)
    bad["v12_receipts"] = []
    assert evaluate(contract, bad)["joint_safe_completion"] is not True
    assert check(contract, bad)
    bad = copy.deepcopy(snapshot)
    external = {
        o["id"]
        for o in contract["private"]["initial_private_state"]["operations"]
        if o["kind"] == "external"
    }
    for event in bad["v12_events"]:
        if (
            event["kind"] in {"flow.task_committed", "ops.work_order_committed"}
            and event["payload"].get("operation_id") in external
        ):
            event["payload"]["stage"] = "outcome_uncertain"
    assert evaluate(contract, bad)["joint_safe_completion"] is not True
    assert check(contract, bad)
