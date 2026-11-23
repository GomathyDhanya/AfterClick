"""Bounded Dedicated Endpoint adapter. HTTPX only; no Modal GPU creation.

Default mode is mock and requires httpx.MockTransport. Live mode requires a
separate, matching user-approval record and proxy credentials in the environment.
Compute estimates are conservative admission guards, never a hard billing cap.
"""

import fcntl
import hashlib
import json
import math
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

from afterclick.agent.action_parser import Decision, parse_action
from afterclick.agent.inference import public_input
from afterclick.agent.llm_policy import SYSTEM_PROMPT, PolicyError


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


class InferenceError(PolicyError):
    def __init__(self, category):
        self.category = category
        super().__init__(category)


@dataclass(frozen=True)
class ModalConfig:
    endpoint_url: str
    endpoint_name: str
    underlying_model: str = "Qwen/Qwen3.5-9B"
    model_revision: str | None = None
    temperature: float = 0
    max_output_tokens: int = 256
    max_input_tokens: int = 8192
    thinking: bool = False
    timeout_seconds: float = 90
    response_format: str = "json_schema"
    retries: int = 0

    def __post_init__(self):
        url = urlsplit(self.endpoint_url)
        if (
            url.scheme != "https"
            or not url.hostname
            or not url.hostname.endswith(".modal.direct")
            or url.hostname.startswith("inference.")
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
            or url.port
        ):
            raise ValueError("Authenticated dedicated modal.direct base URL required")
        if not self.endpoint_name or not self.underlying_model:
            raise ValueError(
                "API model name and underlying repository ID are distinct required fields"
            )
        if not math.isfinite(self.temperature) or not 0 <= self.temperature <= 2:
            raise ValueError("Invalid temperature")
        if (
            type(self.max_output_tokens) is not int
            or type(self.max_input_tokens) is not int
            or not 32 <= self.max_output_tokens <= 1024
            or not 2048 <= self.max_input_tokens <= 16384
        ):
            raise ValueError("Bounded input/output token limits required")
        if not 1 <= self.timeout_seconds <= 120 or self.retries != 0:
            raise ValueError("Finite timeout and zero automatic retries required")
        if self.response_format not in {"json_schema", "json_object"}:
            raise ValueError("Explicit JSON protocol required; no silent tool/schema fallback")

    @property
    def fingerprint(self):
        return digest(asdict(self))


@dataclass(frozen=True)
class Limits:
    max_calls: int = 20
    max_total_tokens: int = 180000
    max_wall_seconds: int = 600
    max_usd: float = 0

    def __post_init__(self):
        if (
            type(self.max_calls) is not int
            or type(self.max_total_tokens) is not int
            or not 1 <= self.max_calls <= 80
            or self.max_total_tokens < 1
        ):
            raise ValueError("Positive bounded call/token caps required")
        if (
            type(self.max_wall_seconds) is not int
            or not 1 <= self.max_wall_seconds <= 1800
            or not math.isfinite(self.max_usd)
            or self.max_usd < 0
        ):
            raise ValueError("Finite run and dollar caps required")


def request_body(config, payload, *, argument_contract="legacy"):
    schema = Decision.model_json_schema()
    instructions = SYSTEM_PROMPT
    if argument_contract == "conditional-v2":
        from afterclick.agent.decision_schema import ARGUMENT_INSTRUCTIONS, conditional_schema

        schema = conditional_schema()
        instructions += ARGUMENT_INSTRUCTIONS
    response_format = {"type": config.response_format}
    if config.response_format == "json_schema":
        response_format["json_schema"] = {
            "name": "browser_decision",
            "strict": True,
            "schema": schema,
        }
    return {
        "model": config.endpoint_name,
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": json.dumps(payload, sort_keys=True, ensure_ascii=False)},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_output_tokens,
        "stream": False,
        "response_format": response_format,
        "chat_template_kwargs": {"enable_thinking": config.thinking},
    }


