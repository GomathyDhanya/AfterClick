"""Read-only admission checks for immutable v12 TEST assignments."""

import json
from pathlib import Path

from afterclick.completion_v12.evidence import digest, sha


def read(path):
    return json.loads(Path(path).read_text())


def admit(protocol, registration):
    path = Path(protocol["freeze_path"])
    assert sha(path) == protocol["freeze_sha256"], "Changed frozen protocol"
    freeze = read(path)
    assert freeze["status"] == "FROZEN_BEFORE_TEST"
    assert freeze["test_contract_count"] == 216 and freeze["dev_contract_count"] == 72
    for name, expected in freeze["source_hashes"].items():
        assert sha(Path(name)) == expected, "Changed frozen source: " + name
    for name, expected in freeze["gate_hashes"].items():
        assert sha(Path(name)) == expected, "Changed qualification evidence: " + name
    model = freeze["models"][registration["model_tag"]]
    assert protocol["model"] == model["repo_id"]
    assert protocol["revision"] == model["revision"]
    assert protocol["endpoint_id"] == model["endpoint_id"]
    manifest_path = Path(freeze["manifests"][registration["model_tag"]]["path"])
    assert sha(manifest_path) == freeze["manifests"][registration["model_tag"]]["sha256"]
    manifest = read(manifest_path)
    cells = {cell["episode_id"]: cell for cell in manifest["episodes"]}
    requested = [cell["episode_id"] for cell in registration["episodes"]]
    assert len(requested) == len(set(requested)), "Duplicate assignment in job"
    for cell in registration["episodes"]:
        assert cell == cells[cell["episode_id"]], "Modified or unregistered TEST assignment"
    assert registration["limits"] == freeze["limits"]
    for identifier, entry in registration["contracts"].items():
        assert identifier.startswith("TEST-")
        assert sha(Path(entry["path"])) == freeze["contracts"][identifier]["sha256"]
        assert digest(read(entry["path"])) == entry["digest"]
    assert set(c["task_id"] for c in registration["episodes"]) == set(registration["contracts"])
    return freeze
