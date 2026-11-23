import io
import json
import sys
import time

import pytest

from research_ops.scripts import modal_lifecycle as lifecycle


def setup_run(tmp_path, monkeypatch):
    run = tmp_path / "run"
    (run / "raw").mkdir(parents=True)
    (run / "protocol.json").write_text(
        json.dumps(
            {
                "approved_by_user": True,
                "max_usd": 2,
                "workspace": "test",
                "underlying_model": "Qwen/Qwen3.5-9B",
                "hf_revision": "fixed",
            }
        )
    )
    (run / "raw/guardrails_verified.json").write_text(
        json.dumps({"usage_cap_usd": 2, "effective_net_spend_limit_usd": 0})
    )
    monkeypatch.setattr(lifecycle, "RUN", run)
    monkeypatch.setattr(lifecycle, "LOG_DIR", run / "raw")
    monkeypatch.setattr(sys, "argv", ["modal_lifecycle"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("stop\n"))
    return run


def test_lifecycle_stops_without_interactive_confirmation(tmp_path, monkeypatch):
    run = setup_run(tmp_path, monkeypatch)
    active = [False]
    calls = []

    def cli(args, name, timeout=30):
        calls.append(args)
        if args[0] == "profile":
            return "test"
        if args[:2] == ["endpoint", "list"]:
            return json.dumps([{"name": lifecycle.NAME}] if active[0] else [])
        if args[:2] == ["endpoint", "create"]:
            active[0] = True
            return "created"
        if args[:2] == ["endpoint", "info"]:
            return json.dumps({"app_id": "test-app", "service_url": "https://test.modal.direct"})
        if args[:2] == ["app", "info"]:
            return "{}"
        if args[:2] == ["endpoint", "stop"]:
            if "--yes" not in args:
                raise RuntimeError("Interactive confirmation would block")
            active[0] = False
            return "stopped"
        raise AssertionError(args)

    monkeypatch.setattr(lifecycle, "cli", cli)
    lifecycle.main()
    assert not active[0]
    assert json.loads((run / "raw/lifecycle-finished.json").read_text())["stop_confirmed"]
    assert sum(c[:2] == ["endpoint", "create"] for c in calls) == 1


@pytest.mark.parametrize("guard", ["finalized", "deadline"])
def test_finalized_or_expired_run_cannot_create_resource(tmp_path, monkeypatch, guard):
    run = setup_run(tmp_path, monkeypatch)
    if guard == "finalized":
        (run / "finalization.json").write_text("{}")
    else:
        (run / "raw/lifecycle-start.json").write_text(
            json.dumps({"started_epoch": time.time() - 200})
        )
    calls = []

    def cli(args, name, timeout=30):
        calls.append(args)
        if args[0] == "profile":
            return "test"
        if args[:2] == ["endpoint", "list"]:
            return "[]"
        raise AssertionError("No resource-creating call should be possible")

    monkeypatch.setattr(lifecycle, "cli", cli)
    with pytest.raises(RuntimeError):
        lifecycle.main()
    assert not any(c[:2] == ["endpoint", "create"] for c in calls)
