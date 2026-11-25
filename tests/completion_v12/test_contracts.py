import copy
import json

import pytest

from afterclick.completion_v12.contracts import (
    KIT,
    public_projection,
    schema_check,
    validate,
    verify_kit,
)


def test_supplied_kit_remains_intact_and_example_is_not_a_qualified_task():
    assert verify_kit()["passed"]
    example = json.loads((KIT / "templates/task_contract_example.json").read_text())
    # The illustrative example declares depth 4, but its four-node graph has depth 3.
    # Do not silently accept the example's self-reported complexity as a measurement.
    with pytest.raises(ValueError, match="dependency depth"):
        validate(example)
    example.pop("structure_metrics")
    assert validate(example)["dependency_depth"] == 3
    assert example["authoring_status"] == "design_example"
    assert "private" not in public_projection(example)


def test_missing_obligation_dependencies_and_cycles_fail_closed():
    example = json.loads((KIT / "templates/task_contract_example.json").read_text())
    example.pop("structure_metrics")
    for dependencies in [["missing"], ["handoff_record"]]:
        c = copy.deepcopy(example)
        c["private"]["obligations"][-1]["dependencies"] = dependencies
        with pytest.raises(ValueError):
            validate(c)


def test_schema_never_accepts_booleans_as_integer_seeds_or_silently_ignores_keywords():
    with pytest.raises(ValueError):
        schema_check({"type": "integer"}, True)
    with pytest.raises(ValueError, match="Unsupported"):
        schema_check({"type": "string", "unimplementedConstraint": 1}, "value")
