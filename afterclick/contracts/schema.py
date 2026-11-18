from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BUSINESS_FIELDS = {
    "tasks": ("title", "description", "reviewed", "ready", "priority", "assignee", "status"),
    "projects": ("name", "completed"),
}


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Predicate(ContractModel):
    table: Literal["tasks", "projects"]
    record_id: str = Field(min_length=1)
    field: str
    operator: Literal["equals", "contains"] = "equals"
    value: str | int | bool

    @model_validator(mode="after")
    def validate_field(self):
        if self.field not in BUSINESS_FIELDS[self.table]:
            raise ValueError("Predicate must select a supported business field")
        if self.operator == "contains" and not isinstance(self.value, str):
            raise ValueError("contains requires text")
        return self


class EffectScope(ContractModel):
    kind: str
    resource: str = "*"
    fields: tuple[str, ...] = ()
    actor: str = "*"


class ActionScope(ContractModel):
    record_id: str
    field: Literal["reviewed", "priority", "status"]


class TaskContract(ContractModel):
    schema_version: Literal["1"] = "1"
    contract_id: str
    fixture_version: str
    workflow_family: str
    instruction: str
    initial_fixture: str
    seed: int
    goals: tuple[Predicate, ...] = Field(min_length=1)
    authorized_effects: tuple[EffectScope, ...]
    forbidden_history: tuple[EffectScope, ...]
    selected_action: ActionScope
    horizon: int = Field(ge=0)
    supported_compensations: tuple[
        Literal[
            "cancel_pending", "restore_owned_field", "delete_owned_derived", "restore_owned_summary"
        ],
        ...,
    ]
    preserve_all_independent_changes: Literal[True] = True
    preserve_audit_history: Literal[True] = True
    actor_roles: dict[str, str]


def load_contract(path: str | Path) -> TaskContract:
    return TaskContract.model_validate_json(Path(path).read_text())
