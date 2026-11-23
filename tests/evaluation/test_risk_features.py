import pytest

from afterclick.research.features import Features, vector


@pytest.mark.parametrize(
    "hidden",
    [
        "mechanism",
        "seed",
        "branch",
        "oracle",
        "outcome",
        "event_time",
        "future_schedule",
        "recovery_class",
        "intervention",
        "receipt_time",
    ],
)
def test_predictive_boundary_rejects_hidden_fields(hidden):
    features = dict(
        horizon_ms=100,
        candidate_action="mark_reviewed",
        goal_authorizes_review=False,
        visible_description_ready=True,
    )
    with pytest.raises(ValueError):
        Features.model_validate(dict(features, **{hidden: 1}))
    assert vector({"features": features, "metadata": {hidden: "not passed"}}) == [100 / 1535, 0, 1]
