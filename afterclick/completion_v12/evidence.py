"""Content-addressed raw-record references, checked independently of graph construction."""

import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class EvidenceStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.cache = {}

    def path(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError("Missing or out-of-root evidence: " + str(relative))
        return path

    def read(self, relative):
        if relative not in self.cache:
            path = self.path(relative)
            data = path.read_bytes()
            value = (
                [json.loads(line) for line in data.splitlines() if line.strip()]
                if path.suffix == ".jsonl"
                else json.loads(data)
            )
            self.cache[relative] = (hashlib.sha256(data).hexdigest(), value)
        return self.cache[relative][1]

    def reference(self, relative, *pointer):
        value = self.read(relative)
        for part in pointer:
            value = value[part]
        return dict(
            path=relative,
            file_sha256=self.cache[relative][0],
            pointer=list(pointer),
            value_sha256=digest(value),
        )

    def resolve(self, ref):
        # Fresh stores are used for independent verification, never a builder's cache.
        value = self.read(ref["path"])
        if self.cache[ref["path"]][0] != ref["file_sha256"]:
            raise ValueError("Raw evidence file changed: " + ref["path"])
        for part in ref["pointer"]:
            value = value[part]
        if digest(value) != ref["value_sha256"]:
            raise ValueError("Raw evidence record changed: " + ref["path"])
        return value


def historical_audit(root, output):
    """Verify the pre-v12 cohort without treating an active v12 run as sealed evidence."""
    root, output = Path(root), Path(output)
    paths = sorted((root / "artifacts/research_runs").glob("*/checksums.json"))
    paths = [p for p in paths if not p.parent.name.startswith("v12-")]
    errors, checked = [], 0
    for seal in paths:
        for relative, expected in json.loads(seal.read_text())["file_sha256"].items():
            p = (seal.parent / relative).resolve()
            checked += 1
            if not p.is_relative_to(seal.parent.resolve()) or not p.is_file() or sha(p) != expected:
                errors.append(str(p))
    result = dict(
        schema_version=1,
        historical_run_ids=[p.parent.name for p in paths],
        seals={str(p.relative_to(root)): sha(p) for p in paths},
        checked_files=checked,
        mismatches=errors,
        passed=not errors,
        scope=(
            "Pre-v12 sealed raw evidence; source freezes checked by original verifiers separately"
        ),
    )
    output.write_text(json.dumps(result, indent=2) + "\n")
    if errors:
        raise ValueError("Historical evidence mismatch")
    return result
