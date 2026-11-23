"""Provider-independent, visible-only policy boundary (no database/oracle imports)."""

import json
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from afterclick.agent.action_parser import Decision


class Policy(Protocol):
    evidence_kind: str
    records: list

    def decide(self, task: dict, observation: dict, history: list) -> Decision: ...


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Goal(PublicModel):
    table: Literal["tasks", "projects"]
    record_id: str
    field: str
    operator: Literal["contains", "equals"]
    value: str | int | bool


class Task(PublicModel):
    instruction: str = Field(max_length=8000)
    goals: list[Goal] = Field(max_length=20)


class Inputs(PublicModel):
    Description: str
    Status: str
    Priority: str
    Assignee: str
    Comment: str


class Control(PublicModel):
    role: Literal["input", "button"]
    name: str
    value: str | None = None
    enabled: bool


class Observation(PublicModel):
    text: str
    inputs: Inputs
    controls: list[Control]
    save_status: str


class Action(PublicModel):
    # Gateway.history omits value on read/click? Accept its exact three-field vocabulary.
    kind: Literal["navigate", "fill", "click", "select", "read", "wait"]
    target: str
    value: str = ""


class HistoryEntry(PublicModel):
    action: Action
    feedback: Literal["completed", "failed", "suppressed"]


def public_input(task, observation, history):
    """Reject extra fields at every structured level; never log invalid supplied values.

    Values of visible text are untrusted page data. Schema validation cannot establish
    where a caller obtained text; the observation constructor remains the trust boundary.
    """
    Task.model_validate(task)
    Observation.model_validate(observation)
    if not isinstance(history, list) or len(history) > 50:
        raise ValueError("Bounded public history required")
    for entry in history:
        HistoryEntry.model_validate(entry)
    payload = {"task": task, "observation": observation, "history": history}
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False)
    if len(serialized.encode()) > 32000:
        raise ValueError("Public context exceeds bounded size")
    return json.loads(serialized)


class VisiblePolicy:
    """Optional boundary for legacy Gemini/test/recorded providers; prompts stay identical."""

    def __init__(self, policy):
        self.policy = policy

    def __getattr__(self, name):
        return getattr(self.policy, name)

    @property
    def journal(self):
        return self.policy.journal

    @journal.setter
    def journal(self, value):
        self.policy.journal = value

    def decide(self, task, observation, history):
        public_input(task, observation, history)
        return self.policy.decide(task, observation, history)
