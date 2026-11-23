import json
import threading
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from afterclick.agent.browser_observation import public_history
from afterclick.agent.decision_schema import CONDITIONAL, conditional_schema
from afterclick.agent.inference import VisiblePolicy
from afterclick.agent.modal_policy import (
    InferenceError,
    Limits,
    ModalConfig,
    ModalPolicy,
    RecordedOpenAIPolicy,
    digest,
)


def visible():
    return (
        {
            "instruction": "Update the description to API v2",
            "goals": [
                {
                    "table": "tasks",
                    "record_id": "TASK-42",
                    "field": "description",
                    "operator": "contains",
                    "value": "API v2",
                }
            ],
        },
        {
            "text": "Task details",
            "inputs": {
                "Description": "API v1",
                "Status": "In progress",
                "Priority": "Normal",
                "Assignee": "Maya",
                "Comment": "",
            },
            "controls": [{"role": "button", "name": "Retry save", "enabled": True}],
            "save_status": "✓ Committed",
        },
        [],
    )


def reply(content='{"kind":"done","target":"","value":""}'):
    return {
        "id": "mock-completion",
        "model": "afterclick-test",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 500, "completion_tokens": 20, "total_tokens": 520},
    }


def provider(
    tmp_path,
    *,
    response=None,
    status=200,
    limits=None,
    handler=None,
    cache=False,
    config=None,
    journal=None,
    clock=None,
):
    calls = []

    def handle(request):
        calls.append(request)
        if handler:
            return handler(request)
        return httpx.Response(status, json=reply() if response is None else response)

    policy = ModalPolicy(
        config or ModalConfig("https://test.us-west.modal.direct", "afterclick-test"),
        limits or Limits(),
        journal=journal or tmp_path / "calls.jsonl",
        transport=httpx.MockTransport(handle),
        cache_dir=tmp_path / "cache" if cache else None,
        **({"clock": clock} if clock else {}),
    )
    return policy, calls


@pytest.mark.parametrize("small", [False, True])
def test_exact_request_provenance_no_auth_in_journal(tmp_path, small):
    config = ModalConfig(
        "https://test.us-west.modal.direct",
        "afterclick-test",
        underlying_model="Qwen/Qwen3.5-4B" if small else "Qwen/Qwen3.5-9B",
        model_revision="851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a" if small else None,
    )
    p, calls = provider(tmp_path, config=config)
    assert p.decide(*visible()).kind == "done"
    sent = json.loads(calls[0].content)
    assert calls[0].url.path == "/v1/chat/completions"
    assert sent["model"] == "afterclick-test" != p.config.underlying_model
    assert sent["chat_template_kwargs"] == {"enable_thinking": False}
    assert sent["response_format"]["json_schema"]["strict"] is True
    assert p.records[0]["evidence_kind"] == "mock_openai_responses"
    assert p.records[0]["resolved_model"] == "afterclick-test"
    assert "MOCK-NOT-A-CREDENTIAL" not in p.journal.read_text()
    rows = [json.loads(line) for line in p.journal.read_text().splitlines()]
    assert [r["event"] for r in rows] == ["started", "finished"]
    assert p.usage_summary()["known_total_tokens"] == 520


def test_public_synthetic_scope_omits_credentials_and_rejects_labels(tmp_path, monkeypatch):
    monkeypatch.setenv("MODAL_PROXY_TOKEN_ID", "wk-DO-NOT-SEND")
    monkeypatch.setenv("MODAL_PROXY_TOKEN_SECRET", "ws-DO-NOT-SEND")
    calls = []

    def respond(request):
        calls.append(request)
        assert "authorization" not in request.headers
        return httpx.Response(200, json=reply())

    p = ModalPolicy(
        ModalConfig("https://test.modal.direct", "afterclick-test"),
        Limits(),
        journal=tmp_path / "calls.jsonl",
        transport=httpx.MockTransport(respond),
        public_synthetic_task_hashes=[digest(visible()[0])],
    )
    assert p.decide(*visible()).kind == "done"
    task, obs, history = visible()
    task["instruction"] = "An unregistered real user task"
    with pytest.raises(InferenceError, match="unregistered_public_synthetic_task"):
        p.decide(task, obs, history)
    task, obs, _ = visible()
    raw = [
        {
            "action": {"kind": "read", "target": "Description", "value": ""},
            "feedback": {"status": "suppressed"},
        }
    ]
    with pytest.raises(InferenceError, match="hidden_intervention_feedback"):
        p.decide(task, obs, public_history(raw, blind_interventions=False))
    assert public_history(raw)[0]["feedback"] == "completed"
    assert raw[0]["feedback"]["status"] == "suppressed"
    assert len(calls) == 1
    assert "DO-NOT-SEND" not in p.journal.read_text()


