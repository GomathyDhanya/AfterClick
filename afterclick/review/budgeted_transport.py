"""Shared capped transport adapter; no default connection or implicit authorization.

Caller must hold an explicitly approved run reservation and supply an admitted
Factory. A mock httpx transport permits offline qualification without paid calls.
"""

import json
import time
from uuid import uuid4

import httpx

from afterclick.tcope.budget import Factory
from afterclick.tcope.driver import append

ENDPOINT = "https://gomathydhanya142--ep-afterclick-server.us-east.modal.direct"


class SharedFactory(Factory):
    def rows(self):
        rows = super().rows()
        path = self.run / "external-model-calls.jsonl"
        if path.exists():
            rows += [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        return rows


class BudgetedToolTransport:
    def __init__(self, factory, *, approved_reservation=None, transport=None):
        if transport is None and not approved_reservation:
            raise ValueError("Explicit approved shared reservation required before network")
        if transport is None:
            if approved_reservation.get("run_id") != factory.run.name:
                raise ValueError("Reservation/run mismatch")
            if approved_reservation.get("authorization_source") != "explicit-review-allocation":
                raise ValueError("Closed historical category cannot authorize external requests")
        self.factory = factory
        self.client = httpx.Client(timeout=30, trust_env=False, transport=transport)
        self.journal = factory.run / "external-model-calls.jsonl"

    def __call__(self, request):
        self.factory.admit()
        if time.monotonic() >= self.factory.deadline:
            raise TimeoutError("Shared deadline")
        if request.get("model") != "AfterClick" or request.get("tool_choice") != "auto":
            raise ValueError("Frozen model/native tool configuration required")
        if "response_format" in request or request.get("max_tokens") != 512:
            raise ValueError("Frozen generation format/output limit required")
        # Conservative UTF8 byte bound plus chat-frame overhead, not an exact tokenizer claim.
        encoded = json.dumps(request, ensure_ascii=False).encode("utf-8")
        if len(encoded) + 32 * len(request["messages"]) > self.factory.protocol["max_input_tokens"]:
            raise ValueError("Conservative public input-token bound exceeded")
        identity = uuid4().hex
        start = time.time()
        append(
            self.journal,
            dict(
                event="started", request_id=identity, request=request, wall=start, timestamp=start
            ),
        )
        try:
            response = self.client.post(ENDPOINT + "/v1/chat/completions", json=request)
            response.raise_for_status()
            value = response.json()
            usage = value.get("usage", {})
            if "total_tokens" not in usage:
                raise ValueError("Unknown generation usage")
            append(
                self.journal,
                dict(
                    event="finished",
                    request_id=identity,
                    response=value,
                    wall=time.time(),
                    timestamp=time.time(),
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage["total_tokens"],
                    billing_uncertain=False,
                ),
            )
            return value
        except BaseException as exc:
            append(
                self.journal,
                dict(
                    event="failed",
                    request_id=identity,
                    error_type=type(exc).__name__,
                    billing_uncertain=True,
                    wall=time.time(),
                    timestamp=time.time(),
                ),
            )
            raise

    def close(self):
        self.client.close()
