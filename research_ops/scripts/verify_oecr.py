"""Read-only historical seals and current confirmation source verification."""

import argparse
import hashlib
import json
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(output):
    checked = 0
    errors = []
    sealed = 0
    for seal in Path("artifacts/research_runs").glob("*/checksums.json"):
        value = json.loads(seal.read_text())
        sealed += 1
        for rel, expected in value["file_sha256"].items():
            p = seal.parent / rel
            checked += 1
            if not p.exists() or sha(p) != expected:
                errors.append(str(p))
    for file in [
        "research_ops/TCOPE_FINAL_FREEZE.json",
        "research_ops/OECR_CONFIRMATION_FREEZE.json",
    ]:
        for name, expected in json.loads(Path(file).read_text())["source_hashes"].items():
            if sha(Path(name)) != expected:
                errors.append(name)
    result = dict(
        schema_version=1,
        sealed_runs=sealed,
        checked_paths=checked,
        mismatches=errors,
        passed=not errors,
    )
    atomic_json(output, result)
    if errors:
        raise SystemExit("Frozen evidence mismatch")
    print(json.dumps(result))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    verify(p.parse_args().output)
