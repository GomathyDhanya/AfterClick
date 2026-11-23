"""One approved diagnostic: preflight, provision, inspect, read-only smoke, verified cleanup.

No endpoint is created without --execute and a matching unfinalized approval protocol.
All provider/decision failures stop the run; no inference retries or browser actions.
"""

import argparse
import hashlib
import json
import math
import os
import subprocess
import threading
import time
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from afterclick.agent.modal_policy import (
    Limits,
    ModalConfig,
    ModalPolicy,
    atomic_json,
    digest,
)
from afterclick.replay.demo import source_manifest

ROOT = Path(__file__).resolve().parents[2]
CLI = str(Path.home() / ".local/bin/modal")


def resource_estimate(info, rates, *, expected_min_containers=0):
    """Inspect actual configured resources; distinguish request estimates from limits."""
    if expected_min_containers not in {0, 1}:
        raise ValueError("Only bounded zero/one minimum is supported")
    if (info.get("min_containers"), info.get("max_containers"), info.get("buffer_containers")) != (
        expected_min_containers,
        1,
        0,
    ):
        raise ValueError("Autoscaling differs from approved zero/one/zero")
    if info.get("scaledown_window") != 2:
        raise ValueError("Unapproved idle window")

    def bound(value):
        if isinstance(value, list) and len(value) == 2:
            number, basis = value[1], "configured_limit"
        else:
            number, basis = value, "twice_configured_request_estimate"
        if type(number) not in (int, float) or not math.isfinite(number) or number <= 0:
            raise ValueError("Missing/invalid CPU or memory metadata")
        return number * (2 if basis.startswith("twice") else 1), basis

    cpu, cpu_basis = bound(info.get("cpu"))
    memory, memory_basis = bound(info.get("memory_mib"))
    gpus = info.get("gpus")
    if not isinstance(gpus, list) or not gpus:
        raise ValueError("GPU resource metadata unavailable")
    gpu_hour = 0
    for kind, count in gpus:
        key = "gpu_hour_cost_" + kind.lower().replace("-", "_")
        key = {"gpu_hour_cost_a10": "gpu_hour_cost_a10g"}.get(key, key)
        if type(count) is not int or count < 1 or key not in rates:
            raise ValueError("Unknown GPU price/count")
        gpu_hour += float(rates[key]) * count
    rate = (
        gpu_hour
        + cpu * float(rates["cpu_hour_cost"])
        + memory / 1024 * float(rates["mem_gib_hour_cost"])
    ) / 3600
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("Invalid resource estimate")
    return {
        "usd_per_second_estimate": rate,
        "gpus": gpus,
        "cpu_pricing_basis": cpu_basis,
        "cpu_priced_cores": cpu,
        "memory_pricing_basis": memory_basis,
        "memory_priced_mib": memory,
        "is_hard_billing_bound": False,
    }