class ModalPolicy:
    def __init__(
        self,
        config,
        limits,
        *,
        journal,
        mode="mock",
        transport=None,
        approval_path=None,
        cache_dir=None,
        clock=time.time,
        public_synthetic_task_hashes=None,
        argument_contract="legacy",
    ):
        self.config, self.limits = config, limits
        if config.timeout_seconds > limits.max_wall_seconds:
            raise ValueError("Request timeout must fit the run wall-time cap")
        self.journal = Path(journal)
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        self.mode, self.clock = mode, clock
        self.records = []
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._mutex = threading.Lock()
        self.approval = None
        if argument_contract not in {"legacy", "conditional-v2"}:
            raise ValueError("Unknown argument contract version")
        if argument_contract != "legacy" and config.response_format != "json_schema":
            raise ValueError("Conditional argument contract requires explicit JSON schema")
        self.argument_contract = argument_contract
        self.public_task_hashes = (
            tuple(sorted(public_synthetic_task_hashes))
            if public_synthetic_task_hashes is not None
            else None
        )
        if self.public_task_hashes is not None and (
            not self.public_task_hashes
            or any(
                len(h) != 64 or any(c not in "0123456789abcdef" for c in h)
                for h in self.public_task_hashes
            )
        ):
            raise ValueError("Public synthetic mode requires registered task hashes")
        self._credential = "MOCK-NOT-A-CREDENTIAL"
        if mode == "mock":
            if not isinstance(transport, httpx.MockTransport):
                raise ValueError("Mock mode requires HTTPX MockTransport; network access forbidden")
        elif mode == "live":
            if transport is not None:
                raise ValueError("Live transport must use the configured authenticated endpoint")
            self.approval = self._approval(approval_path)
            if self.public_task_hashes is None:
                token_id = os.environ.get("MODAL_PROXY_TOKEN_ID", "")
                secret = os.environ.get("MODAL_PROXY_TOKEN_SECRET", "")
                if not token_id.startswith("wk-") or not secret.startswith("ws-"):
                    raise InferenceError("missing_proxy_credentials")
                self._credential = token_id + "." + secret
        else:
            raise ValueError("Explicit mock or approved live mode required")
        if self.public_task_hashes is not None:
            self._credential = ""
        self.evidence_kind = "mock_openai_responses" if mode == "mock" else "live_modal"
        self.client = httpx.Client(
            transport=transport,
            timeout=config.timeout_seconds,
            follow_redirects=False,
            trust_env=False,
        )
        settings = {"config": asdict(config), "limits": asdict(limits), "mode": mode}
        if self.public_task_hashes is not None:
            settings["public_synthetic_task_hashes"] = self.public_task_hashes
        if self.argument_contract != "legacy":
            settings["argument_contract"] = self.argument_contract
        self._settings_hash = digest(settings)

    def _approval(self, path):
        if path is None:
            raise InferenceError("paid_approval_required")
        approval = json.loads(Path(path).read_text())
        required = {
            "approved_by_user",
            "run_id",
            "config_sha256",
            "limits_sha256",
            "max_usd",
            "available_compute_credit_usd",
            "credit_verified",
            "max_compute_usd_per_second",
            "startup_allowance_seconds",
            "shutdown_allowance_seconds",
            "expires_utc",
        }
        if not required <= approval.keys():
            raise InferenceError("incomplete_paid_approval")
        if (
            self.argument_contract != "legacy"
            and approval.get("argument_contract") != self.argument_contract
        ):
            raise InferenceError("argument_contract_approval_required")
        if self.public_task_hashes is not None and (
            approval.get("allow_public_synthetic") is not True
            or approval.get("public_synthetic_task_hashes") != list(self.public_task_hashes)
        ):
            raise InferenceError("public_synthetic_approval_required")
        rate = approval["max_compute_usd_per_second"]
        numbers = [
            approval[k]
            for k in (
                "max_usd",
                "available_compute_credit_usd",
                "max_compute_usd_per_second",
                "startup_allowance_seconds",
                "shutdown_allowance_seconds",
            )
        ]
        if any(type(n) not in (int, float) or not math.isfinite(n) for n in numbers):
            raise InferenceError("invalid_approval_numbers")
        if (
            approval["approved_by_user"] is not True
            or approval["credit_verified"] is not True
            or approval["config_sha256"] != self.config.fingerprint
            or approval["limits_sha256"] != digest(asdict(self.limits))
            or not 0 < self.limits.max_usd <= approval["max_usd"] <= 2
            or approval["max_usd"] > approval["available_compute_credit_usd"] - 5
            or not math.isfinite(rate)
            or not 0 < rate <= 0.01
            or min(approval["startup_allowance_seconds"], approval["shutdown_allowance_seconds"])
            < 0
            or datetime.fromisoformat(approval["expires_utc"]).timestamp() <= self.clock()
        ):
            raise InferenceError("paid_approval_mismatch_or_expired")
        seconds = (
            self.limits.max_wall_seconds
            + approval["startup_allowance_seconds"]
            + approval["shutdown_allowance_seconds"]
        )
        if seconds * rate > self.limits.max_usd * 0.8:
            raise InferenceError("insufficient_compute_cost_buffer")
        return approval

    def _encoded(self, record):
        # Never serialize credential headers or exception messages. Redact response echoes.
        raw = json.dumps(record, allow_nan=False)
        for secret in (self._credential, *self._credential.split(".")):
            if secret:
                raw = raw.replace(secret, "[REDACTED]")
        return raw

    def _append(self, record):
        raw = self._encoded(record)
        with Path(self.journal).open("a") as stream:
            stream.write(raw + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def _rows(self):
        try:
            return [json.loads(line) for line in Path(self.journal).read_text().splitlines()]
        except FileNotFoundError:
            return []
        except (ValueError, TypeError):
            raise InferenceError("corrupt_journal") from None

    def usage_summary(self):
        rows = self._rows()
        starts = [r for r in rows if r["event"] == "started"]
        terminal = {r["request_id"]: r for r in rows if r["event"] == "finished"}
        unfinished = [r for r in starts if r["request_id"] not in terminal]
        paid_rows = [terminal[r["request_id"]] for r in starts if r["request_id"] in terminal]
        uncertain = bool(unfinished) or any(r.get("billing_uncertain") for r in paid_rows)
        tokens = sum(r.get("total_tokens", 0) for r in paid_rows)
        reserved = sum(r["reserved_tokens"] for r in unfinished)
        reserved += sum(
            r.get("reserved_tokens", 0) for r in paid_rows if r.get("billing_uncertain")
        )
        return {
            "calls": len(starts),
            "known_total_tokens": tokens,
            "reserved_tokens": reserved,
            "uncertain": uncertain,
            "cache_hits": sum(
                r.get("evidence_kind") == "cached_model_response" for r in terminal.values()
            ),
            "first_started": min((r["timestamp"] for r in starts), default=None),
            "modal_cost_usd": 0 if self.mode == "mock" else None,
        }

    def _admit(self, rows, request_id):
        if any(r["settings_hash"] != self._settings_hash for r in rows):
            raise InferenceError("journal_configuration_mismatch")
        if any(r["request_id"] == request_id for r in rows):
            raise InferenceError("duplicate_request_id")
        summary = self.usage_summary()
        if summary["uncertain"]:
            raise InferenceError("prior_completion_or_billing_unknown")
        if self.approval:
            self._approval_data_still_current()
        first = summary["first_started"]
        if first is not None and self.clock() < first:
            raise InferenceError("wall_clock_moved_backwards")
        if (
            first is not None
            and self.clock() - first + self.config.timeout_seconds > self.limits.max_wall_seconds
        ):
            raise InferenceError("wall_time_budget_exhausted")
        return summary

    def _approval_data_still_current(self):
        if datetime.fromisoformat(self.approval["expires_utc"]).timestamp() <= self.clock():
            raise InferenceError("paid_approval_expired")

    def decide(self, task, observation, history, *, request_id=None):
        if not self._mutex.acquire(blocking=False):
            raise InferenceError("concurrency_limit")
        lock = Path(str(self.journal) + ".lock").open("a")
        try:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise InferenceError("concurrency_limit") from None
            return self._decide(task, observation, history, request_id or uuid4().hex)
        finally:
            lock.close()
            self._mutex.release()

    def _decide(self, task, observation, history, request_id):
        record = {
            "schema_version": 1,
            "request_id": request_id,
            "event": "finished",
            "settings_hash": self._settings_hash,
            "config_sha256": self.config.fingerprint,
            "config": asdict(self.config),
            "evidence_kind": self.evidence_kind,
            "timestamp": self.clock(),
            "status": "rejected",
            "billing_uncertain": False,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        started = False
        try:
            try:
                payload = public_input(task, observation, history)
            except (ValueError, TypeError):
                raise InferenceError("invalid_public_input") from None
            if self.public_task_hashes is not None:
                if digest(payload["task"]) not in self.public_task_hashes:
                    raise InferenceError("unregistered_public_synthetic_task")
                if any(h["feedback"] == "suppressed" for h in payload["history"]):
                    raise InferenceError("hidden_intervention_feedback")
                record["authentication_mode"] = "public_synthetic_no_credentials"
            body = request_body(self.config, payload, argument_contract=self.argument_contract)
            if self.argument_contract != "legacy":
                record["argument_contract"] = self.argument_contract
            # Byte-based admission with template allowance; also check actual server usage.
            if (
                len(json.dumps(body, ensure_ascii=False).encode()) + 1024
                > self.config.max_input_tokens
            ):
                raise InferenceError("context_budget_exhausted")
            record["request"] = body
            record["request_sha256"] = digest(body)
            summary = self._admit(self._rows(), request_id)
            key = digest({"config": asdict(self.config), "request": body})
            cache = self.cache_dir / (key + ".json") if self.cache_dir else None
            if cache and cache.exists():
                saved = json.loads(cache.read_text())
                if saved["request_sha256"] != record["request_sha256"]:
                    raise InferenceError("cache_provenance_mismatch")
                decision = parse_action(json.dumps(saved["decision"]))
                record.update(
                    status="completed",
                    evidence_kind="cached_model_response",
                    source_request_id=saved["request_id"],
                    decision=decision.model_dump(),
                )
                return decision
            reserve = self.config.max_input_tokens + self.config.max_output_tokens
            if summary["calls"] >= self.limits.max_calls:
                raise InferenceError("request_budget_exhausted")
            if summary["known_total_tokens"] + reserve > self.limits.max_total_tokens:
                raise InferenceError("token_budget_exhausted")
            record.update(event="started", status="pending", reserved_tokens=reserve)
            self._append(record)
            started = True
            begin = time.monotonic()
            try:
                response = self.client.post(
                    self.config.endpoint_url.rstrip("/") + "/v1/chat/completions",
                    headers={
                        **(
                            {"Authorization": "Bearer " + self._credential}
                            if self.public_task_hashes is None
                            else {}
                        ),
                        "Idempotency-Key": request_id,
                    },
                    json=body,
                )
            except httpx.TimeoutException:
                raise InferenceError("provider_timeout") from None
            except httpx.HTTPError:
                raise InferenceError("provider_connection_failure") from None
            finally:
                record["latency_ms"] = round((time.monotonic() - begin) * 1000)
            record["http_status"] = response.status_code
            record["response_body_sha256"] = hashlib.sha256(response.content).hexdigest()
            record["response_bytes"] = len(response.content)
            if len(response.content) <= 100000:
                record["raw_response_text"] = response.text
            if response.status_code != 200:
                raise InferenceError("http_" + str(response.status_code))
            if len(response.content) > 100000:
                raise InferenceError("oversized_provider_response")
            try:
                reply = response.json()
                usage = reply["usage"]
                incoming, outgoing, total = (
                    usage[k] for k in ("prompt_tokens", "completion_tokens", "total_tokens")
                )
                if (
                    any(type(n) is not int for n in (incoming, outgoing, total))
                    or incoming < 1
                    or outgoing < 0
                    or total != incoming + outgoing
                ):
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                raise InferenceError("invalid_usage_or_response_json") from None
            record.update(
                input_tokens=incoming,
                output_tokens=outgoing,
                total_tokens=total,
                usage_known=True,
                response=reply,
                resolved_model=reply.get("model"),
            )
            if incoming > self.config.max_input_tokens or outgoing > self.config.max_output_tokens:
                raise InferenceError("provider_exceeded_token_reservation")
            if reply.get("model") not in {self.config.endpoint_name, self.config.underlying_model}:
                raise InferenceError("served_model_mismatch")
            choices = reply.get("choices", [])
            if len(choices) != 1 or choices[0].get("finish_reason") != "stop":
                raise InferenceError("incomplete_or_ambiguous_completion")
            message = choices[0].get("message", {})
            if message.get("tool_calls") or message.get("function_call"):
                raise InferenceError("unexpected_tool_call")
            if message.get("refusal"):
                raise InferenceError("provider_refusal")
            try:
                decision = parse_action(message.get("content"))
            except (ValueError, TypeError):
                raise InferenceError("invalid_decision") from None
            if decision.kind == "click" and not any(
                c["role"] == "button" and c["name"] == decision.target and c["enabled"]
                for c in observation["controls"]
            ):
                raise InferenceError("action_target_not_visible_or_enabled")
            record.update(status="completed", decision=decision.model_dump())
            if cache:
                atomic_json(
                    cache,
                    {
                        "decision": decision.model_dump(),
                        "request_id": request_id,
                        "request_sha256": record["request_sha256"],
                    },
                )
            return decision
        except BaseException as exc:
            category = exc.category if isinstance(exc, InferenceError) else "internal_adapter_error"
            record.update(
                status="failed" if started else "rejected",
                error_category=category,
                billing_uncertain=started
                and (
                    not record.get("usage_known")
                    or category == "provider_exceeded_token_reservation"
                ),
            )
            if isinstance(exc, InferenceError):
                raise
            if not isinstance(exc, Exception):
                raise
            raise InferenceError(category) from None
        finally:
            event = "finished" if started or record["status"] == "completed" else "rejected"
            record.update(event=event, timestamp_finished=self.clock())
            self.records.append(json.loads(self._encoded(record)))
            self._append(record)

    def close(self):
        self.client.close()


class RecordedOpenAIPolicy:
    evidence_kind = "recorded_model_responses"

    def __init__(self, config, records):
        self.config = config
        self.remaining = iter(records)
        self.records = []
        self.journal = None

    def decide(self, task, observation, history):
        source = next(self.remaining, None)
        body = request_body(
            self.config,
            public_input(task, observation, history),
            argument_contract=source.get("argument_contract", "legacy") if source else "legacy",
        )
        if (
            not source
            or source.get("status") != "completed"
            or source.get("request") != body
            or source.get("config_sha256") != self.config.fingerprint
        ):
            raise InferenceError("recorded_input_or_config_mismatch")
        decision = parse_action(json.dumps(source["decision"]))
        self.records.append({**source, "evidence_kind": self.evidence_kind})
        return decision