def test_live_public_exception_still_requires_specific_scope_approval(tmp_path):
    from dataclasses import asdict

    config = ModalConfig("https://test.modal.direct", "afterclick-test")
    limits = Limits(max_usd=1)
    approval = dict(
        approved_by_user=True,
        run_id="no-network-test",
        config_sha256=config.fingerprint,
        limits_sha256=digest(asdict(limits)),
        max_usd=1,
        available_compute_credit_usd=30,
        credit_verified=True,
        max_compute_usd_per_second=0.001,
        startup_allowance_seconds=0,
        shutdown_allowance_seconds=0,
        expires_utc=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    )
    path = tmp_path / "approval.json"
    path.write_text(json.dumps(approval))
    with pytest.raises(InferenceError, match="public_synthetic_approval_required"):
        ModalPolicy(
            config,
            limits,
            journal=tmp_path / "calls.jsonl",
            mode="live",
            approval_path=path,
            public_synthetic_task_hashes=[digest(visible()[0])],
        )


def test_conditional_generation_contract_rejects_real_failed_read_and_replays(tmp_path):
    # Exact semantic failure observed in warmv2; it must remain invalid.
    bad = {"kind": "read", "target": "Description", "value": "Document the API v1 integration."}
    with pytest.raises(ValueError):
        CONDITIONAL.validate_python(bad)
    assert conditional_schema()["$defs"]["Read"]["properties"]["value"]["const"] == ""
    config = ModalConfig("https://test.modal.direct", "afterclick-test", max_input_tokens=16384)
    requests = []

    def respond(request):
        requests.append(request)
        body = json.loads(request.content)
        assert body["response_format"]["json_schema"]["schema"]["type"] == "object"
        assert "value is the empty string" in body["messages"][0]["content"]
        return httpx.Response(200, json=reply('{"kind":"read","target":"Description","value":""}'))

    policy = ModalPolicy(
        config,
        Limits(),
        journal=tmp_path / "v2.jsonl",
        transport=httpx.MockTransport(respond),
        argument_contract="conditional-v2",
    )
    assert policy.decide(*visible()).kind == "read"
    assert len(requests) == 1 and policy.records[0]["argument_contract"] == "conditional-v2"
    replay = RecordedOpenAIPolicy(config, policy.records)
    assert replay.decide(*visible()).kind == "read"


@pytest.mark.parametrize(
    "content",
    [
        "no JSON",
        "",
        "{}",
        '{"kind":"run","target":"","value":""}',
        '{"kind":"done","target":"","value":"","oracle":true}',
        '{"kind":"navigate","target":"https://example.org","value":""}',
        '{"kind":"select","target":"Priority","value":"Catastrophic"}',
        '{"kind":"done","kind":"read","target":"Description","value":""}',
        None,
        [],
    ],
)
def test_invalid_outputs_preserved_and_usage_counted(tmp_path, content):
    p, calls = provider(tmp_path, response=reply(content))
    with pytest.raises(InferenceError, match="invalid_decision"):
        p.decide(*visible())
    assert len(calls) == 1 and p.records[-1]["response"] == reply(content)
    assert p.usage_summary()["known_total_tokens"] == 520
    assert not p.usage_summary()["uncertain"]


@pytest.mark.parametrize("reason", ["length", "content_filter", "tool_calls", None, "unknown"])
def test_noncomplete_status_never_becomes_action(tmp_path, reason):
    r = reply()
    r["choices"][0]["finish_reason"] = reason
    p, _ = provider(tmp_path, response=r)
    with pytest.raises(InferenceError, match="incomplete_or_ambiguous"):
        p.decide(*visible())
    assert p.records[-1]["status"] == "failed"