class Diagnostic:
    def __init__(self, run, *, clock=time.monotonic, sleep=time.sleep):
        self.run = Path(run).resolve()
        self.p = json.loads((self.run / "protocol.json").read_text())
        if self.run.parent != ROOT / "artifacts/research_runs" or self.run.name != self.p["run_id"]:
            raise ValueError("Registered artifact run required")
        if (self.run / "finalization.json").exists() or (self.run / "raw/paid-start.json").exists():
            raise ValueError("No resumption/retry of finalized or already launched paid run")
        self.is_4b = self.p["underlying_model"] == "Qwen/Qwen3.5-4B"
        timing = (480, 60, 60) if self.is_4b else (240, 60, 60)
        if (
            tuple(self.p[k] for k in ("startup_seconds", "inference_seconds", "shutdown_seconds"))
            != timing
        ):
            raise ValueError("Documented timing limits required")
        if self.is_4b and (
            self.p["hf_revision"] != "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
            or self.p["max_calls"] != 1
            or self.p["approved_max_usd"] != 1.5
            or self.p["max_compute_usd_per_second"] != 0.0021
            or self.p.get("max_total_tokens") != 8448
            or self.p.get("retries") != 0
        ):
            raise ValueError("4B arm differs from preregistered bounded proposal")
        self.work_seconds = sum(timing[:2])
        self.total_seconds = sum(timing)
        self.clock, self.sleep = clock, sleep
        self.started = None
        self.seq = 0
        self.may_exist = False
        self.stopped = threading.Event()
        self.stop_lock = threading.Lock()
        self.private_path = ROOT / ".bootstrap/credentials" / (self.run.name + ".json")
        self.secrets = []
        self.metrics = {
            "schema_version": 1,
            "run_id": self.run.name,
            "status": "preflight",
            "model_calls_attempted": 0,
            "valid_decisions": 0,
            "invalid_decisions": 0,
            "read_only_compliant": 0,
            "planned_decisions": self.p["max_calls"],
            "metadata_models_calls": 0,
            "endpoint_created": False,
            "endpoint_stopped_verified": False,
            "proxy_deleted": False,
            "actual_cost_usd": None,
        }

    def require_approval(self):
        if not 0 < self.p["approved_max_usd"] <= 2:
            raise ValueError("Specific bounded approval required")
        if self.is_4b:
            approval = json.loads((self.run / "approval.json").read_text())
            if (
                approval.get("approved_by_user") is not True
                or approval.get("run_id") != self.run.name
                or approval.get("max_usd") != self.p["approved_max_usd"]
                or approval.get("protocol_sha256")
                != hashlib.sha256((self.run / "protocol.json").read_bytes()).hexdigest()
            ):
                raise ValueError("Approval must match this exact protocol")
        elif self.p.get("approved_by_user") is not True:
            raise ValueError("Specific bounded approval required")

    def safe(self, value):
        text = json.dumps(value)
        for secret in self.secrets:
            text = text.replace(secret, "[REDACTED]")
        return json.loads(text)

    def event(self, stage, **fields):
        row = self.safe(
            {
                "schema_version": 1,
                "run_id": self.run.name,
                "event": stage,
                "utc": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": None
                if self.started is None
                else round(self.clock() - self.started, 3),
                **fields,
            }
        )
        with (self.run / "trials.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        atomic_json(self.run / "metrics.json", self.metrics)

    def command(self, args, label, timeout=20):
        self.seq += 1
        try:
            result = subprocess.run(
                [CLI, *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            chunks = [
                part.decode(errors="replace") if isinstance(part, bytes) else part or ""
                for part in (exc.stdout, exc.stderr)
            ]
            name = f"{self.seq:03d}-{label}-timeout.txt"
            (self.run / "raw" / name).write_text(self.safe("".join(chunks)))
            self.event(
                "cli_timeout", args=args, raw_reference="raw/" + name, timeout_seconds=timeout
            )
            raise
        text = self.safe(result.stdout + result.stderr)
        name = f"{self.seq:03d}-{label}.txt"
        (self.run / "raw" / name).write_text(text)
        self.event("cli", args=args, raw_reference="raw/" + name, exit_code=result.returncode)
        if result.returncode:
            raise RuntimeError("CLI failed: " + label)
        return result.stdout

    def preflight(self):
        if self.command(["profile", "current"], "profile").strip() != self.p["workspace"]:
            raise ValueError("Workspace mismatch")
        if json.loads(self.command(["endpoint", "list", "--env", "main", "--json"], "existing")):
            raise ValueError("Unexpected active endpoint; no duplicate resource launch")
        rates = json.loads(self.command(["billing", "rates", "--json"], "rates"))
        atomic_json(self.run / "raw/rates.json", rates)
        billing = json.loads(self.command(["billing", "summary", "--json"], "billing-before"))
        atomic_json(self.run / "raw/billing-before.json", billing)
        guard = json.loads((self.run / "raw/guardrails_verified.json").read_text())
        if guard["usage_cap_usd"] != 2 or guard["effective_net_spend_limit_usd"] != 0:
            raise ValueError("Documented account guardrails missing")
        if (
            guard["remaining_credit_usd"] < 5 + self.p["approved_max_usd"]
            or guard["usage_headroom_usd"] < self.p["approved_max_usd"]
        ):
            raise ValueError("Insufficient reserve/headroom")
        verified = datetime.fromisoformat(guard["utc_verified"])
        if not 0 <= (datetime.now(timezone.utc) - verified).total_seconds() <= 600:
            raise ValueError("Refresh dashboard guardrails within ten minutes of deployment")
        if not self.private_path.exists():
            result = subprocess.run(
                [CLI, "workspace", "proxy-tokens", "create", "--name", self.run.name, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
                stdin=subprocess.DEVNULL,
            )
            if result.returncode:
                raise RuntimeError("Proxy creation failed; credential-bearing output withheld")
            private = json.loads(result.stdout)
            self.private_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(self.private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as stream:
                json.dump(private, stream)
        private = json.loads(self.private_path.read_text())
        self.secrets = [private["Authorization"], private["Modal-Key"], private["Modal-Secret"]]
        self.event("proxy_ready_before_paid_clock", secret_logged=False)
        self.rates, self.guard = rates, guard
        # Freeze complete code and public input provenance before any paid launch.
        (self.run / "raw/controller-executed.py").write_bytes(Path(__file__).read_bytes())
        atomic_json(self.run / "raw/source-manifest.json", source_manifest())
        self.private = private

    def stop(self):
        with self.stop_lock:
            if self.stopped.is_set() or not self.may_exist:
                return
            try:
                self.command(
                    ["endpoint", "stop", self.p["endpoint_name"], "--env", "main", "--yes"],
                    "stop",
                    timeout=20,
                )
            except Exception as exc:
                self.event("stop_request_error", error_type=type(exc).__name__)
            rows = json.loads(
                self.command(["endpoint", "list", "--env", "main", "--json"], "verify-stop")
            )
            if any(r.get("name") == self.p["endpoint_name"] for r in rows):
                raise RuntimeError("Owned endpoint still active")
            self.metrics["endpoint_stopped_verified"] = True
            self.stopped.set()
            print("STOP_CONFIRMED", flush=True)

    def cleanup_proxy(self):
        if not self.private_path.exists():
            return
        private = json.loads(self.private_path.read_text())
        result = subprocess.run(
            [CLI, "workspace", "proxy-tokens", "delete", private["Modal-Key"], "--yes"],
            capture_output=True,
            text=True,
            timeout=15,
            stdin=subprocess.DEVNULL,
        )
        if result.returncode:
            raise RuntimeError("Temporary proxy cleanup failed")
        self.private_path.unlink()
        self.metrics["proxy_deleted"] = True
        self.event("temporary_proxy_deleted", secret_logged=False)

    def capture_startup_logs(self, deadline):
        """Bounded read-only diagnostics; missing logs do not trigger inference retries."""
        try:
            self.command(
                [
                    "endpoint",
                    "logs",
                    self.p["endpoint_name"],
                    "--env",
                    "main",
                    "--tail",
                    "100",
                    "--timestamps",
                    "--show-container-id",
                ],
                "startup-logs",
                timeout=max(0.1, min(5, deadline - self.clock())),
            )
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            self.event("startup_logs_unavailable", error_type=type(exc).__name__)

    def inspect(self):
        deadline = self.started + self.p["startup_seconds"]
        next_logs = self.started
        while self.clock() < deadline:
            remaining = deadline - self.clock()
            info = json.loads(
                self.command(
                    ["endpoint", "info", self.p["endpoint_name"], "--env", "main", "--json"],
                    "endpoint-info",
                    timeout=max(0.1, min(15, remaining)),
                )
            )
            atomic_json(self.run / "raw/latest-endpoint-info.json", info)
            print("PROVISION", round(self.clock() - self.started), info.get("status"), flush=True)
            if info.get("status") == "failed":
                if self.is_4b:
                    self.capture_startup_logs(deadline)
                raise RuntimeError("Managed endpoint deployment failed")
            if self.is_4b and self.clock() >= next_logs and self.clock() + 5 < deadline:
                self.capture_startup_logs(deadline)
                next_logs = self.clock() + 30
            if info.get("server_id") and info.get("service_url") and info.get("status") == "live":
                if (
                    info["repo_id"] != self.p["underlying_model"]
                    or info["revision"] != self.p["hf_revision"]
                    or not info["requires_proxy_auth"]
                    or info["serving_mode"] != "dedicated"
                ):
                    raise ValueError("Endpoint identity/authentication mismatch")
                resource = json.loads(
                    self.command(
                        ["server", "info", info["server_id"], "--env", "main", "--json"],
                        "server-info",
                        timeout=max(0.1, min(15, deadline - self.clock())),
                    )
                )
                estimate = resource_estimate(resource, self.rates)
                atomic_json(
                    self.run / "raw/resource-admission.json",
                    {"resources": resource, "estimate": estimate},
                )
                if estimate["usd_per_second_estimate"] > self.p["max_compute_usd_per_second"]:
                    raise ValueError("Resource estimate exceeds approved ceiling")
                if self.clock() > deadline:
                    raise TimeoutError("Resource inspection exceeded startup window")
                self.metrics["resource_rate_estimate"] = estimate
                self.event("resource_admitted", estimate=estimate)
                return info
            self.sleep(min(4, max(0, deadline - self.clock())))
        raise TimeoutError(
            f"Provisioning/readiness not established within clean{self.p['startup_seconds']}seconds"
        )

    def smoke(self, info):
        end = min(self.started + self.work_seconds, self.clock() + self.p["inference_seconds"])
        self.metrics["status"] = "live_metadata"
        self.metrics["metadata_models_calls"] = 1
        private = self.private
        base = info["service_url"].rstrip("/")
        ModalConfig(base, info["model_name"], timeout_seconds=30)
        self.event("models_request_started")
        with httpx.Client(
            timeout=min(30, end - self.clock()), follow_redirects=False, trust_env=False
        ) as client:
            result = client.get(
                base + "/v1/models", headers={"Authorization": private["Authorization"]}
            )
        result.raise_for_status()
        models = result.json()
        atomic_json(self.run / "raw/models.json", self.safe(models))
        names = {r["id"] for r in models["data"]}
        api_name = info["model_name"]
        if api_name not in names:
            raise ValueError("Advertised API model name mismatch")
        if end - self.clock() < 30:
            raise TimeoutError("No full bounded generation opportunity remains")
        config = ModalConfig(
            base,
            api_name,
            underlying_model=self.p["underlying_model"],
            model_revision=self.p["hf_revision"],
            timeout_seconds=30,
        )
        limits = Limits(
            max_calls=self.p["max_calls"],
            max_total_tokens=self.p.get("max_total_tokens", 180000),
            max_wall_seconds=max(30, int(end - self.clock())),
            max_usd=min(self.p["approved_max_usd"], self.guard["usage_headroom_usd"]),
        )
        approval = {
            "approved_by_user": True,
            "run_id": self.run.name,
            "config_sha256": config.fingerprint,
            "limits_sha256": digest(asdict(limits)),
            "max_usd": self.p["approved_max_usd"],
            "available_compute_credit_usd": self.guard["remaining_credit_usd"],
            "credit_verified": True,
            "max_compute_usd_per_second": self.p["max_compute_usd_per_second"],
            "startup_allowance_seconds": self.p["startup_seconds"],
            "shutdown_allowance_seconds": 60,
            "expires_utc": (
                datetime.now(timezone.utc) + timedelta(seconds=max(1, end - self.clock()))
            ).isoformat(),
        }
        atomic_json(self.run / "raw/inference-approval.json", approval)
        atomic_json(
            self.run / "raw/resolved-model-config.json",
            {"config": asdict(config), "limits": asdict(limits)},
        )
        inputs = json.loads((self.run / "raw/inputs.json").read_text())
        old = {
            key: os.environ.get(key) for key in ["MODAL_PROXY_TOKEN_ID", "MODAL_PROXY_TOKEN_SECRET"]
        }
        os.environ.update(
            MODAL_PROXY_TOKEN_ID=private["Modal-Key"],
            MODAL_PROXY_TOKEN_SECRET=private["Modal-Secret"],
        )
        policy = None
        try:
            policy = ModalPolicy(
                config,
                limits,
                journal=self.run / "model_calls.jsonl",
                mode="live",
                approval_path=self.run / "raw/inference-approval.json",
            )
            for index, value in enumerate(inputs[: self.p["max_calls"]]):
                if self.clock() + 30 > end:
                    self.metrics["status"] = "partial_time_budget"
                    break
                self.metrics["decision_attempts"] = self.metrics.get("decision_attempts", 0) + 1
                try:
                    decision = policy.decide(value["task"], value["observation"], value["history"])
                    self.metrics["valid_decisions"] += 1
                    compliant = decision.kind in {"read", "wait", "done"}
                    self.metrics["read_only_compliant"] += compliant
                    self.event(
                        "decision", index=index, decision=decision.model_dump(), read_only=compliant
                    )
                    print("DECISION", index, decision.kind, flush=True)
                    if not compliant:
                        self.metrics["read_only_violations"] = 1
                        raise ValueError("Read-only task violation; no action executed")
                except Exception as exc:
                    self.metrics["failed_decision_attempts"] = (
                        self.metrics.get("failed_decision_attempts", 0) + 1
                    )
                    self.metrics["invalid_decisions"] += getattr(exc, "category", None) in {
                        "invalid_decision",
                        "incomplete_or_ambiguous_completion",
                        "provider_refusal",
                        "unexpected_tool_call",
                        "action_target_not_visible_or_enabled",
                    }
                    self.event(
                        "decision_failed",
                        index=index,
                        error_type=type(exc).__name__,
                        error_category=getattr(exc, "category", None),
                    )
                    raise
            else:
                self.metrics["status"] = "smoke_complete"
        finally:
            if policy:
                self.metrics["usage"] = policy.usage_summary()
                self.metrics["model_calls_attempted"] = self.metrics["usage"]["calls"]
                policy.close()
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def execute(self):
        # This gate precedes every CLI call, credential change and finalization mutation.
        self.require_approval()
        error = None
        try:
            self.preflight()
            self.started = self.clock()
            atomic_json(
                self.run / "raw/paid-start.json",
                {
                    "utc": datetime.now(timezone.utc).isoformat(),
                    "monotonic": self.started,
                    "work_limit_seconds": self.work_seconds,
                    "total_limit_seconds": self.total_seconds,
                },
            )

            def watchdog():
                if not self.stopped.wait(max(0, self.started + self.work_seconds - self.clock())):
                    try:
                        self.stop()
                    except Exception as exc:
                        self.event("watchdog_stop_failed", error_type=type(exc).__name__)

            threading.Thread(target=watchdog, daemon=True).start()
            self.may_exist = True
            self.metrics["status"] = "provisioning"
            self.event("deployment_started")
            self.command(
                [
                    "endpoint",
                    "create",
                    "--env",
                    "main",
                    "--name",
                    self.p["endpoint_name"],
                    "--model",
                    self.p["underlying_model"],
                    "--custom-hf-repo",
                    self.p["underlying_model"],
                    "--custom-hf-revision",
                    self.p["hf_revision"],
                    "--min-containers",
                    "0",
                    "--max-containers",
                    "1",
                    "--buffer-containers",
                    "0",
                    "--scaledown-window",
                    "2",
                ],
                "create",
                timeout=40,
            )
            self.metrics["endpoint_created"] = True
            self.smoke(self.inspect())
        except BaseException as exc:
            error = exc
            self.metrics.update(
                status="failed_or_inconclusive",
                error_type=type(exc).__name__,
                error_category=getattr(
                    exc,
                    "category",
                    str(exc) if not isinstance(exc, httpx.HTTPError) else type(exc).__name__,
                ),
            )
            self.event("run_failed", error_type=type(exc).__name__)
            print("RUN_STOPPED", type(exc).__name__, flush=True)
        finally:
            try:
                self.stop()
            finally:
                try:
                    self.cleanup_proxy()
                finally:
                    self.metrics["elapsed_paid_seconds"] = (
                        None if self.started is None else round(self.clock() - self.started, 3)
                    )
                    atomic_json(self.run / "metrics.json", self.safe(self.metrics))
                    atomic_json(
                        self.run / "finalization.json",
                        {
                            "schema_version": 1,
                            "approval_closed": True,
                            "endpoint_stopped_verified": self.metrics["endpoint_stopped_verified"],
                            "proxy_deleted": self.metrics["proxy_deleted"],
                            "utc": datetime.now(timezone.utc).isoformat(),
                        },
                    )
        return 1 if error else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    d = Diagnostic(args.run)
    if not args.execute:
        print(
            json.dumps(
                {
                    "mode": "dry_run",
                    "run_id": d.run.name,
                    "endpoint": d.p["endpoint_name"],
                    "approved_max_usd": d.p["approved_max_usd"],
                    "timing_seconds": [
                        d.p[k] for k in ("startup_seconds", "inference_seconds", "shutdown_seconds")
                    ],
                    "network_calls": 0,
                }
            )
        )
        return
    raise SystemExit(d.execute())


if __name__ == "__main__":
    main()
