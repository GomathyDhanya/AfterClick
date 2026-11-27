"""Finite recheck of every missing-fixture failure, preserving the full-run report."""

import argparse
import hashlib
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "research_ops/publication"
CLI = str(Path.home() / ".local/bin/modal")


def load(p):
    return json.loads(p.read_text())


def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n")


def main(run):
    run.mkdir(parents=True, exist_ok=False)
    state = load(KIT / "FINANCE_STATE.json")
    assert (
        state["active"] is None
        and not state["unresolved"]
        and state["guard_accounted_usd"] + 1 <= 28
    )
    assert (
        os.environ.get("MODAL_PROFILE") == "gsankarasubr"
        and os.environ.get("MODAL_ENVIRONMENT") == "main"
    )
    prior = ROOT / "artifacts/research_runs/publication-20261126-linux-regression-v3"
    xml = ET.parse(prior / "restored/tests.xml")
    targets = []
    for t in xml.iter("testcase"):
        failure = t.find("failure")
        if failure is not None:
            assert "p1c-qwen35-9b-smoke-v2/raw/inputs.json" in failure.attrib["message"]
            targets.append(t.attrib["classname"].replace(".", "/") + ".py::" + t.attrib["name"])
    assert len(targets) == 22
    fixture = ROOT / "artifacts/research_runs/p1c-qwen35-9b-smoke-v2/raw/inputs.json"
    reg = dict(
        targets=targets,
        registered=len(targets),
        fixture=str(fixture.relative_to(ROOT)),
        fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
        prior_full_run_tests=417,
        prior_full_run_passed=395,
        prior_full_run_failed=22,
        scope=(
            "All22 prior failures; immutable archived fixture restored; "
            "tests/runtime unchanged; not a fresh full-suite run"
        ),
        cpu=[2, 2],
        memory_mib=[4096, 4096],
        timeout=300,
        block_network=True,
        model_calls=0,
        provider_calls=0,
    )
    save(run / "registration.json", reg)
    state["active"] = dict(run_id=run.name, reservation_usd=1, cpu_only=True)
    state["guard_accounted_usd"] += 1
    save(KIT / "FINANCE_STATE.json", state)
    started = time.monotonic()
    sandbox = None
    closed = False
    error = None
    before = None

    def bill(name):
        p = subprocess.run(
            [CLI, "billing", "summary", "--json", "--profile", "gsankarasubr"],
            capture_output=True,
            text=True,
            timeout=40,
        )
        assert p.returncode == 0
        (run / (name + ".json")).write_text(p.stdout)
        return json.loads(p.stdout)

    try:
        before = bill("billing-before")
        assert float(before["billed_cost"]) == 0
        image = modal.Image.from_id(load(prior / "image.json")["image_id"])
        app = modal.App("afterclick-linux-fixture-followup-20261126", include_source=False)
        with app.run(environment_name="main"):
            sandbox = modal.Sandbox.create(
                "sleep",
                "300",
                app=app,
                image=image,
                cpu=(2, 2),
                memory=(4096, 4096),
                timeout=300,
                block_network=True,
                include_oidc_identity_token=False,
            )
            save(run / "sandbox.json", dict(sandbox_id=sandbox.object_id, app_id=app.app_id))
            sandbox.filesystem.copy_from_local(fixture, "/work/afterclick-v12/" + reg["fixture"])
            sandbox.filesystem.copy_from_local(
                run / "registration.json", "/input/followup-registration.json"
            )
            script = """import subprocess, json, os, tarfile, xml.etree.ElementTree as E
from pathlib import Path

out = Path("/result")
out.mkdir(exist_ok=True)
root = Path("/work/afterclick-v12")
os.environ["PYTHONPATH"] = str(root)
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://afterclick:afterclick_local@127.0.0.1:55432/afterclick"
)
setup = (
    "install -d -o postgres -g postgres /tmp/ac_pg && runuse"
    "r -u postgres -- initdb -D /tmp/ac_pg -A trust && runus"
    "er -u postgres -- pg_ctl -D /tmp/ac_pg -l /tmp/ac_pg/se"
    "rver.log -o '-p 55432 -h 127.0.0.1' start && runuser -u"
    ' postgres -- psql -p 55432 -h 127.0.0.1 -c "CREATE ROLE'
    " afterclick LOGIN SUPERUSER PASSWORD 'afterclick_local'"
    '" && runuser -u postgres -- createdb -p 55432 -h 127.0.'
    "0.1 -O afterclick afterclick"
)
p = subprocess.run(["bash", "-c", setup], capture_output=True, text=True, timeout=30)
(out / "setup.log").write_text(p.stdout + p.stderr)
reg = json.loads(Path("/input/followup-registration.json").read_text())
p = subprocess.run(
    ["python", "-m", "pytest", "-q", *reg["targets"], "--junitxml=/result/tests.xml"],
    cwd=root,
    capture_output=True,
    text=True,
    timeout=180,
)
(out / "pytest.log").write_text(p.stdout + p.stderr)
suite = list(E.parse(out / "tests.xml").getroot())[0].attrib
(out / "report.json").write_text(
    json.dumps(
        dict(
            complete=True,
            returncode=p.returncode,
            pytest=suite,
            all_registered_rechecked=int(suite["tests"]) == reg["registered"],
            all_passed=p.returncode == 0,
            model_calls=0,
            provider_calls=0,
        ),
        indent=2,
    )
)
subprocess.run(
    ["runuser", "-u", "postgres", "--", "pg_ctl", "-D", "/tmp/ac_pg", "stop"],
    capture_output=True,
    timeout=30,
)
with tarfile.open("/result-bundle.tar.gz", "w:gz") as t:
    for q in out.iterdir():
        t.add(q, arcname=q.name)
print(json.dumps(dict(returncode=p.returncode, suite=suite)), flush=True)
"""
            (run / "payload-source.py").write_text(script)
            sandbox.filesystem.write_text(script, "/input/followup.py")
            p = sandbox.exec("python", "-u", "/input/followup.py", timeout=240)
            (run / "stdout.log").write_text(p.stdout.read())
            (run / "stderr.log").write_text(p.stderr.read())
            p.wait()
            save(run / "process.json", dict(returncode=p.returncode))
            sandbox.filesystem.copy_to_local("/result-bundle.tar.gz", run / "result-bundle.tar.gz")
            sandbox.terminate(wait=True)
            closed = True
    except Exception as e:
        error = type(e).__name__ + ": " + str(e)
    finally:
        if sandbox and not closed:
            try:
                sandbox.terminate(wait=True)
                closed = True
            except Exception:
                pass
        after = bill("billing-after")
        elapsed = time.monotonic() - started
        guard = max(
            0.1 + elapsed * (2 * 0.1419 + 4 * 0.024) / 3600 * 1.5,
            float(after["metered_cost"]) - float((before or {}).get("metered_cost", 0)),
        )
        if not closed:
            guard = max(1, guard)
        result = dict(
            error=error,
            closed=closed,
            guard_accounted_usd=guard,
            elapsed_seconds=elapsed,
            cash_billed_usd=float(after["billed_cost"]),
            model_calls=0,
            provider_calls=0,
        )
        save(run / "lifecycle.json", result)
        state = load(KIT / "FINANCE_STATE.json")
        state["runs"].append(dict(run_id=run.name, **result))
        state["guard_accounted_usd"] += guard - 1
        state["active"] = None
        state["unresolved"] = not closed
        save(KIT / "FINANCE_STATE.json", state)
        print(json.dumps(result), flush=True)
        if error:
            raise RuntimeError(error)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if a.execute:
        main(a.run)
    else:
        print("Explicit --execute, finite CPU-only fixture follow-up, at most $1 reserved.")
