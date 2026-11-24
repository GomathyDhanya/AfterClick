"""Generic finite lifecycle for preregistered E0-E5 runs on the existing endpoint only."""

import argparse
import hashlib
import json
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import httpx

from afterclick.agent.modal_policy import atomic_json
from afterclick.research.finance import Supervisor
from afterclick.tcope.budget import Factory
from research_ops.scripts.p1_diagnostic import resource_estimate
from research_ops.scripts.p1_existing import cli

ENDPOINT = "ep-NtuMALXsRWKk5JLfZk4BOF"


def execute(run):
    p = json.loads((run / "protocol.json").read_text())
    auth = json.loads(Path("research_ops/AUTHORIZATION.json").read_text())
    controls = json.loads(Path(run / "raw/financial-controls.json").read_text())
    assert p["endpoint_id"] == ENDPOINT == auth["endpoint_id"]
    cap, total, startup, window = (
        p[k] for k in ["max_usd", "total_seconds", "startup_seconds", "inference_seconds"]
    )
    assert 0 < cap <= 2 and 1 <= p["max_calls"] <= 80
    assert total == startup + window + p["cleanup_seconds"]
    assert total * 0.00135 * 1.25 <= cap
    assert sum(p["arm_call_caps"].values()) <= p["max_calls"]
    work = total - p["cleanup_seconds"]
    assert p["controller_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for name, expected in p["source_hashes"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
    assert auth["standing_authorized"] and controls["effective_net_spend_limit_usd"] == 0
    age = (
        datetime.now(timezone.utc) - datetime.fromisoformat(controls["utc_verified"])
    ).total_seconds()
    if not 0 <= age <= 900:
        raise ValueError("Refresh provider cap/net-spend controls before paid work")
    if (run / "raw/paid-start.json").exists():
        raise ValueError("Never reuse a launched run")
    before = json.loads(cli(["billing", "summary", "--json"], run / "raw/billing-before.json"))
    reported_credit = 30 - abs(float(before["adjustments"]["credits"]))
    if min(reported_credit, controls["conservative_credit_usd"]) - cap < 8:
        raise ValueError("Protected $8 credit reserve unavailable")
    if float(before["metered_cost_breakdown"]["llm_tokens"]) != 0:
        raise ValueError("Unexpected token-billed account usage")
    info = json.loads(
        cli(
            ["endpoint", "info", ENDPOINT, "--env", "main", "--json"],
            run / "raw/endpoint-before.json",
        )
    )
    assert info["serving_mode"] == "dedicated" and info["status"] == "live"
    assert info["repo_id"] == p["model"] and info["revision"] == p["revision"]
    assert info["requires_proxy_auth"] is False
    # No other active resources may consume the bounded provider envelope unaccounted.
    endpoints = json.loads(
        cli(["endpoint", "list", "--env", "main", "--json"], run / "raw/endpoints-before.json")
    )
    apps = json.loads(cli(["app", "list", "--env", "main", "--json"], run / "raw/apps-before.json"))
    assert len(endpoints) == 1 and endpoints[0]["endpoint_id"] == ENDPOINT and not apps
    with Supervisor(Path("research_ops/SPEND_STATE.json")) as supervisor:
        supervisor.reserve(
            run.name, p["category"], p["max_usd"], before, controls["provider_usage_cap_usd"]
        )
        started = time.monotonic()
        since = datetime.now(timezone.utc).isoformat()
        atomic_json(run / "raw/paid-start.json", dict(utc=since, endpoint_id=ENDPOINT))
        server = info["server_id"]
        restored = threading.Event()
        restore_lock = threading.Lock()
        factory = None
        idle = False
        error = None
        passed = False
        rate = 0.00135

        def scale(minimum, label):
            cli(
                [
                    "server",
                    "autoscaler",
                    "update",
                    server,
                    "--env",
                    "main",
                    "--min-containers",
                    str(minimum),
                    "--max-containers",
                    "1",
                    "--buffer-containers",
                    "0",
                    "--scaledown-window",
                    "2",
                ],
                run / f"raw/autoscaler-{label}.txt",
                timeout=10,
            )
            settings = json.loads(
                cli(
                    ["server", "autoscaler", "settings", server, "--env", "main", "--json"],
                    run / f"raw/settings-{label}.json",
                    timeout=10,
                )
            )["current_settings"]
            if (
                settings.get("min_containers") or 0,
                settings["max_containers"],
                settings.get("buffer_containers") or 0,
                settings["scaledown_window"],
            ) != (minimum, 1, 0, 2):
                raise RuntimeError("Autoscaler readback mismatch")
            return settings

        def restore():
            with restore_lock:
                if not restored.is_set():
                    scale(0, "restore")
                    restored.set()

        def watchdog():
            try:
                restore()
            except BaseException:
                (run / "raw/watchdog-error.txt").write_text(traceback.format_exc())

        timer = threading.Timer(work, watchdog)
        timer.daemon = True
        timer.start()
        try:
            settings = scale(1, "warm")
            resources = json.loads(
                cli(["server", "info", server, "--env", "main", "--json"], run / "raw/server.json")
            )
            resources.update(
                {k: settings.get(k) or 0 for k in ["min_containers", "buffer_containers"]}
            )
            resources.update(max_containers=1, scaledown_window=2)
            rates = json.loads(cli(["billing", "rates", "--json"], run / "raw/rates.json"))
            admission = resource_estimate(resources, rates, expected_min_containers=1)
            atomic_json(run / "raw/resource-admission.json", admission)
            if admission["usd_per_second_estimate"] > 0.00135:
                raise ValueError("Rate above envelope")
            rate = admission["usd_per_second_estimate"]
            ready = False
            for index in range(45):
                if time.monotonic() > started + startup - 15:
                    break
                try:
                    log = cli(
                        [
                            "endpoint",
                            "logs",
                            ENDPOINT,
                            "--env",
                            "main",
                            "--since",
                            since,
                            "--tail",
                            "100",
                            "--timestamps",
                        ],
                        run / f"raw/readiness-{index}.txt",
                        timeout=min(5, max(0.1, started + startup - 15 - time.monotonic())),
                    )
                except Exception:
                    log = ""
                if "AfterClick (H100:1) sglang deployment is ready." in log:
                    ready = True
                    break
                time.sleep(min(4, max(0, started + startup - 15 - time.monotonic())))
            if not ready:
                raise TimeoutError("No fresh provider readiness; no inference retry")
            with httpx.Client(
                timeout=min(15, max(0.1, started + startup - time.monotonic())), trust_env=False
            ) as client:
                response = client.get(info["service_url"] + "/v1/models")
            atomic_json(
                run / "raw/models-response.json",
                dict(status=response.status_code, body=response.text),
            )
            response.raise_for_status()
            assert info["model_name"] in {x["id"] for x in response.json()["data"]}
            deadline = min(started + work, time.monotonic() + window)
            factory = Factory(
                run,
                p,
                info,
                deadline,
                supervisor.data["baseline_credit_usd"]
                - max(
                    sum(r["guard_charge_usd"] for r in supervisor.data["runs"]),
                    supervisor.data["account_additional_highwater_usd"],
                ),
            )
            from afterclick.tcope.experiments import run_experiment

            run_experiment(p["experiment"], factory, run, deadline)
            passed = True
        except BaseException:
            error = traceback.format_exc()
            (run / "raw/error.txt").write_text(error)
        finally:
            if factory:
                factory.close()
            try:
                restore()
            except BaseException:
                (run / "raw/cleanup-error.txt").write_text(traceback.format_exc())
                error = error or "min0 restoration failed"
            timer.cancel()
            cleanup_end = min(started + total, time.monotonic() + 35)
            try:
                for index in range(20):
                    if time.monotonic() >= cleanup_end:
                        break
                    containers = json.loads(
                        cli(
                            [
                                "container",
                                "list",
                                "--app-id",
                                info["app_id"],
                                "--env",
                                "main",
                                "--json",
                            ],
                            run / f"raw/containers-after-{index}.json",
                            timeout=min(5, max(0.1, cleanup_end - time.monotonic())),
                        )
                    )
                    if not containers:
                        idle = True
                        break
                    time.sleep(1)
            except BaseException:
                (run / "raw/idle-check-error.txt").write_text(traceback.format_exc())
                error = error or "Idle verification unavailable"
            elapsed = time.monotonic() - started
            atomic_json(
                run / "lifecycle-metrics.json",
                dict(
                    schema_version=1,
                    passed=passed,
                    usage=factory.usage() if factory else dict(calls=0),
                    min0_restored=restored.is_set(),
                    idle_verified=idle,
                    endpoint_preserved=True,
                    elapsed_seconds=elapsed,
                    error=error is not None,
                ),
            )
            atomic_json(
                run / "finalization.json",
                dict(
                    schema_version=1,
                    utc=datetime.now(timezone.utc).isoformat(),
                    closed=True,
                    idle_verified=idle,
                    min0_restored=restored.is_set(),
                ),
            )
            after = json.loads(
                cli(["billing", "summary", "--json"], run / "raw/billing-after.json")
            )
            supervisor.finish(
                after,
                elapsed,
                rate,
                idle_verified=idle and restored.is_set(),
                uncertain=factory.usage()["uncertain"] if factory else False,
            )
        return 0 if passed and idle and not error else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.execute:
        raise SystemExit(execute(args.run))
    print((args.run / "protocol.json").read_text())
