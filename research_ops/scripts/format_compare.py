"""Single bounded format pair; lifecycle copied from validated p1_standing, no deployment."""

import argparse
import hashlib
import json
import threading
import time
import traceback
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

from afterclick.agent.browser_observation import public_task
from afterclick.agent.modal_policy import Limits, ModalConfig, ModalPolicy, atomic_json, digest
from afterclick.extensions.interaction_trial import run_task
from afterclick.extensions.native_tools import NativeConfig, NativeToolPolicy
from afterclick.research.finance import Supervisor
from research_ops.scripts.p1_diagnostic import resource_estimate
from research_ops.scripts.p1_existing import cli, contracts

ENDPOINT = "ep-NtuMALXsRWKk5JLfZk4BOF"
ACTIVE_POLICIES = []


def task_hashes():
    return [digest(public_task(contracts()[1]))]


def validate_formats(json_policy, run, deadline):
    # Read schema inside the already budgeted warm window, not an extra cold-start probe.
    try:
        with httpx.Client(timeout=10, trust_env=False) as client:
            response = client.get(json_policy.config.endpoint_url + "/openapi.json")
        atomic_json(
            run / "raw/deployed-openapi.json", dict(status=response.status_code, body=response.text)
        )
    except httpx.HTTPError:
        atomic_json(run / "raw/deployed-openapi.json", dict(status=None, available=False))
    config = NativeConfig(**asdict(json_policy.config))
    approval = dict(json_policy.approval)
    approval.update(
        config_sha256=config.fingerprint, limits_sha256=digest(asdict(json_policy.limits))
    )
    atomic_json(run / "raw/native-inference-approval.json", approval)
    native = NativeToolPolicy(
        config,
        json_policy.limits,
        journal=run / "native-model-calls.jsonl",
        mode="live",
        approval_path=run / "raw/native-inference-approval.json",
        public_synthetic_task_hashes=task_hashes(),
    )
    ACTIVE_POLICIES.append(native)
    reports = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                for label, policy in [("json_schema", json_policy), ("native_tools", native)]:
                    if any(x.usage_summary()["uncertain"] for x in ACTIVE_POLICIES):
                        raise RuntimeError("Prior provider request unresolved; no next arm")
                    result = run_task(
                        browser, contracts()[1], policy, run / label, deadline, max_turns=6
                    )
                    reports.append(result)
                    with (run / "trials.jsonl").open("a") as f:
                        f.write(
                            json.dumps(
                                dict(
                                    schema_version=1,
                                    format=label,
                                    accepted=result["accepted"],
                                    valid=result["valid"],
                                    task_success=result.get("task", {}).get("success"),
                                    repeated_proposals=result["repeated_proposals"],
                                    executed_repetitions=result["executed_repetitions"],
                                    termination=result["termination"],
                                    raw_reference=label + "/report.json",
                                )
                            )
                            + "\n"
                        )
                    with (run / "oracle_certificates.jsonl").open("a") as f:
                        f.write(
                            json.dumps(
                                dict(
                                    format=label,
                                    task=result.get("task"),
                                    effects=result.get("effects"),
                                )
                            )
                            + "\n"
                        )
            finally:
                browser.close()
    finally:
        native.close()
    winner = (
        "native_tools" if reports[1]["accepted"] and not reports[0]["accepted"] else "json_schema"
    )
    atomic_json(
        run / "comparison.json",
        dict(
            schema_version=1,
            arm_count=len(reports),
            attempts_per_arm=1,
            provisional_choice=winner,
            not_population_reliability=True,
            arms=[
                {
                    k: r[k]
                    for k in [
                        "format",
                        "accepted",
                        "valid",
                        "repeated_proposals",
                        "executed_repetitions",
                        "argument_errors",
                        "model_calls",
                        "termination",
                        "policy_usage",
                    ]
                }
                for r in reports
            ],
        ),
    )