@pytest.mark.parametrize(
    "case", ["refusal", "tool", "empty_choices", "multiple_choices", "wrong_model"]
)
def test_refusal_tool_errors_and_model_identity(tmp_path, case):
    r = reply()
    if case == "refusal":
        r["choices"][0]["message"]["refusal"] = "cannot"
    if case == "tool":
        r["choices"][0]["message"]["tool_calls"] = [{"function": {"name": "shell"}}]
    if case == "empty_choices":
        r["choices"] = []
    if case == "multiple_choices":
        r["choices"] *= 2
    if case == "wrong_model":
        r["model"] = "unapproved-model"
    p, _ = provider(tmp_path, response=r)
    with pytest.raises(InferenceError):
        p.decide(*visible())
    assert p.records[-1]["status"] == "failed"


@pytest.mark.parametrize("status", [400, 401, 429, 500, 503, 307])
def test_http_errors_no_retry_and_freeze_survives_restart(tmp_path, status):
    p, calls = provider(tmp_path, status=status)
    with pytest.raises(InferenceError, match=f"http_{status}"):
        p.decide(*visible())
    assert p.usage_summary()["uncertain"]
    again, attempts = provider(tmp_path)
    with pytest.raises(InferenceError, match="prior_completion_or_billing_unknown"):
        again.decide(*visible())
    assert len(calls) == 1 and not attempts


@pytest.mark.parametrize(
    "error", [httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError]
)
def test_network_uncertainty_freezes_without_echoing_exception(tmp_path, error):
    def fail(request):
        raise error("SENSITIVE-CREDENTIAL", request=request)

    p, calls = provider(tmp_path, handler=fail)
    with pytest.raises(InferenceError):
        p.decide(*visible())
    assert p.usage_summary()["uncertain"] and len(calls) == 1
    assert "SENSITIVE-CREDENTIAL" not in p.journal.read_text()


@pytest.mark.parametrize(
    "usage",
    [
        None,
        {},
        {"prompt_tokens": True, "completion_tokens": 20, "total_tokens": 21},
        {"prompt_tokens": 500, "completion_tokens": 20, "total_tokens": 999},
    ],
)
def test_unknown_usage_is_not_zero_cost_success(tmp_path, usage):
    r = reply()
    r["usage"] = usage
    p, _ = provider(tmp_path, response=r)
    with pytest.raises(InferenceError, match="invalid_usage"):
        p.decide(*visible())
    assert p.usage_summary()["uncertain"]


def test_provider_exceeding_reserved_tokens_freezes(tmp_path):
    r = reply()
    r["usage"] = {"prompt_tokens": 500, "completion_tokens": 257, "total_tokens": 757}
    p, _ = provider(tmp_path, response=r)
    with pytest.raises(InferenceError, match="exceeded_token_reservation"):
        p.decide(*visible())
    assert p.usage_summary()["uncertain"]


@pytest.mark.parametrize(
    "where", ["task", "goal", "observation", "inputs", "control", "history", "action"]
)
def test_hidden_state_at_every_structured_depth_never_reaches_transport(tmp_path, where):
    task, obs, history = visible()
    history.append(
        {"action": {"kind": "read", "target": "Description", "value": ""}, "feedback": "completed"}
    )
    target = {
        "task": task,
        "goal": task["goals"][0],
        "observation": obs,
        "inputs": obs["inputs"],
        "control": obs["controls"][0],
        "history": history[0],
        "action": history[0]["action"],
    }[where]
    target["hidden_scheduler"] = {"future_oracle": "SECRET-SENTINEL"}
    p, calls = provider(tmp_path)
    with pytest.raises(InferenceError, match="invalid_public_input"):
        p.decide(task, obs, history)
    assert not calls and "SECRET-SENTINEL" not in p.journal.read_text()


