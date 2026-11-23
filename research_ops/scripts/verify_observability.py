"""Read-only verification of both preserved studies and delivered figures. No network/model load."""

import argparse
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(root):
    base = root / "artifacts/research_runs"
    checked = 0
    bad = []
    seals = list(base.glob("*/checksums.json"))
    for seal in seals:
        for name, h in json.loads(seal.read_text())["file_sha256"].items():
            p = seal.parent / name
            checked += 1
            if not p.is_file() or sha(p) != h:
                bad.append(str(p))
    for freeze, groups in [
        ("p6-risk-study-v1/FROZEN.json", ["code_hashes", "artifact_hashes"]),
        ("o1-observability-development-v1/FROZEN.json", ["source_hashes", "artifact_hashes"]),
    ]:
        d = json.loads((base / freeze).read_text())
        for group in groups:
            for name, h in d[group].items():
                p = root / name
                checked += 1
                if not p.is_file() or sha(p) != h:
                    bad.append(name)
    for original, delivered in [
        ("p10-synthesis-v1/figures/generated-final", "paper/generated"),
        ("o5-observability-synthesis-v1/figures/generated-final", "paper/observability-generated"),
    ]:
        for p in (base / original).iterdir():
            target = root / delivered / p.name
            checked += 1
            if not target.is_file() or sha(p) != sha(target):
                bad.append(str(target))
    for run in base.iterdir():
        if run.is_dir() and not (run / "checksums.json").exists():
            bad.append("Unsealed " + run.name)
    marker = json.loads((base / "o2-observability-locked-v1/raw/holdout-opened.json").read_text())
    if marker["freeze_sha256"] != sha(base / "o1-observability-development-v1/FROZEN.json"):
        bad.append("New freeze differs from once-only opening marker")
    result = dict(
        schema_version=1,
        sealed_runs=len(seals),
        checked_files=checked,
        mismatches=bad,
        passed=not bad,
        mode="read_only_no_network_no_model_loading",
    )
    print(json.dumps(result, indent=2))
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    verify(p.parse_args().root.resolve())
