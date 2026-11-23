"""Bounded two-phase LOCAL reproduction, dry-run default; known holdout is not new confirmation."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

from afterclick.agent.modal_policy import atomic_json

ROOT = Path(__file__).resolve().parents[2]
NAMES = ["o1-observability-development-v1", "o2-observability-locked-v1"]


def run(replica, execute=False, max_cycles=2, max_wall_minutes=15, paid_mode="disabled"):
    if paid_mode != "disabled" or not re.fullmatch(r"[a-zA-Z0-9_-]{1,50}", replica):
        raise ValueError("Local disabled paid mode and simple replica ID required")
    host = urlsplit(os.environ.get("DATABASE_URL", "postgresql://127.0.0.1")).hostname
    if host not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Loopback test PostgreSQL only")
    if not 1 <= max_cycles <= 2 or not 1 <= max_wall_minutes <= 45:
        raise ValueError("Finite caps required")
    base = ROOT / "artifacts/reproductions" / replica
    commands = [
        [
            sys.executable,
            "-m",
            "afterclick.extensions.observability_study",
            "develop",
            "--run",
            str(base / NAMES[0]),
        ],
        [
            sys.executable,
            "-m",
            "afterclick.extensions.observability_study",
            "confirm",
            "--run",
            str(base / NAMES[1]),
            "--development",
            str(base / NAMES[0]),
        ],
    ]
    if not execute:
        print(json.dumps(dict(dry_run=True, commands=commands, paid_mode="disabled"), indent=2))
        return
    if not base.exists():
        base.mkdir(parents=True)
        for name in NAMES:
            r = base / name
            r.mkdir()
            for d in ["raw", "figures"]:
                (r / d).mkdir()
            for n in ["trials.jsonl", "model_calls.jsonl", "oracle_certificates.jsonl"]:
                (r / n).touch()
            source = ROOT / "research_ops/protocols/observability" / (name + ".json")
            (r / "protocol.json").write_bytes(source.read_bytes())
            atomic_json(
                r / "manifest.json",
                dict(
                    schema_version=1,
                    mode="known_protocol_reproduction_not_new_confirmation",
                    original_run_id=name,
                    replica=replica,
                    protocol_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    model_calls=0,
                    cost_usd=0,
                ),
            )
        atomic_json(
            base / "STATE.json", dict(schema_version=1, completed=0, active=None, failed=False)
        )
    state = json.loads((base / "STATE.json").read_text())
    if state["active"] or state["failed"]:
        raise ValueError("Preserved interruption; diagnose and use fresh replica")
    deadline = time.monotonic() + max_wall_minutes * 60
    for _ in range(max_cycles):
        if state["completed"] == 2:
            break
        name = NAMES[state["completed"]]
        state["active"] = name
        atomic_json(base / "STATE.json", state)
        try:
            with (base / name / "raw/reproduction.log").open("w") as log:
                child = subprocess.Popen(
                    commands[state["completed"]], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT
                )
                try:
                    code = child.wait(timeout=max(1, deadline - time.monotonic()))
                except BaseException:
                    child.terminate()
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
                    raise
            if code:
                raise RuntimeError("Local reproduction failed; raw log preserved")
            state.update(completed=state["completed"] + 1, active=None)
            atomic_json(base / "STATE.json", state)
            with (base / "registry.jsonl").open("a") as f:
                f.write(
                    json.dumps(
                        dict(phase=name, status="complete", new_independent_confirmation=False)
                    )
                    + "\n"
                )
        except BaseException:
            state["failed"] = True
            atomic_json(base / "STATE.json", state)
            with (base / name / "trials.jsonl").open("a") as f:
                f.write(json.dumps(dict(event="crashed_or_interrupted")) + "\n")
            raise
    print(
        json.dumps(
            dict(
                completed=state["completed"],
                total=2,
                paid_mode="disabled",
                reproduction_not_new_confirmation=True,
            )
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replica", required=True)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--max-cycles", type=int, default=2)
    p.add_argument("--max-wall-minutes", type=int, default=15)
    p.add_argument("--paid-mode", choices=["disabled"], default="disabled")
    run(**vars(p.parse_args()))