def test_visible_wrapper_preserves_legacy_provider_and_rejects_hidden_input():
    class Legacy:
        evidence_kind = "test_policy"
        records = []

        def decide(self, *args):
            self.records.append(args)
            return "legacy-result"

    raw = Legacy()
    wrapped = VisiblePolicy(raw)
    assert wrapped.decide(*visible()) == "legacy-result"
    task, obs, history = visible()
    obs["oracle"] = True
    with pytest.raises(ValueError):
        wrapped.decide(task, obs, history)
    assert len(raw.records) == 1


def test_duplicate_request_does_not_erase_accounting(tmp_path):
    p, calls = provider(tmp_path)
    p.decide(*visible(), request_id="fixed")
    with pytest.raises(InferenceError, match="duplicate_request_id"):
        p.decide(*visible(), request_id="fixed")
    assert len(calls) == 1 and p.usage_summary()["known_total_tokens"] == 520
    assert p.usage_summary()["calls"] == 1


@pytest.mark.parametrize(
    "limits,category",
    [
        (Limits(max_calls=1), "request_budget_exhausted"),
        (Limits(max_total_tokens=8500), "token_budget_exhausted"),
    ],
)
def test_request_and_total_token_limits_persist_across_instances(tmp_path, limits, category):
    p, _ = provider(tmp_path, limits=limits)
    p.decide(*visible())
    again, calls = provider(tmp_path, limits=limits)
    with pytest.raises(InferenceError, match=category):
        again.decide(*visible())
    assert not calls


def test_wall_limit_and_pending_crash_record_fail_closed(tmp_path):
    timestamp = [1000.0]
    p, _ = provider(tmp_path, clock=lambda: timestamp[0])
    p.decide(*visible())
    timestamp[0] += 599
    with pytest.raises(InferenceError, match="wall_time_budget_exhausted"):
        p.decide(*visible())
    original = [json.loads(line) for line in p.journal.read_text().splitlines()][0]
    other = tmp_path / "crashed.jsonl"
    other.write_text(json.dumps(original) + "\n")
    crashed, calls = provider(tmp_path, journal=other)
    with pytest.raises(InferenceError, match="prior_completion_or_billing_unknown"):
        crashed.decide(*visible())
    assert not calls


def test_cache_provenance_config_key_and_recorded_input_matching(tmp_path):
    p, calls = provider(tmp_path, cache=True)
    p.decide(*visible())
    p.decide(*visible())
    assert len(calls) == 1 and p.records[-1]["evidence_kind"] == "cached_model_response"
    assert p.records[-1]["total_tokens"] == 0 and p.usage_summary()["cache_hits"] == 1
    modified = replace(p.config, model_revision="a-fixed-revision")
    other, new_calls = provider(
        tmp_path, config=modified, journal=tmp_path / "other.jsonl", cache=True
    )
    other.decide(*visible())
    assert len(new_calls) == 1
    replay = RecordedOpenAIPolicy(p.config, p.records[:1])
    assert replay.decide(*visible()).kind == "done"
    assert replay.records[-1]["evidence_kind"] == "recorded_model_responses"
    task, obs, history = visible()
    obs["text"] = "different"
    with pytest.raises(InferenceError, match="recorded_input_or_config_mismatch"):
        RecordedOpenAIPolicy(p.config, p.records[:1]).decide(task, obs, history)


