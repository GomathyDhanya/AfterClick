"""Verify/restore the separately supplied evidence archive without provider access."""

import hashlib
import json
import tarfile
from pathlib import PurePosixPath


def verify(archive, restore_to=None):
    if restore_to:
        restore_to.mkdir(parents=True, exist_ok=False)
    observed = {}
    release = derivative = None
    expanded = 0
    with tarfile.open(archive, "r|gz") as src:
        for m in src:
            p = PurePosixPath(m.name)
            assert (
                m.isfile()
                and not m.issym()
                and not m.islnk()
                and not p.is_absolute()
                and ".." not in p.parts
            )
            expanded += m.size
            assert len(observed) < 300000 and expanded < 24 * 1024**3
            b = src.extractfile(m).read()
            observed[m.name] = hashlib.sha256(b).hexdigest()
            if m.name == "afterclick-v12/RELEASE_FILE_MANIFEST.json":
                release = json.loads(b)
            if m.name == "afterclick-v12/PUBLIC_DERIVATIVE_MANIFEST.json":
                derivative = json.loads(b)
            if restore_to:
                dest = restore_to / str(p)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(b)
    assert release is not None
    if derivative:
        expected = {name: r["derived_sha256"] for name, r in derivative["files"].items()}
        scope = "Audited derivative payloads; source-to-derived mapping retained"
    else:
        expected = {"afterclick-v12/" + name: r["sha256"] for name, r in release["files"].items()}
        scope = "Original release payloads"
    for name, sha in expected.items():
        assert observed[name] == sha, name
    report = dict(
        passed=True,
        archive_sha256=hashlib.file_digest(archive.open("rb"), "sha256").hexdigest(),
        files_verified=len(expected),
        members=len(observed),
        scope=scope,
        restored_to=str(restore_to) if restore_to else None,
        no_provider_calls=True,
        no_model_calls=True,
    )
    print(json.dumps(report, indent=2))
    return report
