"""Restore the exact historical source and optionally its separately supplied raw data."""

import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore(output, archives=()):
    record = json.loads((ROOT / "archive/SNAPSHOTS.json").read_text())
    commit = record["source_commit"]
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    # git archive exports tracked bytes/modes only; no current worktree changes.
    process = subprocess.Popen(["git", "-C", str(ROOT), "archive", commit], stdout=subprocess.PIPE)
    with tarfile.open(fileobj=process.stdout, mode="r|") as source:
        source.extractall(output, filter="data")
    assert process.wait() == 0
    for archive in archives:
        expected = next(a for a in record["assets"] if Path(a["local_path"]).name == archive.name)
        assert sha(archive) == expected["sha256"], archive.name
        with tarfile.open(archive, "r|gz") as source:
            for member in source:
                parts = Path(member.name).parts
                assert not Path(member.name).is_absolute() and ".." not in parts
                assert member.isfile() or member.isdir()
                # Raw evidence only. Never overwrite restored scientific source.
                if len(parts) < 2 or parts[1] != "artifacts" or not member.isfile():
                    continue
                target = output.joinpath(*parts[1:])
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as src, target.open("wb") as dst:
                    import shutil

                    shutil.copyfileobj(src, dst)
    freeze = output / record["freeze_path"]
    assert sha(freeze) == record["freeze_sha256"]
    protocol = json.loads(freeze.read_text())
    checked = []
    missing = []
    old = Path(
        json.loads(
            (output / "research_ops/completion_v12/final_package/RELEASE_INDEX.json").read_text()
        )["original_workspace_root"]
    )
    for category in ["source_hashes", "gate_hashes"]:
        for name, expected in protocol[category].items():
            path = Path(name)
            path = output / (path.relative_to(old) if path.is_absolute() else path)
            if not path.exists():
                missing.append(name)
                continue
            assert sha(path) == expected, name
            checked.append(name)
    report = {
        "source_commit": commit,
        "tracked_source_exported": True,
        "frozen_files_verified": len(checked),
        "missing_raw_gate_paths": missing,
        "all_180_frozen_hashes_verified": len(checked) == 180 and not missing,
        "provider_calls": 0,
        "model_calls": 0,
    }
    (output / "RESTORATION_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if archives:
        assert not missing, "Supply the raw archive required by the original gate inventory"
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-archive", type=Path, action="append", default=[])
    args = parser.parse_args()
    restore(args.output, args.raw_archive)
