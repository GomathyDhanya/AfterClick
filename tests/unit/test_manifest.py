import hashlib
from types import SimpleNamespace

from afterclick.replay.demo import source_manifest


def test_source_manifest_ignores_os_metadata_and_hashes_file_bytes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for path in ("afterclick", "apps/flowboard-web/src"):
        (tmp_path / path).mkdir(parents=True)
    (tmp_path / "afterclick/.DS_Store").write_bytes(b"\xff\x00")
    (tmp_path / "afterclick/example.py").write_text("answer = 42\n")
    for name in ("pyproject.toml", "uv.lock", "apps/flowboard-web/package-lock.json"):
        (tmp_path / name).write_text("")
    monkeypatch.setattr("subprocess.run", lambda *a, **k: SimpleNamespace(returncode=1, stdout=""))
    manifest = source_manifest()
    assert "afterclick/.DS_Store" not in manifest["source_files"]
    assert (
        manifest["source_files"]["afterclick/example.py"]
        == hashlib.sha256(b"answer = 42\n").hexdigest()
    )
    assert manifest["git_commit"] is None


def test_optional_runtime_metadata_tool_can_be_absent(monkeypatch):
    from afterclick.replay.demo import optional_command

    def missing(*args, **kwargs):
        raise FileNotFoundError("docker not installed in isolated validation container")

    monkeypatch.setattr("subprocess.run", missing)
    assert optional_command(["docker", "info"]).returncode == 127
