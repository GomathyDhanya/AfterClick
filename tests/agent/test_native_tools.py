import json

import httpx
import pytest
from playwright.sync_api import sync_playwright

from afterclick.agent.modal_policy import InferenceError, Limits
from afterclick.extensions.interaction_trial import run_task
from afterclick.extensions.native_tools import NativeConfig, NativeToolPolicy, parse_call, tools
from research_ops.scripts.p1_existing import contracts, smoke_input


def call(name="browser_select", args=None, id="call1"):
    return dict(
        id=id,
        type="function",
        function=dict(
            name=name,
            arguments=json.dumps(
                args if args is not None else {"target": "Priority", "value": "High"}
            ),
        ),
    )


def reply(calls):
    return httpx.Response(
        200,
        json=dict(
            model="AfterClick",
            usage=dict(prompt_tokens=100, completion_tokens=30, total_tokens=130),
            choices=[
                dict(
                    finish_reason="tool_calls",
                    message=dict(role="assistant", content=None, tool_calls=calls),
                )
            ],
        ),
    )


def make(tmp_path, handler):
    return NativeToolPolicy(
        NativeConfig(
            endpoint_url="https://fixture.modal.direct",
            endpoint_name="AfterClick",
            max_input_tokens=16384,
            timeout_seconds=1,
        ),
        Limits(max_calls=6, max_total_tokens=100000, max_wall_seconds=100),
        journal=tmp_path / "calls.jsonl",
        transport=httpx.MockTransport(handler),
    )


def test_tools_are_separate_and_correlated(tmp_path):
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        return reply([call(id="call" + str(len(requests)))])

    p = make(tmp_path, handler)
    public = smoke_input()
    calls = p.decide(**public)
    assert requests[0]["tool_choice"] == "auto" and "response_format" not in requests[0]
    assert len(tools()) == 7
    with pytest.raises(InferenceError, match="unresolved_tool"):
        p.decide(**public)
    p.tool_result(calls[0]["id"], status="invalid_arguments", **public)
    p.decide(**public)
    assert any(
        m.get("tool_call_id") == "call1" and m["role"] == "tool" for m in requests[-1]["messages"]
    )
    p.close()


@pytest.mark.parametrize(
    "item",
    [
        call(args={"target": "Priority", "value": "Explode"}),
        call("shell"),
        call(args={"target": "Priority", "value": "High", "oracle": True}),
        call("finish_task", {"oracle": True}),
        call("browser_navigate", {"target": "https://evil.example"}),
    ],
)
def test_strict_arguments(item):
    with pytest.raises((ValueError, TypeError)):
        parse_call(item)


def test_duplicate_json_and_ids_rejected(tmp_path):
    c = call()
    c["function"]["arguments"] = '{"target":"Priority","target":"Status","value":"High"}'
    with pytest.raises(ValueError):
        parse_call(c)
    p = make(tmp_path, lambda request: reply([call(), call()]))
    with pytest.raises(InferenceError, match="duplicate"):
        p.decide(**smoke_input())
    assert not p.usage_summary()["uncertain"]
    p.close()


def test_hidden_observation_never_sent(tmp_path):
    p = make(tmp_path, lambda request: pytest.fail("must not send"))
    payload = smoke_input()
    payload["observation"]["scheduler"] = 1
    with pytest.raises(InferenceError, match="invalid_public_input"):
        p.decide(**payload)
    assert p.usage_summary()["calls"] == 0
    p.close()


def test_unknown_completion_blocks_future_calls(tmp_path):
    p = make(tmp_path, lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("uncertain")))
    with pytest.raises(InferenceError):
        p.decide(**smoke_input())
    with pytest.raises(InferenceError, match="unknown"):
        p.decide(**smoke_input())
    assert p.usage_summary()["calls"] == 1
    p.close()


@pytest.mark.browser
def test_native_real_gateway_errors_repetition_completion_and_tool_ids(tmp_path):
    sent = []
    batches = [
        [
            call("browser_fill", {"target": "Description", "value": "Document API v2."}, "one"),
            call(id="two"),
        ],
        [call(id="repeat"), call("browser_select", {"target": "Priority", "value": "bad"}, "bad")],
        [call("finish_task", {}, "finish")],
    ]

    def handler(request):
        sent.append(json.loads(request.content))
        return reply(batches.pop(0))

    p = make(tmp_path, handler)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        report = run_task(browser, contracts()[1], p, tmp_path / "browser", float("inf"))
        browser.close()
    assert report["accepted"] and report["task"]["success"]
    assert report["repeated_proposals"] == 1 and report["argument_errors"] == 1
    assert report["executed_repetitions"] == 0
    results = [m for m in sent[-1]["messages"] if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in results] == ["one", "two", "repeat", "bad"]
    assert json.loads(results[-1]["content"])["status"] == "invalid_arguments"
    p.close()


def test_finish_visibility_and_duplicate_result_guard(tmp_path):
    from afterclick.agent.browser_observation import public_task
    from afterclick.extensions.interaction_trial import visibly_complete

    public = smoke_input()
    task = public_task(contracts()[1])
    assert not visibly_complete(task, public["observation"])
    p = make(tmp_path, lambda request: reply([call("finish_task", {}, "end")]))
    p.decide(**public)
    p.tool_result("end", status="premature_finish", **public)
    with pytest.raises(ValueError, match="already resolved"):
        p.tool_result("end", status="completed", **public)
    p.close()
