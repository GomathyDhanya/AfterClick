from copy import deepcopy
from uuid import uuid4

import pytest

from afterclick.benchmarks.mock_finance import FakeBank, LostAcknowledgment, ReceiptObserver
from afterclick.contracts.schema import load_contract
from afterclick.evaluation.finance_oracle import verify_finance
from afterclick.evaluation.mechanism_pilot import fee_case
from afterclick.infrastructure.db import Database, digest


@pytest.fixture
def bank():
    provider = Database("ac_bank_unit_" + uuid4().hex)
    receiver = Database("ac_receipt_unit_" + uuid4().hex)
    bank = FakeBank(provider, ReceiptObserver(receiver))
    try:
        yield bank
    finally:
        receiver.drop_experiment()
        provider.drop_experiment()


def test_lost_ack_commit_is_idempotent_and_refund_preserves_fee(bank):
    event = dict(
        id=1,
        kind="task.updated",
        action_id="selected",
        resource="TASK-42",
        logical_time=0,
        before={"reviewed": False},
        after={"reviewed": True},
    )
    bank.consume_committed_events({"effect_events": [event]})
    with pytest.raises(LostAcknowledgment):
        bank.capture("selected", 100, drop_ack=True)
    assert bank.snapshot()["fake_bank_clock"][0]["logical_time"] == 100
    assert len(bank.snapshot()["observer_receipts"]) == 1
    assert bank.capture("selected", 100)["status"] == "duplicate_no_new_effect"
    bank.advance(150)
    assert bank.refund_principal("selected")
    state = bank.snapshot()
    balances = {a["name"]: a["units"] for a in state["fake_accounts"]}
    assert balances == dict(wallet=99, merchant=0, fee_burn=1, external=0)
    assert len(state["fake_ledger"]) == len(state["observer_receipts"]) == 2


@pytest.mark.parametrize("mode", ["early", "late_refund", "conflict"])
def test_real_source_and_external_witness_classes(mode):
    contract = load_contract("fixtures/tasks/review-readiness-v2.json")
    case = fee_case(contract, mode)
    assert case["passed"]
    assert case["reference_certificate"]["valid"]
    if mode == "late_refund":
        assert case["source_certificate"]["classification"] == "VERIFIED_RECOVERABLE"
        assert case["certificate"]["classification"] == "VERIFIED_UNRECOVERABLE"
        assert case["certificate"]["compensated"] and case["certificate"]["residual_fee_units"] == 1
        # Even internally consistent forged fee refunds must fail the declared capability check.
        forged = deepcopy(case["sink_after"])
        refund = next(e for e in forged["fake_ledger"] if e["kind"] == "refund")
        refund["postings"] = {"wallet": 11, "merchant": -10, "fee_burn": -1}
        for a in forged["fake_accounts"]:
            a["units"] += 1 if a["name"] == "wallet" else -1 if a["name"] == "fee_burn" else 0
        next(r for r in forged["observer_receipts"] if r["kind"] == "refund")["postings_hash"] = (
            digest(refund["postings"])
        )
        invalid = verify_finance(
            case["sink_before"],
            forged,
            case["reference"]["sink"],
            case["source_before"]["effect_events"],
            case["source_certificate"],
            reference_validated=True,
            horizon_complete=True,
        )
        assert invalid["classification"] == "UNKNOWN"
        assert any("capability" in r for r in invalid["reasons"])


def test_receipt_censoring_is_distinct_from_commit_and_recovery_time():
    case = fee_case(load_contract("fixtures/tasks/review-readiness-v2.json"), "unknown")
    assert case["passed"] and case["certificate"]["classification"] == "UNKNOWN"
    assert case["certificate"]["receipt_time_right_censored"]
    later = case["receipt_followup"]["certificate"]
    assert later["classification"] == "VERIFIED_UNRECOVERABLE"
    assert later["receipt_event_time"] == 100 and later["receipt_arrival_time"] == 400
    assert case["recovery_time"] == 150 and case["receipt_followup"]["observation_time"] == 450
    assert case["receipt_followup"]["primary_label_unchanged"]
