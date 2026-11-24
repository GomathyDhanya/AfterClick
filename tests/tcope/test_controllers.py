import copy
import json
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import sync_playwright
from pydantic import ValidationError

from afterclick.agent.action_parser import Decision
from afterclick.tcope.budget import Factory
from afterclick.tcope.comparison import Bridge
from afterclick.tcope.controllers import Controller, Forecast, PublicDecision
from afterclick.tcope.driver import run_task
from afterclick.tcope.forecasts import belief_spec
from afterclick.tcope.workload_specs import workload_suite
from afterclick.tcope.workloads import WorkloadWorld
from research_ops.scripts.p1_existing import smoke_input
from tests.agent.test_native_tools import call, reply
from tests.tcope.test_execution import make


def public(index=4, age=0):
    p = smoke_input()
    p["task"] = workload_suite()[index].public()
    p["observation"]["text"] += "\n" + json.dumps(
        dict(
            service="resource",
            age_ms=age,
            acknowledgment="pending or uncertain",
            cancellation="not requested",
            observed_receipts=0,
        )
    )
    p["observation"]["controls"].append(dict(role="button", name="Cancel resource", enabled=True))
    return PublicDecision.from_visible(
        p["task"],
        p["observation"],
        Decision(kind="fill", target="Description", value="x"),
        [1000.0],
        10,
    )


def test_selector_rejects_hidden_features_and_forecast_oracle():
    p = public()
    with pytest.raises(ValidationError):
        PublicDecision.model_validate({**p.model_dump(), "actual_deadline": 55})
    raw = p.model_dump()
    raw["observation"]["private_schedule"] = [1]
    with pytest.raises(ValidationError):
        PublicDecision.model_validate(raw)
    raw = p.model_dump()
    raw["task"]["goals"] = [
        dict(
            table="tasks",
            record_id="TASK-42",
            field="description",
            operator="equals",
            value="hidden",
        )
    ]
    with pytest.raises(ValueError):
        PublicDecision.from_visible(raw["task"], raw["observation"], p.proposal, [], 10)
    with pytest.raises(ValidationError):
        Forecast.model_validate(
            dict(
                public_progress=1.0,
                public_forbidden_receipts=0,
                model_calls=1,
                elapsed_ms=1.0,
                outcome="observed",
                oracle_safe=True,
            )
        )
    with pytest.raises(TypeError):
        Controller("tcope").choose({"world": {}})
    # Equal public observations construct exactly equal priors, regardless of an
    # actual world's realized future (which is never an argument).
    assert belief_spec(p, 711).private() == belief_spec(copy.deepcopy(p), 711).private()


def test_computation_order_and_tcope_stop_against_strong_stage_baseline():
    p = public()
    for arm, expected in [
        ("stage_verify", ["stage"]),
        ("tcope", ["stage"]),
        ("fixed_budget", ["stage", "rollout", "rollout"]),
        ("time_blind", ["rollout", "rollout", "stage"]),
    ]:
        events = []

        def rollout(public, candidate):
            events.append("rollout")
            return dict(
                public_progress=1.0,
                public_forbidden_receipts=0,
                model_calls=1,
                elapsed_ms=100.0,
                outcome="observed",
            )

        c = Controller(arm, stage=lambda d: events.append("stage"), rollout=rollout)
        selected = c.choose(p)
        assert events == expected
        assert selected["kind"] == "execute"
        assert selected["staged_action"]["target"] == "Cancel resource"


