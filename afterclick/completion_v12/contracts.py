"""Task-contract validation and fail-closed benchmark enrollment.

The kit's design-slot CSVs are never counted as authored executable tasks.
The bundled schema uses a deliberately small JSON Schema vocabulary checked
here without adding dependencies to historical locked environments.
"""

import json
from pathlib import Path

from afterclick.completion_v12.evidence import digest

KIT = Path("research_ops/completion_v12")


def schema_check(schema, value, location="$", *, check_vocabulary=True):
    supported = {
        "$schema",
        "title",
        "type",
        "enum",
        "required",
        "properties",
        "items",
        "additionalProperties",
        "minLength",
        "minItems",
        "minimum",
    }
    if check_vocabulary and not schema.keys() <= supported:
        raise ValueError("Unsupported schema keyword")
    types = schema.get("type")
    allowed = [types] if isinstance(types, str) else types
    validators = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "integer": lambda x: type(x) is int,
        "boolean": lambda x: type(x) is bool,
        "null": lambda x: x is None,
    }
    if allowed and not any(validators[t](value) for t in allowed):
        raise ValueError(location + ": incorrect type")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(location + ": outside enum")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            raise ValueError(location + ": missing " + str(sorted(missing)))
        props = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in props:
                schema_check(props[key], item, location + "." + key)
            elif additional is False:
                raise ValueError(location + ": unknown field " + key)
            elif isinstance(additional, dict):
                schema_check(additional, item, location + "." + key)
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValueError(location + ": too few items")
        for i, item in enumerate(value):
            schema_check(schema.get("items", {}), item, f"{location}[{i}]")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        raise ValueError(location + ": string too short")
    if type(value) is int and value < schema.get("minimum", value):
        raise ValueError(location + ": below minimum")


def structure(contract):
    obligations = contract["private"]["obligations"]
    nodes = {o["obligation_id"]: o for o in obligations}
    if len(nodes) != len(obligations):
        raise ValueError("Duplicate obligation ID")
    depths, active = {}, set()

    def visit(key):
        if key not in nodes:
            raise ValueError("Unknown obligation dependency: " + key)
        if key in active:
            raise ValueError("Obligation cycle")
        if key not in depths:
            active.add(key)
            depths[key] = 1 + max([visit(d) for d in nodes[key]["dependencies"]], default=0)
            active.remove(key)
        return depths[key]

    for key in nodes:
        visit(key)
    # Name-invariant graph coloring is a conservative duplicate flag, not an isomorphism proof.
    colors = {
        k: digest([len(n["dependencies"]), sum(k in o["dependencies"] for o in obligations)])
        for k, n in nodes.items()
    }
    for _ in nodes:
        colors = {
            k: digest([colors[k], sorted(colors[d] for d in n["dependencies"])])
            for k, n in nodes.items()
        }
    return dict(
        dependency_depth=max(depths.values()),
        obligations=len(nodes),
        graph_fingerprint=digest(sorted(colors.values())),
    )


def validate(contract):
    schema_check(json.loads((KIT / "templates/task_contract.schema.json").read_text()), contract)
    metrics = structure(contract)
    if (
        contract.get("structure_metrics", {}).get("dependency_depth", metrics["dependency_depth"])
        != metrics["dependency_depth"]
    ):
        raise ValueError("Declared dependency depth disagrees with obligation DAG")
    return metrics


def public_projection(contract):
    validate(contract)
    return contract["public"]
