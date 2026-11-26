"""Post-TEST operational corrigendum: admit only never-started external assignments.
Original frozen actor, environment, SDK and estimators remain unchanged.
"""

"""Independent v12 credit ledger and finite lifecycle for the authorized endpoint.

Previous ledgers and their category limits remain byte-preserved. A reservation
is not permission for cash. A fresh billing-control attestation and live credit
balance are mandatory. Neither endpoint creation nor deletion is supported.
"""

import argparse
import fcntl
import json
import subprocess
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import httpx

from afterclick.agent.modal_policy import atomic_json
from afterclick.completion_v12.benchmark.runner import execute as run_episodes
from afterclick.completion_v12.benchmark.transport import Transport
from afterclick.completion_v12.evidence import sha
from research_ops.scripts.p1_diagnostic import resource_estimate
from research_ops.scripts.p1_existing import cli as modal_cli

KIT = Path("research_ops/completion_v12")
ENDPOINT = "ep-Lqp751voQWfhhoZTNXD4Yf"
STATE = KIT / "FINANCE_STATE.json"
RATE_CEILING = 0.00135


def cli(args, output, timeout=45):
    """Control-plane reads can exceed the old 15-second preflight allowance."""
    return modal_cli(args, output, timeout=timeout)


def read(path):
    return json.loads(Path(path).read_text())


class CreditLedger:
    def __enter__(self):
        self.lock = Path("research_ops/SPEND_STATE.lock").open("a")
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for path in ["research_ops/SPEND_STATE.json", "research_ops/TIMING_SPEND_STATE.json"]:
            old = read(path)
            if old.get("active") or old.get("unresolved_request"):
                raise ValueError("Historical paid lifecycle remains unresolved")
        self.data = read(STATE) if STATE.exists() else None
        if self.data and (self.data["active"] or self.data["unresolved_request"]):
            raise ValueError("Prior v12 reservation is unresolved")
        return self

    def __exit__(self, *args):
        self.lock.close()

    def reserve(self, run, cap, billing, controls):
        auth = read(KIT / "FINANCE_AUTHORIZATION.json")
        assert auth["endpoint_id"] == ENDPOINT
        assert auth["v12_endpoint_credit_ceiling_usd"] == 18
        assert auth["cash_authorized_usd"] == 0
        assert controls["effective_net_spend_limit_usd"] == 0
        assert controls["source"] in {"observed_provider_ui", "explicit_user_attestation"}
        age = (
            datetime.now(timezone.utc) - datetime.fromisoformat(controls["utc_verified"])
        ).total_seconds()
        # The user's setting confirmation remains applicable throughout this session.
        # Live billing and remaining credits are independently re-read for every job.
        if not 0 <= age <= 86400:
            raise ValueError("Billing-control attestation is stale")
        meter = float(billing["metered_cost"])
        if (
            float(billing["billed_cost"]) != 0
            or float(billing["metered_cost_breakdown"]["llm_tokens"]) != 0
        ):
            raise ValueError("Cash/shared-token spending is outside this reservation")
        credit = float(controls["monthly_credit_usd"]) - abs(
            float(billing["adjustments"]["credits"])
        )
        if self.data is None:
            self.data = dict(
                schema_version=1,
                endpoint_id=ENDPOINT,
                authorization="FINANCE_AUTHORIZATION.json",
                ceiling_usd=18,
                baseline_metered_usd=meter,
                baseline_credit_usd=credit,
                account_metered_highwater_usd=meter,
                runs=[],
                active=None,
                unresolved_request=False,
            )
        self.data["account_metered_highwater_usd"] = max(
            meter, self.data["account_metered_highwater_usd"]
        )
        spent = max(
            sum(r["guard_charge_usd"] for r in self.data["runs"]),
            self.data["account_metered_highwater_usd"] - self.data["baseline_metered_usd"],
        )
        credit = min(credit, self.data["baseline_credit_usd"] - spent)
        if cap <= 0 or spent + cap > 18 or credit - cap < 1:
            raise ValueError("Reservation exceeds authorized credits or billing-lag buffer")
        if controls["provider_usage_cap_usd"] - meter < cap:
            raise ValueError("Insufficient provider hard-cap headroom")
        if any(r["run_id"] == run.name for r in self.data["runs"]):
            raise ValueError("A closed paid job cannot be relaunched")
        self.data["active"] = dict(
            run_id=run.name,
            endpoint_id=read(run / "paid-protocol.json")["endpoint_id"],
            reserved_usd=cap,
            metered_before_usd=meter,
            utc=datetime.now(timezone.utc).isoformat(),
        )
        atomic_json(STATE, self.data)

    def close(self, billing, elapsed, rate, idle, usage):
        active = self.data["active"]
        meter = float(billing["metered_cost"])
        conservative = max(elapsed * rate * 1.25, meter - active["metered_before_usd"])
        charge = conservative if idle and not usage.get("uncertain") else active["reserved_usd"]
        self.data["runs"].append(
            dict(
                **active,
                guard_charge_usd=charge,
                elapsed_seconds=elapsed,
                rate_usd_per_second=rate,
                billing_after_usd=meter,
                idle_verified=idle,
                usage=usage,
                actual_isolated_invoice_usd=None,
            )
        )
        self.data["account_metered_highwater_usd"] = max(
            meter, self.data["account_metered_highwater_usd"]
        )
        self.data["active"] = None
        self.data["unresolved_request"] = (
            not idle or bool(usage.get("uncertain")) or float(billing["billed_cost"]) != 0
        )
        atomic_json(STATE, self.data)


