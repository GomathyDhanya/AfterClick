import json
import time

import httpx
from playwright.sync_api import sync_playwright

from afterclick.tcope.budget import Factory
from afterclick.tcope.comparison import Bridge
from afterclick.tcope.driver import append, run_task
from afterclick.tcope.workload_specs import workload_suite
from afterclick.tcope.workloads import WorkloadWorld
from tests.agent.test_native_tools import call, reply
from tests.tcope.test_execution import make


def test_protective_action_awaits_slow_real_http_response(tmp_path):
    spec = workload_suite()[4]
    world = WorkloadWorld(spec)
    original = world.action

    def delayed(*args, **kwargs):
        result = original(*args, **kwargs)
        time.sleep(1.2)  # Real ACK delay after commit; worker continues independently.
        return result

    world.action = delayed
    (tmp_path / "raw").mkdir()
    batches = [
        [
            call(
                "browser_fill",
                {"target": "Description", "value": spec.expected["description"]},
                "desc",
            )
        ],
        [call("finish_task", {}, "finish")],
    ]
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
        tmp_path,
        protocol,
        info,
        time.monotonic() + 100,
        27,
        transport=httpx.MockTransport(lambda request: reply(batches.pop(0))),
    )
    factory.begin_trial(10)
    policy = factory.make()
    bridge = Bridge("stage_verify", spec, policy, factory, tmp_path / "controller")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        result = run_task(
            browser,
            spec,
            policy,
            tmp_path / "world",
            factory.deadline,
            world=world,
            interceptor=bridge,
        )
        browser.close()
    assert result["valid"] and result["termination"] == "model_finish", result.get("error")
    assert result["steps"][0]["status"] == "deferred"
    assert result["policy_usage"]["calls"] == 2 and not result["policy_usage"]["uncertain"]
    assert len(result["model_request_ids"]) == 2
    actions = [
        json.loads(line)
        for line in (tmp_path / "controller/protective-actions.jsonl").read_text().splitlines()
    ]
    assert actions[0]["elapsed_ms"] >= 1200
    factory.end_trial()
    factory.close()


def test_forecast_local_usage_excludes_other_shared_inflight_request(tmp_path):
    policy = make(tmp_path / "policy", lambda request: reply([call("finish_task", {}, "finish")]))

    def other_conversation_started(observation):
        append(
            policy.journal,
            dict(
                event="started",
                request_id="other-conversation-mock",
                reserved_tokens=16896,
                timestamp=time.time(),
                status="pending",
            ),
        )

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        result = run_task(
            browser,
            workload_suite()[6],
            policy,
            tmp_path / "world",
            float("inf"),
            public_done=other_conversation_started,
        )
        browser.close()
    assert policy.usage_summary()["uncertain"]  # Global in-flight status remains conservative.
    assert not result["policy_usage"]["uncertain"]  # This completed conversation is known.
    assert result["policy_usage"]["calls"] == 1
    assert len(result["model_request_ids"]) == 1
    policy.close()
