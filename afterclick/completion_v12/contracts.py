"""Task-contract validation and fail-closed benchmark enrollment.

The kit's design-slot CSVs are never counted as authored executable tasks.
The bundled schema uses a deliberately small JSON Schema vocabulary checked
here without adding dependencies to historical locked environments.
"""

import csv
import json
import re
from collections import Counter
from pathlib import Path

from afterclick.completion_v12.evidence import digest, sha

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


def enrollment(root=Path.cwd()):
    root = Path(root)
    tasks_dir = root / KIT / "tasks"
    tasks = {}
    for path in sorted(tasks_dir.glob("*.json")):
        c = json.loads(path.read_text())
        metrics = validate(c)
        if c["task_id"] in tasks:
            raise ValueError("Duplicate task ID")
        tasks[c["task_id"]] = (path, c, metrics)
    rows, qualified = [], []
    for name in ("task_design_slots_216.csv", "task_design_slots_72_dev.csv"):
        with (root / KIT / "manifests" / name).open() as stream:
            for slot in csv.DictReader(stream):
                key = slot["slot_id"]
                row = dict(task_id=key, split=slot["split"], status="NOT_AUTHORED")
                if key in tasks:
                    path, c, metrics = tasks[key]
                    row.update(
                        status="AUTHORED_UNQUALIFIED",
                        path=str(path.relative_to(root)),
                        sha256=sha(path),
                        metrics=metrics,
                    )
                    if c["reference_plan"]["verified"] and c["authoring_status"] in {
                        "validated",
                        "frozen",
                    }:
                        cert = c["reference_plan"].get("certificate_path")
                        if cert is None or not (root / cert).is_file():
                            raise ValueError(
                                "Verified witness has no executable evidence certificate"
                            )
                        row.update(
                            status="WITNESS_RECORDED_REVIEW_PENDING",
                            certificate_sha256=sha(root / cert),
                        )
                    qualified.append(row)
                rows.append(row)
    unknown = set(tasks) - {r["task_id"] for r in rows}
    if unknown:
        raise ValueError("Authored tasks lack a design slot: " + str(unknown))
    return dict(
        schema_version=1,
        counts=dict(Counter(r["status"] for r in rows)),
        rows=rows,
        test_freeze_eligible=False,
        meaning="Witnesses alone do not qualify complete cohort, split diversity, DEV or power",
    )


def verify_kit():
    errors = []
    for line in (KIT / "KIT_SHA256SUMS.txt").read_text().splitlines():
        expected, name = re.split(r"\s+", line, maxsplit=1)
        if sha(KIT / name) != expected:
            errors.append(name)
    if errors:
        raise ValueError("Supplied specification changed: " + str(errors))
    return dict(checked=22, passed=True)