def execute(run):
    protocol = read(run / "paid-protocol.json")
    registration = read(run / "registration.json")
    endpoint = protocol["endpoint_id"]
    if endpoint != ENDPOINT:
        admitted_model = read(KIT / "ADDITIONAL_MODEL_ENDPOINT.json")
        assert endpoint == admitted_model["endpoint_id"]
        assert protocol["model"] == admitted_model["repo_id"]
        assert protocol["revision"] == admitted_model["revision"]
    assert sha(run / "registration.json") == protocol["registration_sha256"]
    rate_ceiling = protocol.get("max_rate_usd_per_second", RATE_CEILING)
    assert protocol["total_seconds"] * rate_ceiling * 1.25 <= protocol["max_usd"]
    assert protocol["startup_seconds"] + 60 < protocol["total_seconds"]
    for name, expected in protocol["source_hashes"].items():
        assert sha(Path(name)) == expected, name
    if registration["mode"].startswith("DEV"):
        root = Path(registration["qualification_root"])
        for identifier, entry in registration["contracts"].items():
            evidence = read(root / identifier / "qualification.json")
            assert evidence["status"] == "REFERENCE_QUALIFIED", identifier
            assert evidence["contract_sha256"] == sha(Path(entry["path"]))
            for index in range(2):
                assert (
                    read(root / identifier / f"oracle-{index}.json")["joint_safe_completion"]
                    is True
                )
                assert read(root / identifier / f"cut-certificate-{index}.json")["valid"] is True
        for filename in [
            "flow.py",
            "ops.py",
            "infrastructure.py",
            "domain_v12.py",
            "browser.py",
            "ui.py",
            "interface.html",
            "oracle.py",
        ]:
            assert sha(root / "source-archive" / filename) == sha(
                Path("afterclick/completion_v12/benchmark") / filename
            ), filename
    elif registration["mode"] != "FROZEN_TEST":
        raise ValueError("Unknown experiment phase")
    else:
        from afterclick.completion_v12.freeze import admit

        admit(protocol, registration)
    if (run / "external-registration.json").exists():
        assert sha(run / "external-registration.json") == protocol["external_registration_sha256"]
        external_registration = read(run / "external-registration.json")
        if registration["mode"].startswith("DEV"):
            assert external_registration["mode"] == "DEV_OFFICIAL_EXTERNAL"
            assert all(c["split"] == "dev" for c in external_registration["episodes"])
        else:
            frozen = read(protocol["freeze_path"])
            key = (
                "external_dev_manifest"
                if protocol.get("external_before_main")
                and not protocol.get("external_official_before_main")
                else "external_manifest"
            )
            manifest = Path(frozen[key]["path"])
            assert sha(manifest) == frozen[key]["sha256"]
            assert external_registration["mode"] == (
                "DEV_OFFICIAL_EXTERNAL"
                if protocol.get("external_before_main")
                and not protocol.get("external_official_before_main")
                else "FROZEN_OFFICIAL_EXTERNAL"
            )
            if protocol.get("external_resume_of"):
                allowed = {c["episode_id"]: c for c in read(manifest)["episodes"]}
                requested = external_registration["episodes"]
                assert len(requested) == len({c["episode_id"] for c in requested})
                for cell in requested:
                    assert cell == allowed[cell["episode_id"]]
                    for previous in protocol["external_previous_runs"]:
                        assert not (
                            Path(previous) / "external-episodes" / cell["episode_id"]
                        ).exists(), "Never retry a started or uncertain external assignment"
            else:
                assert external_registration["episodes"] == read(manifest)["episodes"]
    if protocol.get("pre_development_run"):
        stage = Path(protocol["pre_development_run"])
        assert sha(stage / "registration.json") == protocol["pre_development_registration_sha256"]
        pre = read(stage / "registration.json")
        assert pre["mode"].startswith("DEV")
        assert all(key.startswith("DEV-") for key in pre["contracts"])
        for key, entry in pre["contracts"].items():
            evidence = read(Path(pre["qualification_root"]) / key / "qualification.json")
            assert evidence["status"] == "REFERENCE_QUALIFIED"
            assert evidence["contract_sha256"] == sha(Path(entry["path"]))
    raw = run / "raw"
    raw.mkdir(exist_ok=True)
    if (raw / "paid-start.json").exists():
        raise ValueError("A paid job is finite and cannot be automatically retried")
    controls = read(raw / "financial-controls.json")
    with CreditLedger() as ledger:
        before = json.loads(cli(["billing", "summary", "--json"], raw / "billing-before.json"))
        info = json.loads(
            cli(["endpoint", "info", endpoint, "--env", "main", "--json"], raw / "endpoint.json")
        )
        if (
            info["serving_mode"] != "dedicated"
            or info["status"]
            not in ({"live", "provisioning"} if endpoint != ENDPOINT else {"live"})
            or info["repo_id"] != protocol["model"]
            or info["revision"] != protocol["revision"]
            or info["requires_proxy_auth"]
        ):
            raise ValueError("Endpoint identity differs from registered serving configuration")
        ledger.reserve(run, protocol["max_usd"], before, controls)
        started, started_wall = time.monotonic(), time.time()
        since = datetime.now(timezone.utc).isoformat()
        atomic_json(raw / "paid-start.json", dict(utc=since, endpoint_id=endpoint))
        server = info["server_id"]
        restored = threading.Event()
        scale_lock = threading.Lock()
        transport, idle, error, rate = None, False, None, rate_ceiling
        deadline = started + protocol["total_seconds"] - 60
        keepalive_stop = threading.Event()
        keepalive_thread = None
        cloud_started = False
        pre_development_started = False

        def cloud_stage(stage, call_cap):
            command = [
                str(Path.home() / ".local/bin/modal"),
                "run",
                "research_ops/completion_v12/cloud_worker.py::execute_registered",
                "--run-dir",
                str(stage.resolve()),
                "--service-url",
                info["service_url"],
                "--model-name",
                info["model_name"],
                "--deadline-utc",
                str(time.time() + max(0, deadline - time.monotonic())),
                "--max-calls",
                str(call_cap),
            ]
            with (stage / "cloud-execution.log").open("w") as stream:
                result = subprocess.run(
                    command,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    timeout=max(1, deadline - time.monotonic() + 45),
                )
            if result.returncode:
                raise RuntimeError("Cloud stage failed; raw evidence retained: " + str(stage))

        def external_stage(call_cap):
            command = [
                str(Path("artifacts/external/undobench-env-v12/bin/python").absolute()),
                "-m",
                "research_ops.scripts.v12_external",
                "--run",
                str(run.resolve()),
                "--execute",
                "--service-url",
                info["service_url"],
                "--model-name",
                info["model_name"],
                "--deadline-utc",
                str(time.time() + max(0, deadline - time.monotonic())),
                "--max-calls",
                str(call_cap),
            ]
            with (run / "external-execution.log").open("w") as stream:
                result = subprocess.run(
                    command,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    timeout=max(1, deadline - time.monotonic() + 20),
                )
            if result.returncode:
                raise RuntimeError("Official external runner failed; raw output retained")

        def scale(minimum, idle_seconds, label):
            with scale_lock:
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
                        str(idle_seconds),
                    ],
                    raw / f"autoscaler-{label}.txt",
                    timeout=30,
                )
                value = json.loads(
                    cli(
                        ["server", "autoscaler", "settings", server, "--env", "main", "--json"],
                        raw / f"settings-{label}.json",
                    )
                )["current_settings"]
                if (
                    value.get("min_containers") or 0,
                    value["max_containers"],
                    value.get("buffer_containers") or 0,
                    value["scaledown_window"],
                ) != (minimum, 1, 0, idle_seconds):
                    raise RuntimeError("Provider autoscaler readback mismatch")
                return value

        def restore():
            if not restored.is_set():
                scale(0, 2, "final-min0")
                restored.set()

        def watchdog():
            try:
                restore()
            except BaseException:
                (raw / "watchdog-error.txt").write_text(traceback.format_exc())

        timer = threading.Timer(protocol["total_seconds"] - 60, watchdog)
        timer.daemon = True
        timer.start()
        try:
            # Keep the provider minimum at zero even while warming: a lost host
            # cannot leave an indefinitely billed minimum container behind.
            settings = scale(0, 60, "warm")
            resources = json.loads(
                cli(["server", "info", server, "--env", "main", "--json"], raw / "server.json")
            )
            resources.update(
                {k: settings.get(k) or 0 for k in ["min_containers", "buffer_containers"]}
            )
            resources.update(max_containers=1, scaledown_window=2)
            rates = json.loads(cli(["billing", "rates", "--json"], raw / "rates.json"))
            estimate = resource_estimate(resources, rates, expected_min_containers=0)
            atomic_json(raw / "resource-estimate.json", estimate)
            rate = estimate["usd_per_second_estimate"]
            if rate > rate_ceiling:
                raise ValueError("Observed serving rate exceeds reservation envelope")
            # A bounded metadata request triggers cold provisioning without an LLM
            # generation. Startup/idle compute is included in this reservation.
            try:
                with httpx.Client(timeout=120, trust_env=False) as client:
                    prime = client.get(info["service_url"] + "/v1/models")
                    atomic_json(
                        raw / "warm-metadata.json", dict(status=prime.status_code, body=prime.text)
                    )
            except httpx.TransportError as exc:
                atomic_json(raw / "warm-metadata.json", dict(error=type(exc).__name__))
            ready = False
            usable_models = None
            index = 0
            while True:
                if time.monotonic() >= started + protocol["startup_seconds"] - 15:
                    break
                # Keep bounded routing demand present during provisioning. A
                # metadata 503 is readiness information, never an LLM retry.
                try:
                    with httpx.Client(timeout=5, trust_env=False) as client:
                        candidate = client.get(info["service_url"] + "/v1/models")
                        health = client.get(info["service_url"] + "/health")
                    atomic_json(
                        raw / f"routing-readiness-{index}.json",
                        dict(
                            status=candidate.status_code,
                            body=candidate.text,
                            health_status=health.status_code,
                            wall=time.time(),
                        ),
                    )
                    if (
                        candidate.status_code == 200
                        and info["model_name"] in {item["id"] for item in candidate.json()["data"]}
                        and health.status_code == 200
                    ):
                        usable_models = candidate
                except (httpx.TransportError, ValueError, KeyError):
                    pass
                if usable_models is not None:
                    ready = True
                    break
                time.sleep(3)
                index += 1
            if not ready:
                raise TimeoutError("Healthy registered model unavailable within bounded startup")
            atomic_json(
                raw / "api-models.json",
                dict(status=usable_models.status_code, body=usable_models.text),
            )
            scale(0, 60, "active-min0")

            def keepalive():
                # Metadata demand prevents another cold start while building the
                # finite CPU image. The existing elapsed-time reservation covers
                # all warm/idle GPU time; no minimum container is introduced.
                with (raw / "finite-metadata-keepalive.jsonl").open("x") as stream:
                    while time.monotonic() < deadline and not keepalive_stop.is_set():
                        try:
                            response = httpx.get(
                                info["service_url"] + "/v1/models", timeout=10, trust_env=False
                            )
                            row = dict(wall=time.time(), status=response.status_code)
                        except Exception as exc:
                            row = dict(wall=time.time(), error=str(exc))
                        stream.write(json.dumps(row) + "\n")
                        stream.flush()
                        keepalive_stop.wait(10)

            keepalive_thread = threading.Thread(target=keepalive, daemon=True)
            keepalive_thread.start()
            pre_used = 0
            if protocol.get("pre_development_run"):
                pre_development_started = True
                stage = Path(protocol["pre_development_run"])
                cloud_stage(stage, protocol["pre_development_max_calls"])
                pre_usage = read(stage / "cloud-usage.json")
                assert read(stage / "queue-reconciliation.json")["complete"]
                assert pre_usage["calls"] > 0 and pre_usage["uncertain"] == 0
                pre_used += pre_usage["calls"]
                atomic_json(
                    raw / "pre-development-accepted.json",
                    dict(
                        utc=datetime.now(timezone.utc).isoformat(),
                        before_any_test=True,
                        stage=str(stage),
                        criterion=(
                            "All registered DEV branches terminal; genuine native calls;"
                            " no uncertain HTTP; no success-rate gate"
                        ),
                    ),
                )
            if protocol.get("external_before_main"):
                external_stage(protocol.get("external_max_calls", 200))
                external_usage = read(run / "external-usage.json")
                assert read(run / "external-reconciliation.json")["complete"]
                assert external_usage["calls"] > 0 and external_usage["uncertain"] == 0
                pre_used += external_usage["calls"]
            if registration.get("execution_backend", "local") == "cloud":
                cloud_started = True
                deadline_wall = time.time() + max(0, deadline - time.monotonic())
                command = [
                    str(Path.home() / ".local/bin/modal"),
                    "run",
                    "research_ops/completion_v12/cloud_worker.py::execute_registered",
                    "--run-dir",
                    str(run.resolve()),
                    "--service-url",
                    info["service_url"],
                    "--model-name",
                    info["model_name"],
                    "--deadline-utc",
                    str(deadline_wall),
                    "--max-calls",
                    str(protocol["max_calls"] - pre_used),
                ]
                with (run / "cloud-execution.log").open("w") as stream:
                    result = subprocess.run(
                        command,
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        timeout=max(1, deadline - time.monotonic() + 45),
                        stdin=subprocess.DEVNULL,
                    )
                if result.returncode:
                    raise RuntimeError("Cloud batch runner failed; see cloud-execution.log")
            else:
                transport = Transport(
                    run / "model-traces",
                    info["service_url"],
                    info["model_name"],
                    deadline=deadline,
                    max_calls=protocol["max_calls"],
                    concurrency=registration["model_concurrency"],
                )
                run_episodes(registration, run / "episodes", transport)
            if (run / "external-registration.json").exists() and not protocol.get(
                "external_before_main"
            ):
                used = (
                    read(run / "cloud-usage.json")["calls"]
                    if cloud_started and (run / "cloud-usage.json").exists()
                    else transport.calls
                    if transport
                    else 0
                )
                remaining_calls = protocol["max_calls"] - used
                command = [
                    str(Path("artifacts/external/undobench-env-v12/bin/python").absolute()),
                    "-m",
                    "research_ops.scripts.v12_external",
                    "--run",
                    str(run.resolve()),
                    "--execute",
                    "--service-url",
                    info["service_url"],
                    "--model-name",
                    info["model_name"],
                    "--deadline-utc",
                    str(time.time() + max(0, deadline - time.monotonic())),
                    "--max-calls",
                    str(remaining_calls),
                ]
                with (run / "external-execution.log").open("w") as stream:
                    completed = subprocess.run(
                        command,
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL,
                        timeout=max(1, deadline - time.monotonic() + 20),
                    )
                if completed.returncode:
                    raise RuntimeError("Official external runner failed; raw output retained")
        except BaseException:
            error = traceback.format_exc()
            (raw / "lifecycle-error.txt").write_text(error)
        finally:
            keepalive_stop.set()
            if keepalive_thread is not None:
                keepalive_thread.join(timeout=12)
            try:
                restore()
                for index in range(20):
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
                            raw / f"containers-after-{index}.json",
                            timeout=5,
                        )
                    )
                    if not containers:
                        idle = True
                        break
                    time.sleep(1)
            except BaseException:
                (raw / "cleanup-error.txt").write_text(traceback.format_exc())
            timer.cancel()
            elapsed = max(time.monotonic() - started, time.time() - started_wall)
            usage = (
                dict(calls=transport.calls, tokens=transport.tokens, uncertain=transport.uncertain)
                if transport
                else dict(calls=0, tokens=0, uncertain=0)
            )
            if (
                registration.get("execution_backend") == "cloud"
                and (run / "cloud-usage.json").exists()
            ):
                usage = read(run / "cloud-usage.json")
            if cloud_started and not (run / "queue-reconciliation.json").exists():
                usage["uncertain"] += 1
                usage["incomplete_cloud_call_accounting"] = True
            if (run / "external-usage.json").exists():
                external = read(run / "external-usage.json")
                for key in ["calls", "tokens", "uncertain"]:
                    usage[key] += external[key]
            if pre_development_started:
                stage = Path(protocol["pre_development_run"])
                if (stage / "cloud-usage.json").exists():
                    pre_usage = read(stage / "cloud-usage.json")
                    for key in ["calls", "tokens", "uncertain"]:
                        usage[key] += pre_usage[key]
                if not (stage / "queue-reconciliation.json").exists():
                    usage["uncertain"] += 1
            after = json.loads(cli(["billing", "summary", "--json"], raw / "billing-after.json"))
            ledger.close(after, elapsed, rate, idle and restored.is_set(), usage)
            atomic_json(
                run / "lifecycle.json",
                dict(
                    usage=usage,
                    elapsed_seconds=elapsed,
                    idle_verified=idle,
                    min0_restored=restored.is_set(),
                    error=error,
                    endpoint_preserved=True,
                ),
            )
        return 0 if idle and error is None else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.execute:
        raise SystemExit(execute(args.run))
    print((args.run / "paid-protocol.json").read_text())
