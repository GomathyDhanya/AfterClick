"""Build and independently hash-check a local publication companion; never uploads."""

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

from research_ops.publication.analysis.audit_data_archive import Redactor

ROOT = Path(__file__).resolve().parents[3]


def main(output):
    assert not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    tracked = (
        subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .split("\0")
    )
    paths = {p for name in tracked if name and (p := ROOT / name).is_file() and not p.is_symlink()}
    for base in (ROOT / "artifacts/research_runs").glob("publication-20261126-*"):
        paths.update(
            p
            for p in base.rglob("*")
            if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts
        )
    audit = (
        ROOT
        / "artifacts/publication-release/AfterClick_v12_Public_Evidence_Candidate.tar.gz.audit.json"
    )
    paths.add(audit)
    for p in paths:
        assert not any(x in p.parts for x in [".git", ".venv", "node_modules", "__pycache__"])
        assert p.suffix not in {".key", ".pem"}
        assert not p.name.startswith(".env") or p.name.endswith(".example")
    redactor = Redactor()
    mapping = {}
    prefix = "afterclick-publication-20261126/"
    with tarfile.open(output, "w:gz", compresslevel=1) as dst:
        for i, p in enumerate(sorted(paths)):
            name = str(p.relative_to(ROOT))
            raw = p.read_bytes()
            public = redactor.transform(name, raw)
            info = tarfile.TarInfo(prefix + name)
            info.size = len(public)
            info.mode = p.stat().st_mode & 0o777
            dst.addfile(info, io.BytesIO(public))
            mapping[name] = dict(
                source_sha256=hashlib.sha256(raw).hexdigest(),
                sha256=hashlib.sha256(public).hexdigest(),
                bytes=len(public),
            )
            if i and i % 2500 == 0:
                print(json.dumps(dict(files_added=i)), flush=True)
        manifest = dict(
            schema_version=1,
            files=mapping,
            credential_audit_findings=redactor.findings,
            original_source_payloads_preserved=True,
            public_upload_performed=False,
            companion_requires_original_data_candidate_sha256="d82178a963b3fe1a4f39d72727c39a5648de8383e8e8bda09b8740779734d509",
            original_research_complete=False,
            anonymous_paper=True,
        )
        b = json.dumps(manifest, indent=2).encode()
        info = tarfile.TarInfo(prefix + "COMPANION_MANIFEST.json")
        info.size = len(b)
        dst.addfile(info, io.BytesIO(b))
    count = 0
    with tarfile.open(output, "r|gz") as src:
        for m in src:
            assert m.isfile() and not m.issym() and not m.islnk() and ".." not in Path(m.name).parts
            if m.name == prefix + "COMPANION_MANIFEST.json":
                continue
            name = m.name.removeprefix(prefix)
            assert hashlib.sha256(src.extractfile(m).read()).hexdigest() == mapping[name]["sha256"]
            count += 1
    assert count == len(mapping)
    digest = hashlib.file_digest(output.open("rb"), "sha256").hexdigest()
    report = dict(
        package=str(output),
        sha256=digest,
        files_checked=count,
        bytes=output.stat().st_size,
        all_payload_hashes_match=True,
        expanded_members_credential_audited=redactor.checked,
        redacted_files=len(redactor.findings),
        credential_pattern_audit_not_universal_privacy_proof=True,
        public_upload_performed=False,
        original_research_matrix_complete=False,
    )
    output.with_suffix(output.suffix + ".verification.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    main(a.output.resolve())
