"""Causal provenance for actual native tool actions, separate from driver setup."""

import json

from afterclick.agent.gateway import Gateway


class AgentGateway(Gateway):
    def __init__(self, *args, **kwargs):
        self.source = dict(
            kind="driver", actor="research-driver", model=None, revision=None, tool_call_id=None
        )
        self.operation_sources = {}
        super().__init__(*args, **kwargs)

    def _route(self, route):
        request = route.request
        headers = {
            **request.headers,
            "x-action-id": self.dispatch_id,
            "x-actor": self.source["actor"],
        }
        if request.method == "PATCH":
            data = request.post_data_json
            original = data["operation_id"]
            if original not in self.operations:
                self.operations[original] = f"{self.dispatch_id}:op{len(self.operations) + 1}"
                self.operation_actions[original] = self.dispatch_id
                self.operation_sources[original] = dict(self.source)
            data["operation_id"] = self.operations[original]
            headers["x-action-id"] = self.operation_actions[original]
            headers["x-actor"] = self.operation_sources[original]["actor"]
            route.continue_(headers=headers, post_data=json.dumps(data))
        else:
            route.continue_(headers=headers)

    def act(self, *args, **kwargs):
        try:
            return super().act(*args, **kwargs)
        finally:
            if self.history:
                self.history[-1]["source"] = dict(self.source)
