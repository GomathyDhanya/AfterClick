"""Network-blocked corrected full-source regression payload."""

import json
import os
import platform
import subprocess
import tarfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("/work/afterclick-v12")
OUT = Path("/result")
OUT.mkdir(exist_ok=True)
steps = []


def run(name, args, timeout=1200):
    start = time.time()
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    (OUT / (name + ".log")).write_text(p.stdout + p.stderr)
    r = dict(name=name, returncode=p.returncode, elapsed=time.time() - start)
    steps.append(r)
    print(json.dumps(r), flush=True)
    return p.returncode == 0


try:
    with tarfile.open("/input/runtime-evidence.tar.gz") as t:
        t.extractall(ROOT, filter="data")
    os.environ["PYTHONPATH"] = str(ROOT)
    os.environ["DATABASE_URL"] = (
        "postgresql+psycopg://afterclick:afterclick_local@127.0.0.1:55432/afterclick"
    )
    run(
        "postgres-start",
        [
            "bash",
            "-c",
            (
                "install -d -o postgres -g postgres /tmp/ac_pg && runuser -u "
                "postgres -- initdb -D /tmp/ac_pg -A trust && runuser -u post"
                "gres -- pg_ctl -D /tmp/ac_pg -l /tmp/ac_pg/server.log -o '-p"
                " 55432 -h 127.0.0.1' start && runuser -u postgres -- psql -p"
                ' 55432 -h 127.0.0.1 -c "CREATE ROLE afterclick LOGIN SUPERUS'
                "ER PASSWORD 'afterclick_local'\" && runuser -u postgres -- cr"
                "eatedb -p 55432 -h 127.0.0.1 -O afterclick afterclick"
            ),
        ],
        90,
    )
    run("regression", ["python", "-m", "pytest", "-q", "--junitxml=/result/tests.xml"], 1200)
    run(
        "postgres-stop",
        ["runuser", "-u", "postgres", "--", "pg_ctl", "-D", "/tmp/ac_pg", "stop"],
        30,
    )
    xml = ET.parse(OUT / "tests.xml")
    suites = list(xml.getroot())
    suite = suites[0].attrib
    failures = [
        dict(
            classname=t.attrib["classname"],
            name=t.attrib["name"],
            message=t.find("failure").attrib.get("message", ""),
        )
        for t in xml.iter("testcase")
        if t.find("failure") is not None
    ]
    report = dict(
        complete=True,
        all_steps_passed=all(s["returncode"] == 0 for s in steps),
        steps=steps,
        pytest=suite,
        failures=failures,
        platform=platform.platform(),
        python=platform.python_version(),
        model_calls=0,
        provider_calls=0,
        network_blocked=True,
    )
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
finally:
    with tarfile.open("/result-bundle.tar.gz", "w:gz") as t:
        for p in OUT.rglob("*"):
            if p.is_file():
                t.add(p, arcname=str(p.relative_to(OUT)))
