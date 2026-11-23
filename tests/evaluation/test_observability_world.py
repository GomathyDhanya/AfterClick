from dataclasses import replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from afterclick.extensions.dispatch_oracle import certify
from afterclick.extensions.dispatch_sql import execute
from afterclick.extensions.dispatch_world import Visible, collision, generate, label_panel, simulate


@given(st.integers(1, 5000), st.sampled_from(["push_id", "push_shift", "pull_heldout"]))
@settings(max_examples=150, deadline=None)
def test_race_identity_and_preservation(seed, cohort):
    i = generate(seed, cohort)
    cancel = simulate(i, "cancel")
    verify = simulate(i, "verify")
    assert int(verify["harm"]) - int(cancel["harm"]) == int(
        i.unsafe and i.age < i.frontier <= i.age + i.probe_delay
    )
    assert cancel["independent_note"] == verify["independent_note"] == "keep-this-note"
    assert list(
        map(int, [cancel["harm"], verify["harm"], cancel["false_intervention"]])
    ) == label_panel(i, i.age)


def test_visible_allowlist_collision_and_receipt_separation():
    a, b = collision()
    assert a.visible() == b.visible()
    assert simulate(a, "verify")["harm"] and not simulate(b, "verify")["harm"]
    with pytest.raises(ValueError):
        Visible.model_validate(dict(a.visible().model_dump(), frontier=a.commit))
    result = simulate(a)
    assert next(e["time"] for e in result["events"] if e["event"] == "ack") > a.commit


@pytest.mark.parametrize("plan", ["continue", "cancel", "verify"])
@pytest.mark.parametrize("mechanism", ["push", "pull"])
def test_independent_sql_witnesses(plan, mechanism):
    i = replace(
        generate(44, "push_id"),
        mechanism=mechanism,
        unsafe=True,
        age=20,
        frontier=15 if mechanism == "pull" else 70,
        commit=70,
        probe_delay=30,
        missing_ack=False,
        duplicate_ack=True,
    )
    actual = execute(i, plan)
    expected = simulate(i, plan)
    assert actual["certificate"]["harm"] == expected["harm"]
    assert actual["certificate"]["task_success"] == expected["task_success"]
    assert actual["certificate"]["receipt_count"] <= 1
    if mechanism == "pull" and plan == "cancel":
        assert actual["certificate"]["harm"]
        assert [(x["event"], x["time"]) for x in actual["trace"]] == [
            ("independent_edit_commit", 10),
            ("unrevokable_child_commit", 15),
            ("source_cancel_commit", 20),
            ("consumer_commit", 70),
        ]


def test_oracle_refuses_fabricated_receipt_and_overwritten_independent_edit():
    source = dict(
        payload="PUBLIC_FIXTURE", independent_note="keep-this-note", cancelled=False, deadline=200
    )
    with pytest.raises(ValueError, match="fabricated"):
        certify(source, dict(copies=[]), [dict(effect_id="fake", arrival=1)])
    with pytest.raises(ValueError, match="preservation"):
        certify(dict(source, independent_note="lost"), dict(copies=[]), [])


def test_policy_boundary_and_acquisition_panels():
    import random

    import numpy as np

    from afterclick.extensions.dispatch_learning import acquire, fit, predict
    from afterclick.extensions.observability_study import choose

    rows = acquire("ordinary", 0, budget=64)
    assert len(rows) == 64 and rows[0]["measurement"] == "UNKNOWN"
    model = fit(rows, 0)
    x = generate(1).visible().model_dump()
    for name in model:
        p = predict(model, name, x)
        assert len(p) == 3 and all(0 <= v <= 1 for v in p)
    with pytest.raises(ValueError):
        choose(
            "learned_risk", dict(x, unsafe_payload=True), [lambda x: np.zeros(3)], random.Random(1)
        )
    with pytest.raises(ValueError):
        predict(model, "logistic", dict(x, oracle=True))
