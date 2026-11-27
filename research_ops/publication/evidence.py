"""Fail-closed compact evidence verification, with no model or application imports."""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root=ROOT):
    root = Path(root)
    index = json.loads((root / "evidence/index.json").read_text())
    for name, entry in index["files"].items():
        path = (root / "evidence" / name).resolve()
        assert path.is_relative_to((root / "evidence").resolve()), name
        assert sha(path) == entry["sha256"], name
    registry = json.loads((root / "paper/claim_registry.json").read_text())
    for entry in registry.values():
        source = root / "evidence/publication" / entry["source"]
        assert source.resolve().is_relative_to((root / "evidence").resolve())
        assert sha(source) == entry["source_sha256"], entry["source"]
        if source.suffix == ".json":
            value = json.loads(source.read_text())
            for part in entry["pointer"].split("/")[1:]:
                value = (
                    value[int(part)]
                    if isinstance(value, list)
                    else value[part.replace("~1", "/").replace("~0", "~")]
                )
    matrix = list(csv.DictReader((root / "evidence/claim_evidence_matrix.csv").open()))
    for entry in matrix:
        assert (root / entry["evidence"]).resolve().is_relative_to((root / "evidence").resolve())
        assert sha(root / entry["evidence"]) == entry["sha256"], entry["id"]
    report = {
        "compact_files_verified": len(index["files"]),
        "claim_registry_entries_verified": len(registry),
        "claim_matrix_rows_verified": len(matrix),
        "model_calls": 0,
        "provider_calls": 0,
        "raw_evidence_verified": False,
    }
    print(json.dumps(report))
    return report
