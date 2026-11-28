"""Verify archives and git source; restore audit-relevant raw members byte exactly."""

import gzip
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HISTORY = HERE / "provenance/historical"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, x):
    path.write_text(json.dumps(x, indent=2) + "\n")


def main():
    snapshot = json.loads((ROOT / "archive/SNAPSHOTS.json").read_text())
    freeze = json.loads((HISTORY / snapshot["freeze_path"]).read_text())
    relevant = [
        "artifacts/research_runs/" + name
        for name in [
            "v12-43-frozen-larger-test-v1/",
            "v12-44-frozen-primary-test-v1/",
            "v12-68-final-credit-bound-continuation/",
            "v12-final-evidence-v1/",
        ]
    ]
    gates = set(freeze["gate_hashes"])
    assets, members, manifest_paths = [], [], []
    for asset in snapshot["assets"]:
        path = ROOT / asset["local_path"]
        actual = sha(path) if path.exists() else None
        assets.append(
            dict(
                **asset,
                actual_sha256=actual,
                accessible=path.exists(),
                matches=actual == asset["sha256"],
            )
        )
        assert actual == asset["sha256"], path
        if not path.name.endswith("tar.gz"):
            continue
        # Candidate is independently inventoried and checked; original + companion
        # supply restoration. Store all member names/sizes, hash restored raw members.
        is_candidate = "Candidate" in path.name
        with tarfile.open(path, "r|gz") as archive:
            for m in archive:
                parts = Path(m.name).parts
                assert not Path(m.name).is_absolute() and ".." not in parts
                assert m.isfile() or m.isdir(), m.name
                rel = "/".join(parts[1:])
                chosen = (
                    m.isfile()
                    and (rel in gates or any(rel.startswith(p) for p in relevant))
                    and not rel.endswith(".tar.gz")
                )
                record = dict(
                    archive=path.name,
                    name=m.name,
                    bytes=m.size,
                    restored=chosen and not is_candidate,
                )
                if chosen and not is_candidate:
                    target = HISTORY / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    data = archive.extractfile(m).read()
                    target.write_bytes(data)
                    record["sha256"] = hashlib.sha256(data).hexdigest()
                if (
                    m.isfile()
                    and ("manifest" in m.name.lower() or "release_index" in m.name.lower())
                    and m.size < 1_000_000
                ):
                    manifest_paths.append(dict(archive=path.name, name=m.name))
                    if "artifacts/" not in rel and Path(rel).suffix in {".json", ".csv"}:
                        target = HERE / "provenance/release_manifests" / path.stem / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.extractfile(m).read())
                members.append(record)
    with gzip.open(HERE / "provenance/archive_members.json.gz", "wt") as stream:
        json.dump(members, stream, separators=(",", ":"))
    write(HERE / "provenance/release_manifests.json", manifest_paths)
    frozen = []
    for category in ["source_hashes", "gate_hashes"]:
        for rel, expected in freeze[category].items():
            path = Path(rel)
            if path.is_absolute():
                path = path.relative_to(ROOT)
            actual = sha(HISTORY / path) if (HISTORY / path).exists() else None
            frozen.append(
                dict(
                    category=category,
                    path=str(path),
                    expected=expected,
                    actual=actual,
                    matches=actual == expected,
                )
            )
    git_files = []
    tree = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-tree", "-r", snapshot["source_commit"]], text=True
    )
    for line in tree.splitlines():
        metadata, rel = line.split("\t")
        mode, kind, expected = metadata.split()
        actual = subprocess.check_output(
            ["git", "hash-object", str(HISTORY / rel)], text=True
        ).strip()
        git_files.append(
            dict(path=rel, blob_expected=expected, blob_actual=actual, matches=expected == actual)
        )
    write(HERE / "provenance/git_source_inventory.json", git_files)
    write(HERE / "provenance/frozen_hashes.json", frozen)
    # Payload expected source hashes are recorded assertions by the historical
    # worker, not an independent attestation of deployed container bytes.
    payloads = []
    for prefix in relevant[:3]:
        for p in sorted((HISTORY / prefix).glob("cloud-batches/*/*/payload.json")):
            x = json.loads(p.read_text())
            checks = {
                name: sha(HISTORY / name) == expected
                for name, expected in x["expected_source_hashes"].items()
            }
            payloads.append(
                dict(
                    path=str(p.relative_to(HISTORY)),
                    sha256=sha(p),
                    batch_id=x["batch_id"],
                    checks=checks,
                    all_match=all(checks.values()),
                )
            )
    write(HERE / "provenance/executed_source_payloads.json", payloads)
    report = dict(
        assets=assets,
        source_commit=snapshot["source_commit"],
        protocol_sha256=sha(HISTORY / snapshot["freeze_path"]),
        git_source_files=len(git_files),
        git_source_matches=sum(r["matches"] for r in git_files),
        frozen_files=len(frozen),
        frozen_matches=sum(r["matches"] for r in frozen),
        execution_payloads=len(payloads),
        payloads_source_matches=sum(r["all_match"] for r in payloads),
        accessible="all three named archives and git bundle; all relevant TEST raw restored separately from source",  # noqa: E501
        restoration_scope="all git-tracked files plus relevant internal TEST runs, final evidence and frozen raw gate records; redundant unrelated extracted copies omitted after full extraction exhausted disk",  # noqa: E501
        failed_attempt_log="provenance/restoration.log",
        missing=[
            "exact historical authorization-read timestamps",
            "exact historical transaction commit instants",
            "provider internal scheduling traces",
            "independent deployed-container byte attestation",
        ],
        model_calls=0,
    )
    write(HERE / "integrity_report.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "assets"}, indent=2))
    assert all(r["matches"] for r in frozen + git_files)
    assert all(r["all_match"] for r in payloads)


if __name__ == "__main__":
    main()
