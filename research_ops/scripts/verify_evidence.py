"""Read-only checksum, freeze and delivered figure verification; no model loading or network."""

import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    runs = root / "artifacts/research_runs"
    if not runs.is_dir():
        raise ValueError("Unpack the local evidence archive at the repository root first")
    checked, errors, seals = 0, [], 0
    for seal in sorted(runs.glob("*/checksums.json")):
        seals += 1
        record = json.loads(seal.read_text())
        for name, expected in record["file_sha256"].items():
            path = seal.parent / name
            checked += 1
            if not path.is_file() or sha(path) != expected:
                errors.append(str(path.relative_to(root)))
    frozen = json.loads((runs / "p6-risk-study-v1/FROZEN.json").read_text())
    for group in ["code_hashes", "artifact_hashes"]:
        for name, expected in frozen[group].items():
            path = root / name
            checked += 1
            if not path.is_file() or sha(path) != expected:
                errors.append(str(path.relative_to(root)))
    generated = runs / "p10-synthesis-v1/figures/generated-final"
    for file in generated.iterdir():
        delivered = root / "paper/generated" / file.name
        checked += 1
        if not delivered.is_file() or sha(file) != sha(delivered):
            errors.append(str(delivered.relative_to(root)))
    for run in runs.iterdir():
        if run.is_dir() and not (run / "checksums.json").exists():
            errors.append(f"Unsealed run: {run.name}")
    result = dict(
        schema_version=1,
        sealed_runs=seals,
        checked_files=checked,
        mismatches=errors,
        passed=not errors,
        mode="read_only_no_network_no_model_loading",
    )
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    verify(parser.parse_args().root.resolve())
