import copy
import json
import time

import pytest

from afterclick.completion_v12.benchmark.transport import Transport, model_public


def public():
    return dict(
        application="OpsConsole",
        instruction="Complete scoped work",
        policy=[],
        service=dict(authority="approved"),
        records=[
            dict(
                id="w00",
                label="Reconcile",
                kind="record",
                dependencies=[],
                role=None,
                scope_rule="primary",
                choices=["internal", "external"],
                stage="open",
                value="unselected",
                version=1,
            )
        ],
    )


def test_native_tool_ids_history_and_current_dynamic_state_survive_next_turn(tmp_path):
    captured = []

    def generate(episode, role, payload):
        captured.append(copy.deepcopy(payload))
        return dict(
            role="assistant",
            content="",
            tool_calls=[
                dict(
                    id=f"actual-{len(captured)}",
                    type="function",
                    function=dict(name="browser_state", arguments="{}"),
                )
            ],
        ), f"request-{len(captured)}"

    transport = Transport(
        tmp_path / "trace",
        "https://invalid.example",
        "fixture",
        deadline=time.monotonic() + 120,
        max_calls=3,
    )
    transport.generate = generate
    state = public()
    transport.actor("source", state, [])
    state["records"][0].update(stage="complete", value="internal", version=2)
    transport.actor("source", state, [dict(tool="browser_state", result=state)])
    messages = captured[-1]["messages"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool"]
    assert messages[-2]["tool_calls"][0]["id"] == messages[-1]["tool_call_id"] == "actual-1"
    tool = json.loads(messages[-1]["content"])
    assert tool["batch_current_public"]["current_records"]["rows"][0][1] == "complete"
    assert "record_definitions" not in tool["batch_current_public"]
    assert "record_definitions" in json.loads(messages[1]["content"])["public"]
    assert captured[-1]["tool_choice"] == "auto"


def test_unexpected_oracle_field_cannot_cross_actor_observation_boundary():
    with pytest.raises(ValueError, match="public observation boundary"):
        model_public({**public(), "private": {"expected_choice": "internal"}})
