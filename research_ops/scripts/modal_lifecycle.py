"""Finite lifecycle guard for the one specifically approved P1 smoke endpoint.

Leaves no deployed endpoint after normal completion, EOF, timeout or interruption.
No inference or proxy token generation is performed by this script.
"""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "artifacts/research_runs/p1c-qwen35-9b-smoke-v1"
CLI = str(Path.home() / ".local/bin/modal")
NAME = "afterclick-qwen35-9b"
LOG_DIR = RUN / "raw"


def cli(args, name, timeout=30):
    result = subprocess.run([CLI, *args], capture_output=True, text=True, timeout=timeout)
    (LOG_DIR / name).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("Modal CLI failed; see " + name)
    return result.stdout


def main():
    global LOG_DIR
    if (RUN / "finalization.json").exists():
        raise RuntimeError("This experiment is finalized; a new paid approval is required")
    if sys.argv[1:]:
        if sys.argv[1:] != ["--attempt", "2"]:
            raise ValueError("Only the preregistered prerequisite retry is supported")
        LOG_DIR = RUN / "raw/deployment-attempt-2"
        LOG_DIR.mkdir(exist_ok=False)
    approval = json.loads((RUN / "protocol.json").read_text())
    if approval["approved_by_user"] is not True or approval["max_usd"] != 2:
        raise RuntimeError("Exact paid approval required")
    if cli(["profile", "current"], "launch-profile.txt").strip() != approval["workspace"]:
        raise RuntimeError("Approved workspace mismatch")
    existing = json.loads(
        cli(["endpoint", "list", "--env", "main", "--json"], "launch-endpoints.json")
    )
    if existing:
        raise RuntimeError("Unexpected endpoint exists; refuse duplicate or unrelated cleanup")
    guardrails = json.loads((RUN / "raw/guardrails_verified.json").read_text())
    if guardrails["usage_cap_usd"] != 2 or guardrails["effective_net_spend_limit_usd"] != 0:
        raise RuntimeError("Approved spending guardrails required")
    anchor = RUN / "raw/lifecycle-start.json"
    started = json.loads(anchor.read_text())["started_epoch"] if anchor.exists() else time.time()
    if time.time() - started >= 110:
        raise RuntimeError("Original startup allowance exhausted; no paid launch")
    if not anchor.exists():
        anchor.write_text(
            json.dumps(
                {
                    "started_epoch": started,
                    "work_deadline_epoch": started + 600,
                    "shutdown_deadline_epoch": started + 660,
                }
            )
            + "\n"
        )
    stop_lock = threading.Lock()
    stopped = threading.Event()

    def stop():
        with stop_lock:
            if not stopped.is_set():
                print("Stopping the approved endpoint", flush=True)
                try:
                    cli(
                        ["endpoint", "stop", NAME, "--env", "main", "--yes"],
                        "endpoint-stop.log",
                        timeout=50,
                    )
                    stopped.set()
                except Exception as exc:
                    print("STOP_FAILED", type(exc).__name__, flush=True)

    def watchdog():
        if not stopped.wait(max(0, started + 600 - time.time())):
            stop()
            print("Finite work deadline reached", flush=True)

    timer = threading.Thread(target=watchdog, daemon=True)
    timer.start()
    try:
        print("Approved deployment begins; 600-second work deadline active", flush=True)
        cli(
            [
                "endpoint",
                "create",
                "--env",
                "main",
                "--name",
                NAME,
                "--model",
                approval["underlying_model"],
                "--custom-hf-repo",
                approval["underlying_model"],
                "--custom-hf-revision",
                approval["hf_revision"],
                "--min-containers",
                "0",
                "--max-containers",
                "1",
                "--buffer-containers",
                "0",
                "--scaledown-window",
                "2",
            ],
            "endpoint-create.log",
            timeout=max(1, min(110, 120 - (time.time() - started))),
        )
        while time.time() - started < 120:
            info = json.loads(
                cli(["endpoint", "info", NAME, "--env", "main", "--json"], "endpoint-info.json")
            )
            if info.get("app_id") and info.get("service_url"):
                app = json.loads(
                    cli(["app", "info", info["app_id"], "--env", "main", "--json"], "app-info.json")
                )
                if time.time() - started > 120:
                    raise RuntimeError("Provisioning inspection exceeded startup allowance")
                print("APP_RESOURCE_METADATA", json.dumps(app), flush=True)
                print("READY_FOR_INSPECTION", json.dumps(info), flush=True)
                print("Resource metadata saved; enter stop after bounded work.", flush=True)
                break
            time.sleep(2)
        else:
            raise RuntimeError("Provisioning not inspectable within 120 seconds")
        while not stopped.is_set():
            command = sys.stdin.readline()
            if not command or command.strip() == "stop":
                break
            print("Only stop is supported; inference is separately gated.", flush=True)
    finally:
        stop()
        remaining = cli(["endpoint", "list", "--env", "main", "--json"], "final-endpoints.json")
        active = any(item.get("name") == NAME for item in json.loads(remaining))
        print("FINAL_ENDPOINTS", remaining, flush=True)
        (LOG_DIR / "lifecycle-finished.json").write_text(
            json.dumps(
                {
                    "finished_epoch": time.time(),
                    "elapsed_seconds": round(time.time() - started, 3),
                    "stop_confirmed": not active,
                }
            )
            + "\n"
        )
        if active:
            raise RuntimeError("Cleanup not verified: approved endpoint remains active")


if __name__ == "__main__":
    main()
