import json

import httpx
import pytest

from afterclick.agent.action_parser import parse_action
from afterclick.agent.browser_observation import public_history, public_task
from afterclick.agent.llm_policy import Budget, GeminiPolicy, PolicyError
from afterclick.contracts.schema import load_contract


@pytest.mark.parametrize(
    "value",
    [
        '{"kind":"click","target":"Post","value":"","oracle":true}',
        '{"kind":"navigate","target":"https://example.com","value":""}',
        '{"kind":"fill","target":"Priority","value":"Critical"}',
        '{"kind":"select","target":"Status","value":"Deleted"}',
        '{"kind":"done","kind":"read","target":"Description","value":""}',
        '```json\n{"kind":"done","target":"","value":""}\n```',
        '{"kind":"evaluate","target":"alert(1)","value":""}',
    ],
)
def test_rejects_unsafe_or_ambiguous_actions(value):
    with pytest.raises(ValueError):
        parse_action(value)


def test_model_input_allowlist():
    contract = load_contract("fixtures/tasks/review-readiness-v2.json")
    assert set(public_task(contract)) == {"instruction", "goals"}
    assert public_task(contract) == public_task(
        contract.model_copy(update={"seed": 4321, "horizon": 9999})
    )
    action = {"kind": "click", "target": "Mark reviewed", "value": ""}
    assert public_history(
        [
            {
                "action": action,
                "feedback": {"status": "failed", "error": "secret"},
                "oracle": "secret",
                "intervention": "lost_ack",
                "action_id": "secret",
            }
        ]
    ) == [{"action": action, "feedback": "failed"}]


def provider(reply=None, *, http_status=200, budget=None):
    calls = []
    response = {
        "modelVersion": "gemini-3.1-flash-lite",
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {"parts": [{"text": '{"kind":"done","target":"","value":""}'}]},
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 1000,
            "candidatesTokenCount": 20,
            "thoughtsTokenCount": 10,
            "totalTokenCount": 1030,
        },
    }
    if reply is not None:
        response = reply

    def handle(request):
        calls.append(request)
        if request.url.path.endswith(":countTokens"):
            return httpx.Response(200, json={"totalTokens": 1000})
        return httpx.Response(http_status, json=response)

    policy = GeminiPolicy(
        "TEST-CREDENTIAL",
        budget or Budget(),
        client=httpx.Client(transport=httpx.MockTransport(handle)),
    )
    return policy, calls


def test_exact_requests_usage_and_no_secret_in_artifacts(tmp_path):
    policy, calls = provider()
    policy.journal = tmp_path / "calls.jsonl"
    assert policy.decide({"instruction": "Finish"}, {}, []).kind == "done"
    assert len(calls) == 2
    assert policy.budget.spent_usd == pytest.approx(0.000295)
    assert policy.budget.reserved_usd == pytest.approx(0)
    records = policy.journal.read_text()
    assert "TEST-CREDENTIAL" not in records
    assert "thoughtsTokenCount" in records and "systemInstruction" in records
    assert json.loads(records.splitlines()[0])["status"] == "pending"
    assert json.loads(records.splitlines()[1])["status"] == "completed"


@pytest.mark.parametrize("reason", ["missing_usage", "transport_status", "inconsistent_usage"])
def test_uncertain_charge_stops_subsequent_generation(reason):
    reply = {
        "usageMetadata": {
            "promptTokenCount": 1000,
            "candidatesTokenCount": 10,
            "totalTokenCount": 999,
        }
    }
    policy, calls = provider(
        reply={} if reason == "missing_usage" else reply,
        http_status=503 if reason == "transport_status" else 200,
    )
    with pytest.raises(PolicyError):
        policy.decide({}, {}, [])
    assert policy.budget.uncertain
    assert policy.budget.reserved_usd > 0
    with pytest.raises(PolicyError):
        policy.decide({}, {}, [])
    assert len([c for c in calls if c.url.path.endswith(":generateContent")]) == 1


def test_budget_refuses_before_generation():
    policy, calls = provider(budget=Budget(ceiling_usd=0.00001))
    with pytest.raises(PolicyError, match="budget"):
        policy.decide({}, {}, [])
    assert len(calls) == 1
    assert policy.budget.calls == 0


def test_invalid_completion_is_charged_and_retained():
    policy, calls = provider()
    original = policy._post

    def invalid(method, payload):
        reply = original(method, payload)
        if method == "generateContent":
            reply["candidates"][0]["content"]["parts"][0]["text"] = '{"kind":"shell"}'
        return reply

    policy._post = invalid
    with pytest.raises(ValueError):
        policy.decide({}, {}, [])
    assert policy.budget.spent_usd > 0 and not policy.budget.uncertain
    assert policy.records[-1]["status"] == "failed"


def test_opaque_signature_does_not_reject_text():
    policy, _ = provider()
    original = policy._post

    def signed(method, payload):
        reply = original(method, payload)
        if method == "generateContent":
            reply["candidates"][0]["content"]["parts"][0]["thoughtSignature"] = "opaque"
        return reply

    policy._post = signed
    assert policy.decide({}, {}, []).kind == "done"


def test_recorded_policy_requires_exact_observation_and_prompt():
    from copy import deepcopy

    from afterclick.agent.llm_policy import RecordedPolicy

    policy, _ = provider()
    policy.decide({"instruction": "Finish"}, {"text": "visible"}, [])
    record = policy.records[0]
    replay = RecordedPolicy([record])
    assert replay.decide({"instruction": "Finish"}, {"text": "visible"}, []).kind == "done"
    with pytest.raises(PolicyError, match="input mismatch"):
        RecordedPolicy([record]).decide({"instruction": "Finish"}, {"text": "different"}, [])
    changed = deepcopy(record)
    changed["request"]["systemInstruction"]["parts"][0]["text"] = "different"
    with pytest.raises(PolicyError, match="prompt mismatch"):
        RecordedPolicy([changed]).decide({"instruction": "Finish"}, {"text": "visible"}, [])