def execute(run):
    p = json.loads((run / "protocol.json").read_text())
    auth = json.loads(Path("research_ops/AUTHORIZATION.json").read_text())
    controls = json.loads(Path(run / "raw/financial-controls.json").read_text())
    assert p["endpoint_id"] == ENDPOINT == auth["endpoint_id"]
    guarded_arm = True
    cap, total, startup, window = (0.6, 355, 225, 100) if guarded_arm else (0.9, 450, 240, 180)
    assert p["max_usd"] == cap and p["total_seconds"] == total and p["max_calls"] == 12
    work = total - 30
    assert p["controller_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    assert auth["standing_authorized"] and controls["effective_net_spend_limit_usd"] == 0
    age = (
        datetime.now(timezone.utc) - datetime.fromisoformat(controls["utc_verified"])
    ).total_seconds()
    if not 0 <= age <= 900:
        raise ValueError("Refresh provider cap/net-spend controls before paid work")
    if (run / "raw/paid-start.json").exists():
        raise ValueError("Never reuse a launched run")
    before = json.loads(cli(["billing", "summary", "--json"], run / "raw/billing-before.json"))
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
            run.name, "p1c", p["max_usd"], before, controls["provider_usage_cap_usd"]
        )
        started = time.monotonic()
        since = datetime.now(timezone.utc).isoformat()
        atomic_json(run / "raw/paid-start.json", dict(utc=since, endpoint_id=ENDPOINT))
        server = info["server_id"]
        restored = threading.Event()
        restore_lock = threading.Lock()
        policy = None
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
            config = ModalConfig(
                info["service_url"],
                info["model_name"],
                underlying_model=info["repo_id"],
                model_revision=info["revision"],
                max_input_tokens=16384,
                timeout_seconds=30,
            )
            with httpx.Client(
                timeout=min(15, max(0.1, started + startup - time.monotonic())), trust_env=False
            ) as client:
                response = client.get(config.endpoint_url + "/v1/models")
            atomic_json(
                run / "raw/models-response.json",
                dict(status=response.status_code, body=response.text),
            )
            response.raise_for_status()
            assert config.endpoint_name in {x["id"] for x in response.json()["data"]}
            deadline = min(started + work, time.monotonic() + window)
            limits = Limits(
                max_calls=6,
                max_total_tokens=99840,
                max_wall_seconds=max(30, int(deadline - time.monotonic())),
                max_usd=cap,
            )
            approval = dict(
                approved_by_user=True,
                run_id=run.name,
                config_sha256=config.fingerprint,
                limits_sha256=digest(asdict(limits)),
                max_usd=cap,
                available_compute_credit_usd=supervisor.data["baseline_credit_usd"]
                - supervisor.data["account_additional_highwater_usd"],
                credit_verified=True,
                max_compute_usd_per_second=0.00135,
                startup_allowance_seconds=startup,
                shutdown_allowance_seconds=30,
                expires_utc=(
                    datetime.now(timezone.utc)
                    + timedelta(seconds=max(1, deadline - time.monotonic()))
                ).isoformat(),
                allow_public_synthetic=True,
                public_synthetic_task_hashes=task_hashes(),
                argument_contract="conditional-v2",
                authorization_source="research_ops/AUTHORIZATION.json",
            )
            atomic_json(run / "raw/inference-approval.json", approval)
            policy = ModalPolicy(
                config,
                limits,
                journal=run / "model_calls.jsonl",
                mode="live",
                approval_path=run / "raw/inference-approval.json",
                public_synthetic_task_hashes=task_hashes(),
                argument_contract="conditional-v2",
            )
            ACTIVE_POLICIES.append(policy)
            validate_formats(policy, run, deadline)
            passed = True
        except BaseException:
            error = traceback.format_exc()
            (run / "raw/error.txt").write_text(error)
        finally:
            if policy:
                policy.close()
            try:
                restore()
            except BaseException:
                (run / "raw/cleanup-error.txt").write_text(traceback.format_exc())
                error = error or "min0 restoration failed"
            timer.cancel()
            cleanup_end = min(started + total, time.monotonic() + 20)
            try:
                for index in range(10):
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
                run / "metrics.json",
                dict(
                    schema_version=1,
                    passed=passed,
                    usage=policy.usage_summary() if policy else dict(calls=0),
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
                uncertain=any(x.usage_summary()["uncertain"] for x in ACTIVE_POLICIES),
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
