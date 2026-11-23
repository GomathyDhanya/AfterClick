from copy import deepcopy

import pytest

from afterclick.evaluation.capability_oracle import verify
from afterclick.evaluation.capability_pilot import case


@pytest.mark.parametrize("mechanism", ["delegated_authority", "deadline_opportunity"])
def test_early_late_and_expiry_have_distinct_current_and_historical_targets(mechanism):
    early = case(mechanism, 7, "early")
    late = case(mechanism, 7, "late")
    expired = case(mechanism, 7, "expired")
    assert early["passed"] and late["passed"] and expired["passed"]
    assert not early["certificate"]["historical_forbidden_event"]
    assert late["certificate"]["historical_forbidden_event"]
    assert expired["certificate"]["historical_forbidden_event"]
    if mechanism == "delegated_authority":
        assert expired["certificate"]["classification"] == "VERIFIED_RECOVERABLE"
        assert not expired["certificate"]["current_residual"]
    else:
        assert expired["certificate"]["classification"] == "VERIFIED_UNRECOVERABLE"


def test_oracle_rejects_erased_independent_work_and_missing_commit_proof():
    x = case("delegated_authority", 7, "independent")
    assert x["passed"]
    arguments = dict(prefix_valid=True)
    after = deepcopy(x["after"]["sink"])
    after["state"]["note"] = "initial"
    assert (
        verify(
            x["mechanism"],
            x["before"]["sink"],
            after,
            x["reference"]["sink"],
            x["before"]["source"]["effect_events"],
            **arguments,
        )["classification"]
        == "UNKNOWN"
    )
    assert (
        verify(
            x["mechanism"],
            x["before"]["sink"],
            x["after"]["sink"],
            x["reference"]["sink"],
            [],
            **arguments,
        )["classification"]
        == "UNKNOWN"
    )
