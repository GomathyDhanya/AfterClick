"""Opt-in executable client snapshots with explicit unsupported transport boundaries."""

import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import expect

from afterclick.agent.browser_observation import observe
from afterclick.tcope.gateway import ServiceGateway


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def attach(page, origin, world, checkpoint=None):
    gateway = ServiceGateway(page, origin)
    dist = Path("artifacts/oecr-web/dist")

    def route(request):
        path = urlparse(request.request.url).path
        if path == "/":
            html = (dist / "index.html").read_text()
            bootstrap = ""
            if checkpoint:
                value = json.dumps(checkpoint["client"]).replace("<", "\\u003c")
                panel = json.dumps(checkpoint["browser_payload"]).replace("<", "\\u003c")
                bootstrap = (
                    f"<script>window.oecrBootstrap={value};window.tcBootstrap={panel};</script>"
                )
            html = html.replace("<head>", "<head>" + bootstrap)
            html = html.replace("</body>", '<script src="/tcope-panel.js"></script></body>')
            request.fulfill(body=html, content_type="text/html")
        elif path.startswith("/assets/") and (dist / path.lstrip("/")).is_file():
            request.fulfill(path=str(dist / path.lstrip("/")))
        elif path == "/api/events" and checkpoint:
            request.fallback(
                headers={**request.request.headers, "Last-Event-ID": checkpoint["client"]["cursor"]}
            )
        else:
            request.fallback()

    page.route("**/*", route)
    page.goto(origin)
    expect(page.get_by_label("Description", exact=True)).to_be_visible()
    expect(page.get_by_text("Live updates", exact=True)).to_be_visible()
    world.browser_ready(page)
    return gateway


def capture(world, gateway, conversation):
    page = gateway.page
    page.evaluate("window.oecr.pause()")
    world.browser_pause(page)
    client = page.evaluate("window.oecr.capture()")
    if gateway.pending:
        raise ValueError("OECR_UNSUPPORTED_INFLIGHT_GATEWAY")
    before = world.snapshot()
    observation = observe(gateway)
    after = world.snapshot()
    if before != after:
        raise ValueError("OECR_INCONSISTENT_CAPTURE")
    cp = dict(
        schema_version=1,
        world=before,
        initial_state=before,
        client=client,
        observation=observation,
        browser_payload=world.browser_checkpoint(page, observation),
        conversation=copy.deepcopy(conversation),
    )
    return dict(payload=cp, sha256=digest(cp))


def validate(envelope):
    if set(envelope) != {"payload", "sha256"} or digest(envelope["payload"]) != envelope["sha256"]:
        raise ValueError("OECR_CHECKPOINT_INTEGRITY")
    return copy.deepcopy(envelope["payload"])


def certify(world, gateway, checkpoint, conversation):
    actual = observe(gateway)
    checks = dict(
        world_equal=world.snapshot() == checkpoint["world"],
        observation_equal=actual == checkpoint["observation"],
        client_equal=gateway.page.evaluate("window.oecr.capture()") == checkpoint["client"],
        conversation_equal=conversation == checkpoint["conversation"],
    )
    # Paused relative timers are preserved exactly; they resume from the declared cut.
    original = copy.deepcopy(checkpoint["client"])
    current = gateway.page.evaluate("window.oecr.capture()")
    checks["client_equal"] = original == current
    return dict(
        checks=checks,
        valid=all(checks.values()),
        client_differences=[key for key in original if original[key] != current[key]],
        debounce_timing_scope="Remaining relative delay resumes; no claim of OS timer identity",
    )
