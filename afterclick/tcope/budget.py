"""One paid-run envelope shared across conversations, arms and shadow branches."""

import json
import time
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from afterclick.agent.modal_policy import InferenceError, Limits, atomic_json, digest
from afterclick.model_sprint.policy import NaturalConfig, NaturalPolicy
from afterclick.tcope.policy import ExecutionConfig, ExecutionPolicy


class GuardedPolicy:
    def __init__(self, policy, factory):
        object.__setattr__(self, "policy", policy)
        object.__setattr__(self, "factory", factory)

    def __getattr__(self, key):
        return getattr(self.policy, key)

    def __setattr__(self, key, value):
        setattr(self.policy, key, value)

    def decide(self, *args, **kwargs):
        self.factory.admit()
        return self.policy.decide(*args, **kwargs)


class Factory:
    def __init__(
        self, run, protocol, info, deadline, credit, *, transport=None, startup_elapsed_seconds=None
    ):
        self.run, self.protocol, self.info, self.deadline = run, protocol, info, deadline
        self.credit, self.transport = credit, transport
        if protocol.get("shared_wall_envelope") and startup_elapsed_seconds is None:
            raise ValueError("Measured startup duration required for shared wall envelope")
        startup_allowance = (
            startup_elapsed_seconds
            if protocol.get("shared_wall_envelope")
            else protocol["startup_seconds"]
        )
        self.instances = []
        self.trial_call_start = None
        self.trial_call_cap = None
        self.settings = {}
        for label, cap in protocol["arm_call_caps"].items():
            cls = NaturalConfig if label == "legacy" else ExecutionConfig
            config = cls(
                endpoint_url=info["service_url"],
                endpoint_name=info["model_name"],
                underlying_model=info["repo_id"],
                model_revision=info["revision"],
                max_input_tokens=protocol["max_input_tokens"],
                max_output_tokens=protocol["max_output_tokens"],
                timeout_seconds=protocol["request_timeout_seconds"],
            )
            limits = Limits(
                max_calls=cap,
                max_total_tokens=cap * (config.max_input_tokens + config.max_output_tokens),
                max_wall_seconds=max(30, int(deadline - time.monotonic())),
                max_usd=protocol["max_usd"],
            )
            approval = dict(
                approved_by_user=True,
                run_id=run.name,
                config_sha256=config.fingerprint,
                limits_sha256=digest(asdict(limits)),
                max_usd=protocol["max_usd"],
                available_compute_credit_usd=credit,
                credit_verified=True,
                max_compute_usd_per_second=protocol["max_rate_usd_per_second"],
                startup_allowance_seconds=startup_allowance,
                shutdown_allowance_seconds=protocol["cleanup_seconds"],
                expires_utc=(
                    datetime.now(timezone.utc)
                    + timedelta(seconds=max(1, deadline - time.monotonic()))
                ).isoformat(),
                allow_public_synthetic=True,
                public_synthetic_task_hashes=protocol["public_task_hashes"],
                authorization_source="research_ops/UNIFIED_AUTHORIZATION.json",
            )
            path = run / "raw" / f"{label}-approval.json"
            atomic_json(path, approval)
            self.settings[label] = (config, limits, path)

    def make(self, label="corrected"):
        config, limits, approval = self.settings[label]
        cls = NaturalPolicy if label == "legacy" else ExecutionPolicy
        kwargs = (
            dict(transport=self.transport)
            if self.transport
            else dict(
                mode="live",
                approval_path=approval,
                public_synthetic_task_hashes=self.protocol["public_task_hashes"],
            )
        )
        policy = cls(config, limits, journal=self.run / f"{label}-model-calls.jsonl", **kwargs)
        self.instances.append(policy)
        return GuardedPolicy(policy, self)

    def rows(self):
        return (
            [
                json.loads(line)
                for label in self.settings
                for line in (self.run / f"{label}-model-calls.jsonl").read_text().splitlines()
            ]
            if all((self.run / f"{label}-model-calls.jsonl").exists() for label in self.settings)
            else [
                json.loads(line)
                for label in self.settings
                if (self.run / f"{label}-model-calls.jsonl").exists()
                for line in (self.run / f"{label}-model-calls.jsonl").read_text().splitlines()
            ]
        )

    def usage(self):
        rows = self.rows()
        starts = [r for r in rows if r["event"] == "started"]
        ends = [r for r in rows if r["event"] == "finished"]
        return dict(
            calls=len(starts),
            known_total_tokens=sum(r.get("total_tokens", 0) for r in ends),
            input_tokens=sum(r.get("input_tokens", 0) for r in ends),
            output_tokens=sum(r.get("output_tokens", 0) for r in ends),
            uncertain=bool({r["request_id"] for r in starts} - {r["request_id"] for r in ends})
            or any(r.get("billing_uncertain", False) for r in ends),
        )

    def admit(self):
        usage = self.usage()
        if usage["uncertain"]:
            raise InferenceError("global_request_outcome_unknown")
        if usage["calls"] >= self.protocol["max_calls"]:
            raise InferenceError("global_call_budget_exhausted")
        if (
            self.trial_call_start is not None
            and usage["calls"] - self.trial_call_start >= self.trial_call_cap
        ):
            raise InferenceError("trial_call_budget_exhausted")
        reserve = self.protocol["max_input_tokens"] + self.protocol["max_output_tokens"]
        if usage["known_total_tokens"] + reserve > self.protocol["max_total_reserved_tokens"]:
            raise InferenceError("global_token_budget_exhausted")
        if time.monotonic() + self.protocol["request_timeout_seconds"] + 8 >= self.deadline:
            raise InferenceError("global_wall_budget_exhausted")

    def begin_trial(self, cap):
        if self.trial_call_start is not None:
            raise ValueError("Nested trial budget forbidden; forecasts share parent budget")
        self.trial_call_start = self.usage()["calls"]
        self.trial_call_cap = cap

    def remaining_trial_calls(self):
        return min(
            self.protocol["max_calls"] - self.usage()["calls"],
            self.trial_call_cap - (self.usage()["calls"] - self.trial_call_start)
            if self.trial_call_start is not None
            else self.protocol["max_calls"],
        )

    def end_trial(self):
        self.trial_call_start = self.trial_call_cap = None

    def close(self):
        for p in self.instances:
            p.close()
        with (self.run / "model_calls.jsonl").open("w") as f:
            for row in sorted(
                self.rows(), key=lambda r: r.get("timestamp_finished", r["timestamp"])
            ):
                f.write(json.dumps(row) + "\n")
