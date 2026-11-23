import hashlib
import json
from datetime import datetime, timezone

import httpx
import pytest

from afterclick.replay import adaptive_runner
from research_ops.scripts import p1_existing


def test_existing_reuse_requires_exact_approval_before_control_plane(tmp_path, monkeypatch):
    (tmp_path / "protocol.json").write_text("{}")

    def forbidden(*args, **kwargs):
        pytest.fail("Unapproved resource inspection/mutation")

    monkeypatch.setattr(p1_existing, "cli", forbidden)
    with pytest.raises(FileNotFoundError):
        p1_existing.execute(tmp_path)
    assert not (tmp_path / "finalization.json").exists()


def test_replay_fail_fast_preserves_unattempted_slots(tmp_path, monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(args)
        return {"name": args[2], "valid": False, "error": "fixture provider failure"}

    monkeypatch.setattr(adaptive_runner, "run_branch", fail)
    result = adaptive_runner.run_case(
        None, p1_existing.contracts()[0], None, tmp_path, fail_fast=True
    )
    assert len(calls) == 1 and len(result["branches"]) == 12
    assert not result["certificate"]["valid"]
    assert sum(b.get("attempted") is False for b in result["branches"].values()) == 11
    assert json.loads((tmp_path / "report.json").read_text())["comparison"]["status"] == "INVALID"


def test_valid_approval_and_frozen_contract_reach_only_read_only_preflight(tmp_path, monkeypatch):
    (tmp_path / "raw").mkdir()
    p = dict(
        endpoint_id=p1_existing.ENDPOINT,
        max_calls=40,
        total_seconds=510,
        max_compute_usd_per_second=0.00135,
        controller_sha256=hashlib.sha256(
            p1_existing.Path(p1_existing.__file__).read_bytes()
        ).hexdigest(),
        public_synthetic_task_hashes=p1_existing.task_hashes(),
    )
    (tmp_path / "protocol.json").write_text(json.dumps(p))
    (tmp_path / "approval.json").write_text(
        json.dumps(
            dict(
                approved_by_user=True,
                run_id=tmp_path.name,
                max_usd=0.90,
                protocol_sha256=hashlib.sha256(
                    (tmp_path / "protocol.json").read_bytes()
                ).hexdigest(),
            )
        )
    )
    for i, c in enumerate(p1_existing.contracts()):
        (tmp_path / "raw" / f"contract-{i}.json").write_text(c.model_dump_json())
    (tmp_path / "raw/guardrails_verified.json").write_text(
        json.dumps(
            dict(
                utc_verified=datetime.now(timezone.utc).isoformat(),
                usage_cap_usd=2,
                usage_headroom_usd=1,
                remaining_credit_usd=29,
            )
        )
    )

    class PreflightReached(Exception):
        pass

    def inspect(args, *other, **kwargs):
        assert args[:3] == ["endpoint", "info", p1_existing.ENDPOINT]
        raise PreflightReached

    monkeypatch.setattr(p1_existing, "cli", inspect)
    with pytest.raises(PreflightReached):
        p1_existing.execute(tmp_path)
    assert not (tmp_path / "raw/paid-start.json").exists()


def test_warm_metadata_failure_restores_minimum_without_stopping_endpoint(tmp_path, monkeypatch):
    (tmp_path / "raw").mkdir()
    p = dict(
        endpoint_id=p1_existing.ENDPOINT,
        max_calls=40,
        total_seconds=510,
        max_compute_usd_per_second=0.00135,
        startup_mode="bounded_min1",
        controller_sha256=hashlib.sha256(
            p1_existing.Path(p1_existing.__file__).read_bytes()
        ).hexdigest(),
        public_synthetic_task_hashes=p1_existing.task_hashes(),
    )
    (tmp_path / "protocol.json").write_text(json.dumps(p))
    (tmp_path / "approval.json").write_text(
        json.dumps(
            dict(
                approved_by_user=True,
                run_id=tmp_path.name,
                max_usd=0.90,
                temporary_min_containers=1,
                protocol_sha256=hashlib.sha256(
                    (tmp_path / "protocol.json").read_bytes()
                ).hexdigest(),
            )
        )
    )
    for i, c in enumerate(p1_existing.contracts()):
        (tmp_path / "raw" / f"contract-{i}.json").write_text(c.model_dump_json())
    (tmp_path / "raw/guardrails_verified.json").write_text(
        json.dumps(
            dict(
                utc_verified=datetime.now(timezone.utc).isoformat(),
                usage_cap_usd=2,
                usage_headroom_usd=1,
                remaining_credit_usd=29,
            )
        )
    )
    minimum = [0]
    commands = []

    def control(args, output, **kwargs):
        commands.append(args)
        if args[:2] == ["endpoint", "info"]:
            data = dict(
                repo_id=p1_existing.MODEL,
                revision=p1_existing.REVISION,
                model_name="AfterClick",
                serving_mode="dedicated",
                status="live",
                requires_proxy_auth=False,
                service_url="https://test.modal.direct",
                server_id="fu-test",
                app_id="ap-test",
            )
        elif args[:3] == ["server", "autoscaler", "update"]:
            minimum[0] = int(args[args.index("--min-containers") + 1])
            data = {}
        elif args[:3] == ["server", "autoscaler", "settings"]:
            data = dict(
                current_settings=dict(
                    min_containers=minimum[0],
                    max_containers=1,
                    buffer_containers=0,
                    scaledown_window=2,
                )
            )
        elif args[:2] == ["server", "info"]:
            data = dict(cpu=4, memory_mib=16384, gpus=[["H100", 1]])
        elif args[:2] == ["billing", "rates"]:
            data = dict(gpu_hour_cost_h100="3.95", cpu_hour_cost=".0473", mem_gib_hour_cost=".008")
        elif args[:2] == ["endpoint", "logs"]:
            assert "--since" in args
            output.write_text("AfterClick (H100:1) sglang deployment is ready.")
            return output.read_text()
        elif args[:2] == ["container", "list"]:
            data = []
        else:
            pytest.fail(str(args))
        output.write_text(json.dumps(data))
        return output.read_text()

    monkeypatch.setattr(p1_existing, "cli", control)
    requests = []
    original = httpx.Client

    def respond(request):
        requests.append(request)
        assert "authorization" not in request.headers
        return httpx.Response(503, text="cold test error")

    monkeypatch.setattr(
        p1_existing.httpx,
        "Client",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    assert p1_existing.execute(tmp_path) == 1
    assert len(requests) == 1 and minimum[0] == 0
    final = json.loads((tmp_path / "finalization.json").read_text())
    assert final["min0_restored"] and final["idle_verified"] and final["endpoint_preserved"]
    assert json.loads((tmp_path / "raw/models-response.json").read_text())["status"] == 503
    assert all(args[:2] not in [["endpoint", "create"], ["endpoint", "stop"]] for args in commands)
