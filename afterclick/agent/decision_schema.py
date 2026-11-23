"""Faithful generation schema for conditional arguments; runtime Decision stays unchanged."""

from typing import Literal, Union

from pydantic import Field, TypeAdapter

from afterclick.agent.action_parser import Decision


class Read(Decision):
    kind: Literal["read"]
    target: Literal["Description", "Comment", "Status", "Priority", "Assignee"]
    value: Literal[""]


class Done(Decision):
    kind: Literal["done"]
    target: Literal[""]
    value: Literal[""]


class Navigate(Decision):
    kind: Literal["navigate"]
    target: Literal["/"]
    value: Literal[""]


class Click(Decision):
    kind: Literal["click"]
    target: str = Field(min_length=1, max_length=200)
    value: Literal[""]


class Wait(Decision):
    kind: Literal["wait"]
    target: Literal["✓ Committed", "Failed", "Conflict"]
    value: Literal[""]


class Fill(Decision):
    kind: Literal["fill"]
    target: Literal["Description", "Comment"]
    value: str = Field(max_length=4000)


class SelectStatus(Decision):
    kind: Literal["select"]
    target: Literal["Status"]
    value: Literal["Backlog", "In progress", "Done"]


class SelectPriority(Decision):
    kind: Literal["select"]
    target: Literal["Priority"]
    value: Literal["Normal", "High", "Critical"]


class SelectAssignee(Decision):
    kind: Literal["select"]
    target: Literal["Assignee"]
    value: Literal["Maya", "Alex", "Jordan"]


CONDITIONAL = TypeAdapter(
    Union[Read, Done, Navigate, Click, Wait, Fill, SelectStatus, SelectPriority, SelectAssignee]
)


def conditional_schema():
    return {"type": "object", **CONDITIONAL.json_schema()}


ARGUMENT_INSTRUCTIONS = """
Argument rules are mandatory: value is the empty string for read, click, wait,
navigate and done. Only fill and select may carry text in value. A read requests
the Gateway to read a field; do not put the field's observed text in value.
Example: {"kind":"read","target":"Description","value":""}.
Example: {"kind":"done","target":"","value":""}.
"""
