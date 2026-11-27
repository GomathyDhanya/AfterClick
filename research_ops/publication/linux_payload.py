"""Network-blocked Linux reproduction payload; no model/cloud SDK imports."""

import hashlib
import json
import os
import platform
import subprocess
import tarfile
import time
from pathlib import Path

BASE = Path("/work")
OUT = Path("/result")
OUT.mkdir(exist_ok=True)
steps = []


def run(name, args, timeout=1200, cwd=None):
    begin = time.time()
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        (OUT / (name + ".log")).write_text(p.stdout + p.stderr)
        result = dict(name=name, returncode=p.returncode, elapsed=time.time() - begin, args=args)
    except subprocess.TimeoutExpired as e:
        (OUT / (name + ".log")).write_text(
            (e.stdout or b"").decode(errors="replace") + (e.stderr or b"").decode(errors="replace")
        )
        result = dict(name=name, returncode=124, elapsed=time.time() - begin, args=args)
    steps.append(result)
    (OUT / "steps.json").write_text(json.dumps(steps, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    return result["returncode"] == 0


def main():
    BASE.mkdir(exist_ok=True)
    archive = Path("/input/evidence.tar.gz")
    checks = json.loads(Path("/input/archive-summary.json").read_text())
    assert hashlib.file_digest(archive.open("rb"), "sha256").hexdigest() == checks["sha256"]
    with tarfile.open(archive, "r|gz") as t:
        for m in t:
            assert (
                m.isfile()
                and not m.issym()
                and not m.islnk()
                and ".." not in Path(m.name).parts
                and not Path(m.name).is_absolute()
            )
            p = BASE / m.name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(t.extractfile(m).read())
    root = BASE / "afterclick-v12"
    manifest = json.loads((root / "PUBLIC_DERIVATIVE_MANIFEST.json").read_text())
    checked = 0
    for name, r in manifest["files"].items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == r["derived_sha256"], name
        checked += 1
    (OUT / "data-verification.json").write_text(
        json.dumps(
            dict(
                passed=True,
                files_checked=checked,
                archive_sha256=checks["sha256"],
                changed_files=manifest["changed_top_level_files"],
            ),
            indent=2,
        )
        + "\n"
    )
    with tarfile.open("/input/publication-source.tar.gz", "r:gz") as t:
        t.extractall(root, filter="data")
    os.chdir(root)
    os.environ["PYTHONPATH"] = str(root)
    os.environ["DATABASE_URL"] = (
        "postgresql+psycopg://afterclick:afterclick_local@127.0.0.1:55432/afterclick"
    )
    metadata = dict(
        platform=platform.platform(),
        python=platform.python_version(),
        cwd=str(root),
        source_git_sha="2080c426 plus hashed publication overlay",
        network_policy="Modal Sandbox block_network=True",
        credentials_injected=False,
    )
    (OUT / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    run(
        "existing-reproduction",
        [
            "python",
            "research_ops/scripts/reproduce_afterclick_v12.py",
            "--root",
            ".",
            "--output",
            str(OUT / "existing"),
        ],
    )
    run(
        "controlled-timing",
        [
            "python",
            "research_ops/scripts/v12_actuator_analysis.py",
            "--run",
            "artifacts/research_runs/v12-31-complex-controlled-enforcement-v1",
            "--output",
            str(OUT / "actuator"),
        ],
    )
    run(
        "normalize",
        ["python", "-m", "research_ops.publication.normalize", "--output", str(OUT / "normalized")],
    )
    run(
        "verify-normalized",
        [
            "python",
            "-m",
            "research_ops.publication.verify_normalized",
            "--data",
            str(OUT / "normalized"),
            "--output",
            str(OUT / "verified"),
        ],
    )
    run(
        "analyze",
        [
            "python",
            "-m",
            "research_ops.publication.analyze_existing",
            "--data",
            str(OUT / "normalized"),
            "--output",
            str(OUT / "analysis"),
        ],
    )
    run(
        "obligations",
        [
            "python",
            "-m",
            "research_ops.publication.obligation_audit",
            "--data",
            str(OUT / "normalized"),
            "--output",
            str(OUT / "obligations"),
        ],
    )
    # Real PostgreSQL is local to this isolated Linux sandbox; no host schema is touched.
    run(
        "postgres-start",
        [
            "bash",
            "-c",
            (
                "install -d -o postgres -g postgres /tmp/ac_pg && runuse"
                "r -u postgres -- initdb -D /tmp/ac_pg -A trust && runus"
                "er -u postgres -- pg_ctl -D /tmp/ac_pg -l /tmp/ac_pg/se"
                "rver.log -o '-p 55432 -h 127.0.0.1' start && runuser -u"
                ' postgres -- psql -p 55432 -h 127.0.0.1 -c "CREATE ROLE'
                " afterclick LOGIN SUPERUSER PASSWORD 'afterclick_local'"
                '" && runuser -u postgres -- createdb -p 55432 -h 127.0.'
                "0.1 -O afterclick afterclick"
            ),
        ],
        timeout=90,
    )
    run(
        "regression", ["python", "-m", "pytest", "-q", "--junitxml=/result/tests.xml"], timeout=1200
    )
    run(
        "boundary-dev",
        [
            "python",
            "-m",
            "research_ops.publication.boundary_probe",
            "--dev",
            "--output",
            str(OUT / "boundary-dev"),
        ],
        timeout=180,
    )
    run(
        "postgres-stop",
        ["runuser", "-u", "postgres", "--", "pg_ctl", "-D", "/tmp/ac_pg", "stop"],
        timeout=30,
    )
    report = dict(
        complete=True,
        steps=steps,
        all_steps_passed=all(s["returncode"] == 0 for s in steps),
        zero_model_calls=True,
        zero_provider_calls=True,
        independent_cloud_machine=True,
        independent_human_operator=False,
    )
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    try:
        main()
    finally:
        with tarfile.open("/result-bundle.tar.gz", "w:gz", compresslevel=1) as t:
            for p in OUT.rglob("*"):
                if (
                    p.is_file()
                    and (p.suffix in {".json", ".log", ".xml"} or p.name == "report.json")
                    and "cases" not in p.parts
                ):
                    t.add(p, arcname=str(p.relative_to(OUT)))
