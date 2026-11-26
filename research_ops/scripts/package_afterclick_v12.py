"""Build and independently extract-check the local evidence release, no inference."""

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(output):
    index = json.loads(
        (ROOT / "research_ops/completion_v12/final_package/RELEASE_INDEX.json").read_text()
    )
    output = output.resolve()
    assert not output.exists()
    selected = [
        "afterclick",
        "apps",
        "migrations",
        "tests",
        "docs",
        "research_ops",
        "paper",
        "output/pdf",
        "artifacts/research_runs",
        "artifacts/reproductions",
        "artifacts/external/undobench-v1",
        "artifacts/external/undobench-env-v12-requirements.txt",
        "README.md",
        "AGENTS.md",
        "pyproject.toml",
        "uv.lock",
        "alembic.ini",
        "Makefile",
    ]
    excludes = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".DS_Store",
    }
    files = {}
    for name in selected:
        path = ROOT / name
        if not path.exists():
            continue
        candidates = path.rglob("*") if path.is_dir() else [path]
        for p in candidates:
            if not p.is_file() or p.is_symlink():
                continue
            rel = p.relative_to(ROOT)
            if (
                any(part in excludes for part in rel.parts)
                or p.name.startswith(".env")
                or p.suffix in {".pyc", ".pem", ".key"}
                or p.name in {"SPEND_STATE.lock", ".modal.toml"}
            ):
                continue
            files[str(rel)] = p
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        name: dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)
        for name, p in sorted(files.items())
    }
    metadata = dict(
        schema_version=1,
        files=manifest,
        freeze_sha256=index["freeze_sha256"],
        full_matrix_complete=index["full_matrix_complete"],
        registered=index["registered_test"],
        terminal=index["terminal_test"],
        unexecuted=index["unexecuted_test"],
        excluded_runtime_caches_and_credentials=True,
    )
    with tarfile.open(output, "w:gz", compresslevel=1) as archive:
        for name, p in sorted(files.items()):
            archive.add(p, arcname="afterclick-v12/" + name, recursive=False)
        import io

        blob = json.dumps(metadata, indent=2).encode()
        info = tarfile.TarInfo("afterclick-v12/RELEASE_FILE_MANIFEST.json")
        info.size = len(blob)
        archive.addfile(info, io.BytesIO(blob))
    # Verify every archived byte by reading the artifact independently; reject
    # unsafe paths and links without mutating any original research file.
    checked = 0
    with tarfile.open(output, "r:gz") as archive:
        for member in archive:
            if member.name == "afterclick-v12/RELEASE_FILE_MANIFEST.json":
                continue
            assert member.isfile() and not member.issym() and not member.islnk()
            name = member.name.removeprefix("afterclick-v12/")
            assert ".." not in Path(name).parts and name in manifest
            with archive.extractfile(member) as stream:
                checksum = hashlib.sha256(stream.read()).hexdigest()
            assert checksum == manifest[name]["sha256"]
            checked += 1
    assert checked == len(manifest)
    report = dict(
        package=str(output),
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        files_checked=checked,
        bytes=output.stat().st_size,
        all_hashes_match=True,
        full_matrix_complete=index["full_matrix_complete"],
    )
    output.with_suffix(output.suffix + ".verification.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    output.with_suffix(output.suffix + ".sha256").write_text(
        report["sha256"] + "  " + output.name + "\n"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.output)
