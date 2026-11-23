import json

import pytest

from afterclick.agent.action_parser import Decision
from afterclick.contracts.schema import load_contract
from afterclick.replay.adaptive_runner import run_case


class ObservableTestPolicy:
    """Explicit test double, never live-LLM evidence. Only responds to public UI state."""

    evidence_kind = "test_policy"

    def __init__(self):
        self.records = []

    def decide(self, task, observation, history):
        self.records.append({"task": task, "observation": observation, "history": history})
        if observation["save_status"] == "Failed":
            return Decision(kind="click", target="Retry save", value="")
        if "API v2" not in observation["inputs"]["Description"]:
            return Decision(kind="fill", target="Description", value="Document API v2 integration.")
        return Decision(kind="done", target="", value="")


@pytest.mark.browser
@pytest.mark.parametrize(
    "fixture", ["review-readiness-v2", "priority-escalation-v1", "status-summary-v1"]
)
def test_adaptive_placebos_lost_ack_and_hidden_state_boundary(browser, tmp_path, fixture):
    policy = ObservableTestPolicy()
    contract = load_contract(f"fixtures/tasks/{fixture}.json")
    result = run_case(browser, contract, policy, tmp_path)
    assert result["certificate"]["valid"], json.dumps(result["certificate"])
    assert all(b["task"]["success"] for b in result["branches"].values())
    branches = result["branches"]
    assert branches["lost_ack"]["steps"][0]["decision"]["target"] == "Retry save"
    assert len(branches["lost_ack"]["state"]["operations"]) == 2
    assert (
        branches["execute"]["state"]["tasks"][0]["version"]
        == branches["lost_ack"]["state"]["tasks"][0]["version"]
    )
    for record in policy.records:
        assert set(record["task"]) == {"instruction", "goals"}
        assert set(record["observation"]) == {"text", "inputs", "controls", "save_status"}
        for action in record["history"]:
            assert set(action) == {"action", "feedback"}
    assert result["comparison"]["intervention_supported"]["suppress_adaptive"]["semantic_effects"][
        "only_left"
    ]
    assert not result["comparison"]["intervention_supported"]["lost_ack"]["semantic_effects"][
        "only_left"
    ]
