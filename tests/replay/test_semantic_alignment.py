from copy import deepcopy

import pytest

from afterclick.replay.branch_compare import CONDITIONS, certify
from afterclick.replay.semantic_alignment import align


def test_alignment_ignores_action_and_generated_record_ids_but_retains_multiplicity():
    events = [
        {
            "id": 1,
            "kind": "task.updated",
            "action_id": "a1",
            "resource": "TASK-42",
            "parents": [],
            "before": {"reviewed": False},
            "after": {"reviewed": True},
        },
        {
            "id": 2,
            "kind": "notification.created",
            "action_id": "a1",
            "resource": "notice:a1",
            "parents": [1],
            "before": {},
            "after": {"message": "Ready"},
        },
    ]
    other = deepcopy(events)
    other[0]["action_id"] = "a9"
    other[1].update(action_id="a9", resource="notice:a9")
    result = align({"effect_events": events}, {"effect_events": other})
    assert result["matched_count"] == 2
    assert result["only_left"] == result["only_right"] == []
    other[0]["after"]["reviewed"] = False
    assert align({"effect_events": events}, {"effect_events": other})["only_left"]


def valid_branches():
    return {
        name + suffix: {
            "valid": True,
            "checkpoint": {"prefix": 1},
            "outcome_hash": "same",
            "continuation_hash": "same",
            "ack_evidence": {"verified": True},
        }
        for name in CONDITIONS
        for suffix in ("", "_placebo")
    }


@pytest.mark.parametrize("name", [n + s for n in CONDITIONS for s in ("", "_placebo")])
def test_every_checkpoint_required(name):
    branches = valid_branches()
    assert certify(branches)["valid"]
    branches[name]["checkpoint"]["prefix"] = 2
    assert not certify(branches)["valid"]
    del branches[name]
    assert not certify(branches)["valid"]


def test_placebo_trace_and_null_and_ack_are_required():
    for name, key, value in [
        ("execute_placebo", "continuation_hash", "changed"),
        ("null_suppress", "outcome_hash", "changed"),
        ("lost_ack", "ack_evidence", {"verified": False}),
    ]:
        branches = valid_branches()
        branches[name][key] = value
        assert not certify(branches)["valid"]


def test_new_event_null_before_and_changed_action_identity():
    event = {
        "id": 1,
        "kind": "task.updated",
        "action_id": "a1",
        "resource": "TASK-42",
        "parents": [],
        "before": None,
        "after": {"description": "API v2"},
    }
    assert align({"effect_events": [event]}, {"effect_events": [event]})["matched_count"] == 1
