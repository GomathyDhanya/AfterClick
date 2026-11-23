import copy
import json

import httpx
import pytest
from playwright.sync_api import sync_playwright

from afterclick.agent.modal_policy import InferenceError, Limits, atomic_json
from afterclick.model_sprint.driver import run_task
from afterclick.model_sprint.finance import SprintSupervisor
from afterclick.model_sprint.oracle import evaluate
from afterclick.model_sprint.policy import NaturalConfig, NaturalPolicy
from afterclick.model_sprint.tasks import suite
from research_ops.scripts.p1_existing import smoke_input
from tests.agent.test_native_tools import call, reply


def make(tmp_path, handler):
    return NaturalPolicy(
        NaturalConfig(
            endpoint_url="https://fixture.modal.direct",
            endpoint_name="AfterClick",
            underlying_model="Qwen/Qwen3.5-4B",
            model_revision="fixture",
            max_input_tokens=16384,
            max_output_tokens=384,
            timeout_seconds=1,
        ),
        Limits(max_calls=6, max_total_tokens=100608, max_wall_seconds=100),
        journal=tmp_path / "model_calls.jsonl",
        transport=httpx.MockTransport(handler),
    )


def test_private_goals_and_hidden_fields_rejected_before_http(tmp_path):
    p = make(tmp_path, lambda request: pytest.fail("must not send hidden input"))
    visible = smoke_input()
    private = suite()[0].private()
    with pytest.raises(InferenceError):
        p.decide(task=private, observation=visible["observation"], history=[])
    visible["task"]["goals"] = [
        dict(table="tasks", record_id="TASK-42", field="reviewed", operator="equals", value=True)
    ]
    with pytest.raises(InferenceError, match="private_evaluation"):
        p.decide(**visible)
    visible["task"]["goals"] = []
    visible["observation"]["future_schedule"] = 100
    with pytest.raises(InferenceError, match="invalid_public"):
        p.decide(**visible)
    assert p.usage_summary()["calls"] == 0
    p.close()


def test_compaction_keeps_tool_ids_and_results(tmp_path):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return reply([call(id=f"id-{len(requests)}")])

    p = make(tmp_path, handler)
    public = smoke_input()
    p.decide(**public)
    p.tool_result("id-1", status="completed", **public)
    p.decide(**public)
    body = requests[-1]
    assert "response_format" not in body and body["tool_choice"] == "auto"
    assert [m["tool_call_id"] for m in body["messages"] if m["role"] == "tool"] == ["id-1"]
    old = [m for m in body["messages"] if m["role"] == "user"][0]
    assert "observation" not in json.loads(old["content"])
    p.close()


@pytest.mark.browser
def test_real_browser_sql_notification_and_no_oracle_feedback(tmp_path):
    sent = []
    spec = suite()[0]
    batches = [
        [
            call(
                "browser_fill",
                {"target": "Description", "value": spec.expected["description"]},
                "d",
            ),
            call("browser_click", {"target": "Mark reviewed"}, "r"),
        ],
        [call("finish_task", {}, "f")],
    ]

    def handler(request):
        sent.append(json.loads(request.content))
        return reply(batches.pop(0))

    p = make(tmp_path, handler)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        report = run_task(browser, spec, p, tmp_path / "task", float("inf"))
        browser.close()
    assert report["valid"], report.get("error") or report.get("oracle_error")
    assert report["oracle"]["safe_task_success"]
    assert report["oracle"]["receipt_count"] == 1
    writes = [e for e in report["state"]["effect_events"] if e["kind"] == "task.updated"]
    assert {e["actor"] for e in writes} == {"mock-model"}
    assert all(a["source"]["tool_call_id"] in {"d", "r"} for a in report["actions"][1:])
    assert report["actions"][0]["source"]["kind"] == "driver"
    assert all(
        json.loads(m["content"])["task"]["goals"] == []
        for b in sent
        for m in b["messages"]
        if m["role"] == "user" and "task" in json.loads(m["content"])
    )
    corrupted = copy.deepcopy(report["state"])
    corrupted["notification_deliveries"] = []
    assert not evaluate(spec, report["initial_state"], corrupted)["receiver_consistent"]
    assert evaluate(suite()[1], report["initial_state"], report["state"])[
        "unauthorized_irreversible_event_ids"
    ]
    p.close()


@pytest.mark.browser
def test_premature_model_finish_is_not_oracle_corrected(tmp_path):
    p = make(tmp_path, lambda request: reply([call("finish_task", {}, "f")]))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        report = run_task(browser, suite()[1], p, tmp_path / "task", float("inf"))
        browser.close()
    assert report["valid"] and report["completed_claim"]
    assert not report["oracle"]["goal_success"]
    assert report["model_calls"] == 1
    assert json.loads(p.messages[-1]["content"])["status"] == "completed"
    p.close()


def test_sprint_envelope_cannot_be_bypassed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "research_ops").mkdir()
    atomic_json(
        "research_ops/SPRINT_AUTHORIZATION.json",
        dict(baseline_closed_runs=[], additional_cap_usd=6, baseline_metered_highwater_usd=0),
    )
    s = SprintSupervisor(tmp_path / "state.json")
    s.data = dict(runs=[dict(run_id="spent", guard_charge_usd=5.9)])
    with pytest.raises(ValueError, match="Sprint"):
        s.reserve("new", "trajectories", 0.2, dict(metered_cost=0), 10)


def test_paired_suite_has_no_hidden_public_metadata():
    tasks = suite()
    assert len(tasks) == 12 and len({t.source_group for t in tasks}) == 6
    assert len({t.instruction for t in tasks}) == 12
    assert all(
        set(t.public()) == {"instruction", "goals"} and not t.public()["goals"] for t in tasks
    )
