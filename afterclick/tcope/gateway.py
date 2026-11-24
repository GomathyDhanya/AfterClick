"""Gateway extension for public fake-service writes and observed HTTP acknowledgments."""

from urllib.parse import urlparse

from afterclick.model_sprint.gateway import AgentGateway


class ServiceGateway(AgentGateway):
    def _route(self, route):
        request = route.request
        if request.method == "POST" and "/comments" in request.url:
            route.continue_(
                headers={
                    **request.headers,
                    "x-action-id": self.dispatch_id,
                    "x-actor": self.source["actor"],
                    "x-tcope-operation-id": request.post_data_json["operation_id"],
                }
            )
        else:
            super()._route(route)

    def _request(self, request):
        super()._request(request)
        if request.method == "POST" and "/api/tcope/action" in request.url:
            self.pending.add(request)
            self.requests.append(
                dict(
                    action_id=self.dispatch_id,
                    method=request.method,
                    path=urlparse(request.url).path,
                    request_data=request.post_data_json,
                )
            )
