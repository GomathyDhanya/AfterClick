"""Restartable bounded LOCAL reproduction; dry run by default, paid execution unsupported."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from afterclick.agent.modal_policy import atomic_json

ROOT = Path(__file__).resolve().parents[2]
PHASES = [
    ("p2-20261123-distinct-mechanisms-v1", ["-m", "afterclick.evaluation.mechanism_pilot"]),
    ("p2-capability-diversity-v1", ["-m", "afterclick.evaluation.capability_pilot"]),
    ("p3-formal-recovery-v1", ["research_ops/scripts/audit_recoverability.py"]),
    ("p4-matched-search-v1", ["-m", "afterclick.research.search"]),
    ("p6-risk-study-v1", ["-m", "afterclick.research.study", "develop"]),
    ("p9-locked-confirmation-v1", ["-m", "afterclick.research.study", "confirm"]),
]


def plan(replica, paid_mode="disabled"):
    if paid_mode != "disabled":
        raise ValueError("This runner cannot authorize or launch paid work")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", replica):
        raise ValueError("Simple replica identifier required")
    host = urlsplit(os.environ.get("DATABASE_URL", "postgresql://127.0.0.1")).hostname
    if host not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Local test PostgreSQL only")
    base = ROOT / "artifacts/reproductions" / replica
    commands = []
    for name, prefix in PHASES:
        args = [sys.executable, *prefix, "--run", str(base / name)]
        if name.startswith("p9-"):
            args.extend(["--development", str(base / "p6-risk-study-v1")])
        commands.append(dict(run=name, argv=args))
    return base, commands


def execute(replica, max_cycles, max_minutes):
    if not 1 <= max_cycles <= 6 or not 1 <= max_minutes <= 60:
        raise ValueError("Finite cycle/wall caps required")
    base, commands = plan(replica)
    state_path = base / "STATE.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state["active"] is not None or state.get("failed"):
            raise ValueError(
                "Earlier interruption/failure preserved; use new replica after diagnosis"
            )
    else:
        base.mkdir(parents=True, exist_ok=False)
        state = dict(
            schema_version=1,
            mode="reproduction_not_new_confirmation",
            completed=0,
            active=None,
            failed=False,
        )
        for name, _ in PHASES:
            r = base / name
            r.mkdir()
            (r / "raw").mkdir()
            (r / "figures").mkdir()
            protocol = (ROOT / "research_ops/protocols" / (name + ".json")).read_bytes()
            expected = json.loads((ROOT / "research_ops/protocols/checksums.json").read_text())[
                name
            ]
            if hashlib.sha256(protocol).hexdigest() != expected:
                raise ValueError("Frozen reproduction protocol changed")
            (r / "protocol.json").write_bytes(protocol)
            atomic_json(
                r / "manifest.json",
                dict(
                    schema_version=1,
                    run_id=name,
                    replica=replica,
                    mode="reproduction",
                    protocol_sha256=hashlib.sha256(protocol).hexdigest(),
                    actual_cost_usd=0,
                    model_calls=0,
                ),
            )
            for file in ["trials.jsonl", "model_calls.jsonl", "oracle_certificates.jsonl"]:
                (r / file).touch()
        atomic_json(state_path, state)
    deadline = time.monotonic() + max_minutes * 60
    for _ in range(max_cycles):
        if state["completed"] == len(commands) or deadline - time.monotonic() < 5:
            break
        item = commands[state["completed"]]
        r = base / item["run"]
        state["active"] = item["run"]
        atomic_json(state_path, state)
        before = datetime.now(timezone.utc).isoformat()
        try:
            with (r / "raw/reproduction-execution.log").open("w") as log:
                process = subprocess.Popen(
                    item["argv"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT
                )
                try:
                    code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    raise TimeoutError(
                        "Bounded local reproduction interrupted; traces retained"
                    ) from None
            if code:
                raise RuntimeError("Child phase failed; inspect its raw log")
            state["completed"] += 1
            state["active"] = None
            atomic_json(state_path, state)
            with (base / "registry.jsonl").open("a") as stream:
                stream.write(
                    json.dumps(
                        dict(
                            run=item["run"],
                            started_utc=before,
                            status="completed",
                            cost_usd=0,
                            independent_new_confirmation=False,
                        )
                    )
                    + "\n"
                )
        except BaseException as error:
            state["failed"] = True
            atomic_json(state_path, state)
            with (r / "trials.jsonl").open("a") as stream:
                stream.write(
                    json.dumps(
                        dict(event="crashed_or_interrupted", error_type=type(error).__name__)
                    )
                    + "\n"
                )
            raise
    print(
        json.dumps(
            dict(
                replica=replica,
                completed_phases=state["completed"],
                total_phases=6,
                next_command=(
                    ".venv/bin/python research_ops/scripts/reproduce_research.py "
                    f"--replica {replica} "
                    "--execute --max-cycles 3 --max-wall-minutes 45 --paid-mode disabled"
                ),
                paid_mode="disabled",
            )
        )
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replica", required=True)
    p.add_argument("--max-cycles", type=int, default=3)
    p.add_argument("--max-wall-minutes", type=int, default=45)
    p.add_argument("--paid-mode", choices=["disabled"], default="disabled")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    base, commands = plan(args.replica, args.paid_mode)
    if args.execute:
        execute(args.replica, args.max_cycles, args.max_wall_minutes)
    else:
        print(
            json.dumps(
                dict(dry_run=True, output=str(base), commands=commands, paid_mode="disabled"),
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
