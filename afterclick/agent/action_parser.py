"""Strict, bounded browser decisions; model text is never executable code."""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from afterclick.agent.gateway import Action


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    kind: Literal["navigate", "fill", "click", "select", "read", "wait", "done"]
    target: str = Field(max_length=200)
    value: str = Field(max_length=4000)

    @model_validator(mode="after")
    def bounded(self):
        if self.kind == "done" and (self.target or self.value):
            raise ValueError("done requires empty target and value")
        if self.kind == "navigate" and self.target != "/":
            raise ValueError("Only fixture home navigation is permitted")
        if self.kind in {"fill", "read"} and self.target not in {
            "Description",
            "Comment",
            "Status",
            "Priority",
            "Assignee",
        }:
            raise ValueError("Unknown input label")
        if self.kind == "fill" and self.target not in {"Description", "Comment"}:
            raise ValueError("Use select for dropdowns")
        options = {
            "Status": {"Backlog", "In progress", "Done"},
            "Priority": {"Normal", "High", "Critical"},
            "Assignee": {"Maya", "Alex", "Jordan"},
        }
        if self.kind == "select" and self.value not in options.get(self.target, set()):
            raise ValueError("Unknown dropdown option")
        if self.kind == "click" and not self.target:
            raise ValueError("Button name required")
        if self.kind == "wait" and self.target not in {"✓ Committed", "Failed", "Conflict"}:
            raise ValueError("Unsupported wait state")
        if self.kind not in {"fill", "select"} and self.value:
            raise ValueError("Unexpected action value")
        return self

    def action(self):
        if self.kind == "done":
            raise ValueError("done is a policy termination, not a browser action")
        return Action(self.kind, self.target, self.value)


def parse_action(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    if not isinstance(text, str) or len(text) > 8000:
        raise ValueError("Oversized or non-text action")
    return Decision.model_validate(json.loads(text, object_pairs_hook=unique))
