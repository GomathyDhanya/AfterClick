import json

import pytest

from afterclick.agent.modal_policy import atomic_json
from afterclick.tcope.analyze import exact_sign, summarize, wilson
from afterclick.tcope.belief import BeliefWorld
from afterclick.tcope.controllers import Forecast, PublicDecision, forecast_utility
from afterclick.tcope.forecasts import belief_spec, public_progress
from afterclick.tcope.lifecycle import validate_phase_budget
from tests.tcope.test_controllers import public


def test_new_belief_preserves_known_public_protection_without_actual_future():
    p = public()
    raw = p.model_dump()
    visible = dict(
        service="resource",
        age_ms=2500,
        permission="granted",
        preparation="staged",
        cancellation="requested",
        acknowledgment="verified",
        request_resolved=True,
        observed_receipts=0,
        verification_age_ms=100,
    )
    raw["observation"]["text"] = json.dumps(visible)
    p = PublicDecision.model_validate(raw)
    spec = belief_spec(p, 711)
    assert not spec.schedule["pending"]
    w = BeliefWorld(spec, p)
    try:
        w.initialize()
        actual = w.public()
        for key in visible:
            assert actual[key] == visible[key], key
        assert w.snapshot()["tc_runtime"][0]["state"]["deadline"] in [4500, 6500, 8500, 11000]
        assert w.public()["cancellation"] == "requested"
    finally:
        w.db.drop_experiment()
    raw["observation"]["text"] = json.dumps({**visible, "observed_receipts": 1})
    positive = BeliefWorld(spec, PublicDecision.model_validate(raw))
    try:
        positive.initialize()
        with positive.serve():
            assert positive.public()["observed_receipts"] == 1
            snapshot = positive.snapshot()
            assert snapshot["tc_accounts"][0]["units"] == 2
            assert snapshot["tc_receipts"][0]["payload"]["source"] == "public_known_count"
            assert snapshot["tc_receipts"][0]["id"].startswith("belief-known-")
    finally:
        positive.db.drop_experiment()


def test_public_intent_does_not_invent_already_queued_authorized_effect():
    from afterclick.tcope.workload_specs import workload_suite

    p = public(index=5)
    assert not belief_spec(p, 711).schedule["pending"]
    raw = p.model_dump()
    raw["observation"]["text"] += "\n" + workload_suite()[5].comment
    observed = p.observation.model_dump()
    observed["text"] = (
        json.dumps(dict(service="resource", observed_receipts=1))
        + "\n"
        + workload_suite()[5].comment
    )
    observed["inputs"]["Description"] = workload_suite()[5].expected["description"]
    score, bad = public_progress(p, observed)
    assert score == 3.0 and bad == 0
    with pytest.raises(ValueError, match="Invalid forecast"):
        forecast_utility(
            Forecast(
                public_progress=0.0,
                public_forbidden_receipts=0,
                model_calls=0,
                elapsed_ms=1.0,
                outcome="error",
            )
        )


def test_shared_phase_maxima_do_not_expand_hard_dollar_or_wall_envelope():
    p = dict(
        total_seconds=555,
        startup_seconds=270,
        inference_seconds=375,
        cleanup_seconds=45,
        max_usd=1.0,
        shared_wall_envelope=True,
    )
    validate_phase_budget(p)
    assert min(0 + 555 - 45, 150 + 375) == 510
    with pytest.raises(ValueError):
        validate_phase_budget({**p, "max_usd": 0.8})
    with pytest.raises(ValueError):
        validate_phase_budget({**p, "inference_seconds": 1000})
    with pytest.raises(ValueError):
        validate_phase_budget({**p, "shared_wall_envelope": False})


