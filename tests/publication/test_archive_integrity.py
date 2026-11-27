"""Archive evidence must fail closed on path escape or changed payload bytes."""

import hashlib
import io
import json
import tarfile

import pytest

from research_ops.publication.analysis.archive import verify


def fixture_archive(path, payload=b"original", actual=b"original", name="afterclick-v12/raw.json"):
    metadata = {"files": {"raw.json": {"sha256": hashlib.sha256(payload).hexdigest()}}}
    with tarfile.open(path, "w:gz") as t:
        for member, data in [
            (name, actual),
            ("afterclick-v12/RELEASE_FILE_MANIFEST.json", json.dumps(metadata).encode()),
        ]:
            info = tarfile.TarInfo(member)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))


def test_changed_payload_fails_instead_of_trusting_manifest(tmp_path):
    archive = tmp_path / "data.tar.gz"
    fixture_archive(archive, actual=b"changed")
    with pytest.raises(AssertionError):
        verify(archive)


def test_escape_is_rejected_before_extraction(tmp_path):
    archive = tmp_path / "data.tar.gz"
    fixture_archive(archive, name="../outside.json")
    with pytest.raises(AssertionError):
        verify(archive, tmp_path / "restored")
    assert not (tmp_path / "outside.json").exists()


def test_byte_checked_restore_requires_fresh_destination(tmp_path):
    archive = tmp_path / "data.tar.gz"
    fixture_archive(archive)
    target = tmp_path / "restored"
    report = verify(archive, target)
    assert report["passed"] and report["files_verified"] == 1
    assert (target / "afterclick-v12/raw.json").read_bytes() == b"original"
    with pytest.raises(FileExistsError):
        verify(archive, target)
