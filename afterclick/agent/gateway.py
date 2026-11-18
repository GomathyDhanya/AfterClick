from dataclasses import asdict, dataclass
from typing import Literal
from urllib.parse import urlparse

from playwright.sync_api import expect

from afterclick.infrastructure.db import digest


@dataclass(frozen=True)
class Action:
    kind: Literal["navigate", "fill", "click", "select", "read", "wait"]
    target: str
    value: str = ""


class Gateway:
    """Only UI observations and bounded actions. No DB, scheduler, or oracle reference.

    Route instrumentation stamps causal action identity and stable operation IDs;
    it never introduces a request that the application did not dispatch.
    """

    def __init__(self, page, origin):
        self.page, self.origin = page, origin
        self.history = []
        self.current_id = "initial"
        self.dispatch_id = "initial"
        self.operations = {}
        self.pending = set()
        self.requests = []
        page.route("**/api/**", self._route)
        page.on("request", self._request)
        page.on("requestfinished", self._finished)
        page.on("requestfailed", self._finished)

    def _route(self, route):
        request = route.request
        headers = {**request.headers, "x-action-id": self.dispatch_id, "x-actor": "scripted-agent"}
        if request.method == "PATCH":
            data = request.post_data_json
            original = data["operation_id"]
            if original not in self.operations:
                self.operations[original] = f"{self.dispatch_id}:op{len(self.operations) + 1}"
            data["operation_id"] = self.operations[original]
            import json

            route.continue_(headers=headers, post_data=json.dumps(data))
        else:
            route.continue_(headers=headers)

    def _request(self, request):
        if request.method == "PATCH" or (request.method == "POST" and "/comments" in request.url):
            self.pending.add(request)
            self.requests.append(
                {
                    "action_id": self.dispatch_id,
                    "method": request.method,
                    "path": urlparse(request.url).path,
                }
            )

    def _finished(self, request):
        self.pending.discard(request)

    def observe(self):
        if self.page.url == "about:blank":
            return {"text": "", "inputs": {}}
        # inner_text alone omits live textarea values and selected options.
        inputs = {}
        for label in ("Description", "Status", "Priority", "Assignee", "Comment"):
            locator = self.page.get_by_label(label, exact=True)
            if locator.count():
                inputs[label] = locator.input_value()
        return {"text": self.page.locator("body").inner_text(), "inputs": inputs}

    def act(self, action, suppress=False):
        self.current_id = f"a{len(self.history) + 1:04d}"
        observation = self.observe()
        record = {
            "action_id": self.current_id,
            "sequence": len(self.history) + 1,
            "action": asdict(action),
            "pre_observation": observation,
            "pre_observation_hash": digest(observation),
            "intervention": "suppress" if suppress else "execute",
        }
        self.history.append(record)
        if suppress:
            record["feedback"] = {"status": "suppressed", "tool_executed": False}
            return record
        try:
            if action.kind in {"fill", "click", "select"}:
                state = self.page.get_by_role("status").inner_text()
                if state != "✓ Committed":
                    raise ValueError("Settle the previous autosave before another mutating action")
            if action.kind in {"fill", "click", "select", "navigate"}:
                self.dispatch_id = self.current_id
            if action.kind == "navigate":
                if not action.target.startswith("/") or action.target.startswith("//"):
                    raise ValueError("Navigation must stay in the fixture origin")
                self.page.goto(self.origin + action.target)
                expect(self.page.get_by_label("Description", exact=True)).to_be_visible()
                expect(self.page.get_by_text("Live updates", exact=True)).to_be_visible()
            elif action.kind == "fill":
                self.page.get_by_label(action.target, exact=True).fill(action.value)
            elif action.kind == "click":
                self.page.get_by_role("button", name=action.target, exact=True).click()
            elif action.kind == "select":
                self.page.get_by_label(action.target, exact=True).select_option(action.value)
            elif action.kind == "read":
                record["value"] = self.page.get_by_label(action.target, exact=True).input_value()
            elif action.kind == "wait":
                expect(self.page.get_by_role("status")).to_have_text(action.target, timeout=5000)
            else:
                raise ValueError(f"Unsupported action {action.kind}")
            record["feedback"] = {"status": "completed", "tool_executed": True}
        except Exception as exc:
            record["feedback"] = {"status": "failed", "error": str(exc)}
            raise
        return record