def test_statistics_use_source_units_and_keep_unattempted_conditions(tmp_path):
    assert exact_sign([True] * 3, [False] * 3)["exact_two_sided_p"] == 0.25
    assert exact_sign([True] * 8, [True] * 8)["exact_two_sided_p"] == 1.0
    assert 0.32 < wilson(0, 8)[1] < 0.33
    run = tmp_path / "run"
    run.mkdir()
    atomic_json(
        run / "protocol.json",
        dict(
            partition="development",
            case_id="dev-01",
            execution_order=["none", "stage_verify", "tcope"],
        ),
    )
    row = dict(
        source_group="dev-source-01",
        arm="stage_verify",
        case_id="dev-01",
        valid=True,
        invalid=False,
        unknown=False,
        censored=False,
        goal_success=True,
        safe_task_success=True,
        model_calls=2,
        unauthorized_receipts=0,
        role="primary_controller",
    )
    (run / "trials.jsonl").write_text(json.dumps(row) + "\n")
    (run / "model_calls.jsonl").touch()
    result = summarize([run], tmp_path / "output")
    by = {r["arm"]: r for r in result["arms"]}
    assert (
        by["none"]["planned"] == 1
        and by["none"]["attempted"] == 0
        and by["none"]["unattempted"] == 1
    )
    assert by["tcope"]["safe_completed"] == 0 and by["stage_verify"]["safe_completed"] == 1


def test_shared_factory_retains_existing_eighty_percent_compute_buffer(tmp_path):
    import time

    import httpx

    from afterclick.agent.modal_policy import InferenceError
    from afterclick.tcope.budget import Factory

    (tmp_path / "raw").mkdir()
    protocol = dict(
        arm_call_caps={"corrected": 80},
        max_input_tokens=16384,
        max_output_tokens=512,
        request_timeout_seconds=30,
        max_usd=1.0,
        max_rate_usd_per_second=0.00135,
        startup_seconds=270,
        cleanup_seconds=45,
        shared_wall_envelope=True,
        public_task_hashes=[],
        max_calls=80,
        max_total_reserved_tokens=80 * 16896,
    )
    info = dict(
        service_url="https://fixture.modal.direct",
        model_name="AfterClick",
        repo_id="Qwen/Qwen3.5-9B",
        revision="fixture",
    )
    with pytest.raises(ValueError, match="Measured startup"):
        Factory(tmp_path, protocol, info, time.monotonic() + 360, 24)
    factory = Factory(
        tmp_path,
        protocol,
        info,
        time.monotonic() + 360,
        24,
        startup_elapsed_seconds=150,
        transport=httpx.MockTransport(lambda request: pytest.fail("No HTTP in financial test")),
    )
    policy = factory.make()
    path = factory.settings["corrected"][2]
    approved = policy.policy._approval(path)
    assert approved["startup_allowance_seconds"] == 150
    altered = {**approved, "startup_allowance_seconds": 270}
    atomic_json(path, altered)
    with pytest.raises(InferenceError, match="insufficient_compute_cost_buffer"):
        policy.policy._approval(path)
    assert factory.usage()["calls"] == 0
    factory.close()


