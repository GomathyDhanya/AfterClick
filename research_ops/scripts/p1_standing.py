"""One frozen live pilot under standing authorization; reuse only, never create or delete."""

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

from afterclick.agent.action_parser import Decision
from afterclick.agent.inference import public_input
from afterclick.agent.modal_policy import Limits, ModalConfig, ModalPolicy, atomic_json, digest
from afterclick.replay.adaptive_runner import run_case
from afterclick.research.finance import Supervisor
from research_ops.scripts.p1_diagnostic import resource_estimate
from research_ops.scripts.p1_existing import browser_task, cli, contracts, smoke_input, task_hashes

ENDPOINT = "ep-NtuMALXsRWKk5JLfZk4BOF"


class Guarded:
    def __init__(self, policy, deadline, controller_journal=None):
        self.policy, self.deadline = policy, deadline
        self.controller_journal = controller_journal

    def __getattr__(self, key):
        return getattr(self.policy, key)

    @property
    def journal(self):
        return self.policy.journal

    @journal.setter
    def journal(self, value):
        # Case helpers must not reset a project-run request/token/uncertainty journal.
        pass

    def before_branch(self):
        if time.monotonic() + 45 > self.deadline or self.policy.usage_summary()["uncertain"]:
            raise TimeoutError("Deadline or unresolved prior inference")

    def decide(self, *args, **kwargs):
        self.before_branch()
        if self.controller_journal is not None:
            task, obs, history = (
                args if args else (kwargs["task"], kwargs["observation"], kwargs["history"])
            )
            payload = public_input(task, obs, history)
            retry = any(
                c["role"] == "button" and c["name"] == "Retry save" and c["enabled"]
                for c in obs["controls"]
            )
            if obs["save_status"] == "Failed" and retry:
                decision = Decision(kind="click", target="Retry save", value="")
                with self.controller_journal.open("a") as f:
                    f.write(
                        json.dumps(
                            dict(
                                schema_version=1,
                                origin="deterministic_visible_retry_guard",
                                observation_sha256=digest(payload["observation"]),
                                decision=decision.model_dump(),
                                model_call=False,
                            )
                        )
                        + "\n"
                    )
                return decision
        return self.policy.decide(*args, **kwargs)


def validate(policy, run, deadline):
    report = dict(schema_version=1, live_policy=True, stages=[], multi_action_gates_replay=False)
    p = json.loads((run / "protocol.json").read_text()) if (run / "protocol.json").exists() else {}
    guarded = Guarded(
        policy,
        deadline,
        run / "controller_decisions.jsonl" if p.get("policy_arm") == "visible-retry-v1" else None,
    )
    decision = guarded.decide(**smoke_input())
    assert decision.kind in {"read", "wait", "done"}, "Read-only smoke failed"
    report["stages"].append(dict(stage="smoke", accepted=True, decision=decision.model_dump()))
    atomic_json(run / "validation-report.json", report)
    base, multi = contracts()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for name, contract, steps in [
                ("legitimate_task", base, 6),
                ("multi_action_task", multi, 8),
            ]:
                result = browser_task(browser, contract, guarded, run / name, steps)
                report["stages"].append(dict(stage=name, accepted=result["accepted"]))
                atomic_json(run / "validation-report.json", report)
                if name == "legitimate_task" and not result["accepted"]:
                    raise RuntimeError("Legitimate task failed independently checked gate")
                if result.get("error") or policy.usage_summary()["uncertain"]:
                    raise RuntimeError("Provider/transport task error; stop rather than bypass")
            directory = run / "counterfactual"
            directory.mkdir()
            case = run_case(
                browser,
                base,
                guarded,
                directory,
                max_steps=5,
                fail_fast=True,
                blind_interventions=True,
                check_budget=guarded.before_branch,
            )
            good = case["certificate"]["valid"] and all(
                b.get("task", {}).get("success") for b in case["branches"].values()
            )
            report["stages"].append(
                dict(stage="counterfactual", accepted=good, certificate=case["certificate"])
            )
            atomic_json(run / "validation-report.json", report)
            if not good:
                raise RuntimeError("Live replay invalid; no additional data collection")
        finally:
            browser.close()
    return report


def execute(run):
    p = json.loads((run / "protocol.json").read_text())
    auth = json.loads(Path("research_ops/AUTHORIZATION.json").read_text())
    controls = json.loads(
        Path(
            "artifacts/research_runs/p1h-20261123-new-endpoint-audit/raw/financial-controls.json"
        ).read_text()
    )
    assert p["endpoint_id"] == ENDPOINT == auth["endpoint_id"]
    guarded_arm = p.get("policy_arm") == "visible-retry-v1"
    cap, total, startup, window = (0.6, 355, 225, 100) if guarded_arm else (0.9, 450, 240, 180)
    assert p["max_usd"] == cap and p["total_seconds"] == total and p["max_calls"] == 40
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
                max_calls=40,
                max_total_tokens=665600,
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
            validate(policy, run, deadline)
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
                uncertain=policy.usage_summary()["uncertain"] if policy else False,
            )
        return 0 if passed and idle and not error else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    if not args.execute:
        print((args.run / "protocol.json").read_text())
    else:
        raise SystemExit(execute(args.run))


if __name__ == "__main__":
    main()