@pytest.mark.browser
def test_real_clock_runs_during_forecast_and_early_protection_prevents(tmp_path):
    from dataclasses import replace

    spec = replace(
        workload_suite()[4], schedule={"pending": True, "deadline_ms": 2000, "ack_lag_ms": 5000}
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        batches = [
            [
                call(
                    "browser_fill",
                    {"target": "Description", "value": spec.expected["description"]},
                    "desc",
                )
            ],
            [call("finish_task", {}, "finish-parent")],
        ]
        parent_policy = make(tmp_path / "parent-policy", lambda request: reply(batches.pop(0)))
        parent = run_task(
            browser,
            spec,
            parent_policy,
            tmp_path / "parent",
            float("inf"),
            world=WorkloadWorld(spec),
        )
        assert parent["valid"], parent.get("error")
        cp = json.loads((tmp_path / "parent/checkpoint-00.json").read_text())
        protocol = dict(
            arm_call_caps={"corrected": 30},
            max_input_tokens=16384,
            max_output_tokens=512,
            request_timeout_seconds=1,
            max_usd=1.0,
            max_rate_usd_per_second=0.00135,
            startup_seconds=270,
            cleanup_seconds=45,
            public_task_hashes=[],
            max_calls=30,
            max_total_reserved_tokens=30 * 16896,
        )
        info = dict(
            service_url="https://fixture.modal.direct",
            model_name="AfterClick",
            repo_id="Qwen/Qwen3.5-9B",
            revision="fixture",
        )
        results = {}
        for arm in ["time_blind", "fixed_budget"]:
            run = tmp_path / arm
            (run / "raw").mkdir(parents=True)
            factory = Factory(
                run,
                protocol,
                info,
                time.monotonic() + 100,
                27,
                transport=httpx.MockTransport(
                    lambda request: reply([call("finish_task", {}, "suffix-finish")])
                ),
            )
            factory.begin_trial(10)
            policy = factory.make()
            bridge = Bridge(arm, spec, policy, factory, run / "controller")
            result = run_task(
                browser,
                spec,
                policy,
                run / "world",
                factory.deadline,
                world=WorkloadWorld(spec),
                checkpoint=cp,
                interceptor=bridge,
            )
            forecasts = bridge.finish()
            assert result["valid"], result.get("error") or result.get("oracle_error")
            assert forecasts and all(r["result"]["model_calls"] > 0 for r in forecasts)
            assert not any(
                "error"
                in json.loads((Path(r["directory"]) / "public-summary.json").read_text())["outcome"]
                for r in forecasts
            )
            results[arm] = result
            factory.end_trial()
            factory.close()
        assert results["time_blind"]["oracle"]["mock_receipts"] == 1
        assert results["fixed_budget"]["oracle"]["mock_receipts"] == 0
        # Model prefix queued once, actual substituted protection acknowledged.
        step = results["fixed_budget"]["steps"][0]
        assert step["status"] == "completed" and step["executed"]
        assert json.loads(step["tool_result_message"]["content"])["action_receipt"][
            "requested_executed"
        ]
        assert (
            results["fixed_budget"]["state"]["tasks"][0]["description"]
            == spec.expected["description"]
        )
        assert not results["fixed_budget"]["live_continuation"]  # Mock never genuine.
        browser.close()
        parent_policy.close()


def test_adaptive_allocation_is_reachable_but_stops_when_latency_exceeds_opportunity():
    p = public(index=1)
    raw = p.model_dump()
    raw["proposal"] = {"kind": "click", "target": "Send notice", "value": ""}
    raw["latency_ms"] = [100.0]
    raw["observation"]["text"] += "\n" + workload_suite()[1].comment
    p = PublicDecision.model_validate(raw)
    explored = []

    def forecast(p, candidate):
        explored.append(candidate)
        return dict(
            public_progress=1.0,
            public_forbidden_receipts=0,
            model_calls=1,
            elapsed_ms=100.0,
            outcome="observed",
        )

    Controller("tcope", rollout=forecast, latency_prior_ms=100).choose(p)
    assert len(explored) == 1
    explored.clear()
    Controller("tcope", rollout=forecast, latency_prior_ms=5000).choose(p)
    assert not explored


def test_snapshot_copy_orders_self_referential_jobs():
    from afterclick import domain
    from afterclick.tcope.driver import CoreWorld
    from afterclick.tcope.tasks import competence_suite

    a, b = CoreWorld(competence_suite()[0]), CoreWorld(competence_suite()[0])
    try:
        a.initialize()
        with a.db.engine.connect() as c:
            current = domain.task(c, "TASK-42")
        domain.patch_task(
            a.db,
            "TASK-42",
            {"assignee": "Noah"},
            current["version"],
            "assignment",
            "assignment",
            "scripted-test",
        )
        domain.advance(a.db, 1000)
        state = a.snapshot()
        assert any(j["parent_id"] for j in state["scheduled_jobs"])
        b.initialize({"world": state})
        assert b.snapshot() == state
    finally:
        a.db.drop_experiment()
        b.db.drop_experiment()
