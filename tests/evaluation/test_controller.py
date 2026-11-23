from afterclick.research.controller import Controller


def features(at=300, authorized=False):
    return dict(
        horizon_ms=at,
        candidate_action="mark_reviewed",
        goal_authorizes_review=authorized,
        visible_description_ready=True,
    )


def test_online_prefix_quota_and_authorized_goal_preservation():
    c = Controller("learned_risk", 0.2)
    for index in range(100):
        authorized = index % 3 == 0
        denied = c.act(features(authorized=authorized), 0.9, str(index))
        assert not (authorized and denied)
        assert c.denied <= int(0.2 * (index + 1) + 1e-9)
    # The last arrival is authorized. Unused quota must never force its rejection.
    assert c.denied == 19


def test_decision_prefix_does_not_depend_on_future_observations():
    first = Controller("authorization_timer", 0.4)
    second = Controller("authorization_timer", 0.4)
    prefix = [first.act(features(at=100 + i * 20), 0.9, str(i)) for i in range(10)]
    copy = [second.act(features(at=100 + i * 20), 0.9, str(i)) for i in range(10)]
    second.act(features(at=0, authorized=True), 0, "different-future")
    assert prefix == copy