def test_forecast_copies_public_comment_display_without_branch_marker(tmp_path):
    import time

    import httpx
    from playwright.sync_api import sync_playwright

    from afterclick.tcope.budget import Factory
    from afterclick.tcope.driver import run_task
    from afterclick.tcope.forecasts import ForecastEngine
    from afterclick.tcope.workload_specs import workload_suite
    from afterclick.tcope.workloads import WorkloadWorld
    from tests.agent.test_native_tools import call, reply
    from tests.tcope.test_execution import make

    spec = workload_suite()[1]
    batches = [
        [
            call(
                "browser_fill",
                {"target": "Description", "value": spec.expected["description"]},
                "desc",
            ),
            call("browser_fill", {"target": "Comment", "value": spec.comment}, "draft"),
        ],
        [call("browser_click", {"target": "Post"}, "post")],
        [call("browser_click", {"target": "Send notice"}, "send")],
        [call("finish_task", {}, "parent-done")],
    ]
    policy = make(
        tmp_path / "parent-policy", lambda request: reply(batches.pop(0)), model="Qwen/Qwen3.5-9B"
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        result = run_task(
            browser, spec, policy, tmp_path / "parent", float("inf"), world=WorkloadWorld(spec)
        )
        browser.close()
    assert result["valid"] and result["oracle"]["safe_task_success"]
    cp = json.loads((tmp_path / "parent/checkpoint-03.json").read_text())
    public_input = PublicDecision.from_visible(
        spec.public(),
        cp["observation"],
        __import__("afterclick.extensions.native_tools", fromlist=["parse_call"]).parse_call(
            cp["proposed_call"]
        ),
        [],
        10,
    )
    run = tmp_path / "forecast"
    (run / "raw").mkdir(parents=True)
    protocol = dict(
        arm_call_caps={"corrected": 10},
        max_input_tokens=16384,
        max_output_tokens=512,
        request_timeout_seconds=1,
        max_usd=1.0,
        max_rate_usd_per_second=0.00135,
        startup_seconds=270,
        cleanup_seconds=45,
        public_task_hashes=[],
        max_calls=10,
        max_total_reserved_tokens=168960,
    )
    info = dict(
        service_url="https://fixture.modal.direct",
        model_name="AfterClick",
        repo_id="Qwen/Qwen3.5-9B",
        revision="fixture",
    )
    factory = Factory(
        run,
        protocol,
        info,
        time.monotonic() + 100,
        24,
        transport=httpx.MockTransport(
            lambda request: reply([call("finish_task", {}, "suffix-done")])
        ),
    )
    conversation = {
        key: cp[key]
        for key in ["messages", "history", "pending_ids", "seen_ids", "batch_remaining", "source"]
    }
    engine = ForecastEngine(factory, run / "engine", conversation)
    summary = engine(public_input, {"kind": "execute"})
    engine.join()
    assert summary["outcome"] == "observed" and summary["model_calls"] == 1
    sent = [row["request"] for row in factory.rows() if row["event"] == "finished"]
    assert sent and "belief-initializer" not in json.dumps(sent)
    assert "mock_policy:" in json.dumps(sent)  # Original ordinary visible author retained.
    assert engine.results[0]["result"]["valid"]
    assert not engine.results[0]["result"]["live_continuation"]
    factory.close()
    policy.close()


def test_adaptive_single_forecast_can_defer_risk_until_new_public_verification():
    from afterclick.tcope.controllers import Controller

    p = public(index=5)
    raw = p.model_dump()
    raw["proposal"] = {"kind": "click", "target": "Capture resource", "value": ""}
    raw["latency_ms"] = [100.0]
    raw["observation"]["text"] = (
        json.dumps(
            dict(
                service="resource",
                age_ms=0,
                acknowledgment="pending or uncertain",
                observed_receipts=0,
            )
        )
        + "\n"
        + __import__("afterclick.tcope.workload_specs", fromlist=["workload_suite"])
        .workload_suite()[5]
        .comment
    )
    p = PublicDecision.model_validate(raw)
    c = Controller(
        "tcope",
        latency_prior_ms=100,
        rollout=lambda public, candidate: dict(
            public_progress=2.0,
            public_forbidden_receipts=1,
            model_calls=1,
            elapsed_ms=10.0,
            outcome="observed",
        ),
    )
    assert c.choose(p)["kind"] == "suppress"
    assert c.choose(p)["kind"] == "suppress"
    raw["observation"]["text"] = (
        json.dumps(
            dict(
                service="resource",
                age_ms=1000,
                acknowledgment="verified",
                observed_receipts=0,
                verification_age_ms=100,
            )
        )
        + "\n"
        + __import__("afterclick.tcope.workload_specs", fromlist=["workload_suite"])
        .workload_suite()[5]
        .comment
    )
    assert c.choose(PublicDecision.model_validate(raw))["kind"] == "execute"
