from copy import deepcopy

import pytest

from afterclick import domain
from afterclick.recovery.oracle import verify
from afterclick.recovery.planner import compensate_review


def prepare(db, recovery_time):
    domain.patch_task(db, "TASK-42", {"description": "Document API v2."}, 1, "description", "goal")
    reference = domain.snapshot(db)
    domain.patch_task(db, "TASK-42", {"reviewed": True}, 2, "review", "review")
    domain.advance(db, recovery_time)
    return reference


@pytest.mark.parametrize(
    "time,expected",
    [
        (99, "VERIFIED_RECOVERABLE"),
        (100, "VERIFIED_RECOVERABLE"),
        (199, "VERIFIED_RECOVERABLE"),
        (200, "VERIFIED_UNRECOVERABLE"),
        (250, "VERIFIED_UNRECOVERABLE"),
    ],
)
def test_boundary_around_delivery(db, time, expected):
    reference = prepare(db, time)
    before = domain.snapshot(db)
    assert compensate_review(db, "review")["status"] == "APPLIED"
    domain.advance(db, 300)
    after = domain.snapshot(db)
    certificate = verify(
        before, after, reference, "review", requests_quiescent=True, horizon_complete=True
    )
    assert certificate["classification"] == expected
    assert certificate["goal_preserved"]
    assert certificate["independent_edits_preserved"]
    assert not after["tasks"][0]["reviewed"]
    assert not after["tasks"][1]["ready"]
    assert compensate_review(db, "review")["status"] == "ALREADY_ATTEMPTED"


def test_independent_edit_survives_compensation(db):
    reference = prepare(db, 150)
    domain.patch_task(db, "TASK-42", {"priority": "High"}, 3, "human", "human", "human")
    before = domain.snapshot(db)
    compensate_review(db, "review")
    domain.advance(db, 300)
    after = domain.snapshot(db)
    result = verify(
        before, after, reference, "review", requests_quiescent=True, horizon_complete=True
    )
    assert result["classification"] == "VERIFIED_RECOVERABLE"
    assert after["tasks"][0]["priority"] == "High"


def test_same_value_collaborator_write_is_still_a_conflict(db):
    reference = prepare(db, 150)
    domain.patch_task(db, "TASK-42", {"reviewed": True}, 3, "human", "human", "human")
    before = domain.snapshot(db)
    assert compensate_review(db, "review")["status"] == "CONFLICT"
    after = domain.snapshot(db)
    assert after == before  # no partial cancellation, deletion, or restoration
    assert (
        verify(before, after, reference, "review", requests_quiescent=True, horizon_complete=True)[
            "classification"
        ]
        == "CONFLICT"
    )


def test_oracle_rejects_claim_if_request_or_horizon_unsettled(db):
    reference = prepare(db, 99)
    before = domain.snapshot(db)
    compensate_review(db, "review")
    after = domain.snapshot(db)
    assert (
        verify(before, after, reference, "review", requests_quiescent=False, horizon_complete=True)[
            "classification"
        ]
        == "UNKNOWN"
    )
    assert (
        verify(before, after, reference, "review", requests_quiescent=True, horizon_complete=False)[
            "classification"
        ]
        == "CENSORED"
    )


def test_oracle_detects_illegitimate_snapshot_restore_and_erased_history(db):
    reference = prepare(db, 200)
    domain.patch_task(db, "TASK-42", {"priority": "High"}, 3, "human", "human", "human")
    before = domain.snapshot(db)
    forged = deepcopy(reference)
    result = verify(
        before, forged, reference, "review", requests_quiescent=True, horizon_complete=True
    )
    assert result["classification"] == "VERIFIED_UNRECOVERABLE"
    assert not result["independent_edits_preserved"]
    assert "Historical delivery evidence was removed" in result["residuals"]