def test_concurrency_is_one_across_instances(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def waiting(request):
        entered.set()
        assert release.wait(5)
        return httpx.Response(200, json=reply())

    first, calls = provider(tmp_path, handler=waiting)
    other, other_calls = provider(tmp_path)
    failures = []

    def work():
        try:
            first.decide(*visible())
        except Exception as exc:
            failures.append(exc)

    thread = threading.Thread(target=work)
    thread.start()
    try:
        assert entered.wait(5)
        with pytest.raises(InferenceError, match="concurrency_limit"):
            other.decide(*visible())
        with pytest.raises(InferenceError, match="concurrency_limit"):
            first.decide(*visible())
    finally:
        release.set()
        thread.join(5)
    assert not failures and len(calls) == 1 and not other_calls


def test_mock_cannot_network_and_live_requires_specific_approval(tmp_path):
    config = ModalConfig("https://test.us-west.modal.direct", "afterclick-test")
    with pytest.raises(ValueError, match="MockTransport"):
        ModalPolicy(config, Limits(), journal=tmp_path / "a")
    with pytest.raises(InferenceError, match="paid_approval_required"):
        ModalPolicy(config, Limits(max_usd=2), journal=tmp_path / "b", mode="live")
    with pytest.raises(ValueError, match="dedicated"):
        replace(config, endpoint_url="https://inference.us-west.modal.direct")


def test_click_must_match_visible_enabled_button(tmp_path):
    p, _ = provider(
        tmp_path, response=reply('{"kind":"click","target":"Delete workspace","value":""}')
    )
    with pytest.raises(InferenceError, match="action_target_not_visible_or_enabled"):
        p.decide(*visible())


@pytest.mark.parametrize(
    "fault", ["unapproved", "credits", "config", "limits", "expired", "rate", "nan"]
)
def test_paid_gate_rejects_mismatched_or_unverified_authorization(tmp_path, fault):
    from dataclasses import asdict

    config = ModalConfig("https://test.us-west.modal.direct", "afterclick-test")
    limits = Limits(max_usd=2)
    approval = {
        "approved_by_user": True,
        "run_id": "test-only-no-live-call",
        "config_sha256": config.fingerprint,
        "limits_sha256": digest(asdict(limits)),
        "max_usd": 2,
        "available_compute_credit_usd": 30,
        "credit_verified": True,
        "max_compute_usd_per_second": 0.001,
        "startup_allowance_seconds": 120,
        "shutdown_allowance_seconds": 30,
        "expires_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    if fault == "unapproved":
        approval["approved_by_user"] = False
    if fault == "credits":
        approval["credit_verified"] = False
    if fault == "config":
        approval["config_sha256"] = "changed"
    if fault == "limits":
        approval["limits_sha256"] = "changed"
    if fault == "expired":
        approval["expires_utc"] = "2020-01-01T00:00:00+00:00"
    if fault == "rate":
        approval["max_compute_usd_per_second"] = 0.009
    if fault == "nan":
        approval["available_compute_credit_usd"] = float("nan")
    path = tmp_path / "approval.json"
    path.write_text(json.dumps(approval))
    with pytest.raises(InferenceError):
        ModalPolicy(
            config, limits, journal=tmp_path / "live.jsonl", mode="live", approval_path=path
        )
    assert not (tmp_path / "live.jsonl").exists()


def test_context_admission_and_configuration_changes_fail_before_http(tmp_path):
    p, calls = provider(tmp_path)
    task, obs, history = visible()
    obs["text"] = "x" * 12000
    with pytest.raises(InferenceError, match="context_budget_exhausted"):
        p.decide(task, obs, history)
    assert not calls
    p.decide(*visible())
    changed, attempts = provider(tmp_path, config=replace(p.config, temperature=0.2))
    with pytest.raises(InferenceError, match="journal_configuration_mismatch"):
        changed.decide(*visible())
    assert not attempts


def test_interruption_during_request_is_persisted_as_unknown(tmp_path):
    def interrupt(request):
        raise KeyboardInterrupt()

    p, _ = provider(tmp_path, handler=interrupt)
    with pytest.raises(KeyboardInterrupt):
        p.decide(*visible())
    assert p.records[-1]["status"] == "failed" and p.usage_summary()["uncertain"]
    again, attempts = provider(tmp_path)
    with pytest.raises(InferenceError, match="prior_completion_or_billing_unknown"):
        again.decide(*visible())
    assert not attempts


def test_echoed_auth_is_redacted_in_journal_and_embedded_branch_records(tmp_path):
    def echo(request):
        data = reply()
        data["diagnostic_echo"] = request.headers["Authorization"]
        return httpx.Response(200, json=data)

    p, _ = provider(tmp_path, handler=echo)
    p.decide(*visible())
    assert "MOCK-NOT-A-CREDENTIAL" not in p.journal.read_text()
    assert "MOCK-NOT-A-CREDENTIAL" not in json.dumps(p.records)
    assert "[REDACTED]" in json.dumps(p.records)
