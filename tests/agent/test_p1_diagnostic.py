import hashlib
import json

import pytest

from research_ops.scripts import p1_diagnostic as module


def resources():
    return {
        "min_containers": 0,
        "max_containers": 1,
        "buffer_containers": 0,
        "scaledown_window": 2,
        "cpu": [2, 4],
        "memory_mib": [16384, 32768],
        "gpus": [["H100", 1]],
    }


RATES = {"gpu_hour_cost_h100": "3.95", "cpu_hour_cost": ".0473", "mem_gib_hour_cost": ".008"}


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_containers", 2),
        ("min_containers", 1),
        ("cpu", None),
        ("memory_mib", None),
        ("gpus", []),
    ],
)
def test_resource_admission_rejects_unapproved_or_uninspectable(field, value):
    data = resources()
    data[field] = value
    with pytest.raises(ValueError):
        module.resource_estimate(data, RATES)


def test_resource_estimate_uses_limits_and_labels_scalar_assumptions():
    data = resources()
    result = module.resource_estimate(data, RATES)
    assert result["usd_per_second_estimate"] < 0.0021
    assert result["cpu_pricing_basis"] == "configured_limit"
    data.update(cpu=2, memory_mib=8192)
    result = module.resource_estimate(data, RATES)
    assert result["cpu_priced_cores"] == 4 and result["memory_priced_mib"] == 16384
    assert not result["is_hard_billing_bound"]


@pytest.mark.parametrize("ready", [True, False])
@pytest.mark.parametrize("small", [True, False])
def test_controller_ready_or_timeout_always_stops_without_retry(
    tmp_path, monkeypatch, ready, small
):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    run = tmp_path / "artifacts/research_runs/test"
    (run / "raw").mkdir(parents=True)
    p = {
        "run_id": "test",
        "approved_by_user": True,
        "approved_max_usd": 2,
        "startup_seconds": 240,
        "inference_seconds": 60,
        "shutdown_seconds": 60,
        "max_calls": 20,
        "endpoint_name": "test-model",
        "underlying_model": "Qwen/Qwen3.5-9B",
        "hf_revision": "fixed",
        "max_compute_usd_per_second": 0.0021,
    }
    if small:
        p.update(
            underlying_model="Qwen/Qwen3.5-4B",
            hf_revision="851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
            startup_seconds=480,
            max_calls=1,
            max_total_tokens=8448,
            retries=0,
            approved_max_usd=1.5,
        )
    (run / "protocol.json").write_text(json.dumps(p))
    if small:
        (run / "approval.json").write_text(
            json.dumps(
                dict(
                    approved_by_user=True,
                    run_id="test",
                    max_usd=1.5,
                    protocol_sha256=hashlib.sha256(
                        (run / "protocol.json").read_bytes()
                    ).hexdigest(),
                )
            )
        )
    now = [0.0]
    active = [False]
    calls = []
    d = module.Diagnostic(run, clock=lambda: now[0], sleep=lambda n: now.__setitem__(0, now[0] + n))

    def command(args, label, timeout=20):
        now[0] += 1
        calls.append(args)
        if args[:2] == ["endpoint", "create"]:
            active[0] = True
            return "created"
        if args[:2] == ["endpoint", "info"]:
            return json.dumps(
                {
                    "status": "live" if ready else "provisioning",
                    "server_id": "fu-test",
                    "service_url": "https://test.modal.direct",
                    "repo_id": p["underlying_model"],
                    "revision": p["hf_revision"],
                    "requires_proxy_auth": True,
                    "serving_mode": "dedicated",
                }
            )
        if args[:2] == ["server", "info"]:
            return json.dumps(resources())
        if args[:2] == ["endpoint", "logs"]:
            # Managed provisioning may expose no server logs yet; still reach cleanup.
            raise RuntimeError("No backing server")
        if args[:2] == ["endpoint", "stop"]:
            assert "--yes" in args
            active[0] = False
            return "stopped"
        if args[:2] == ["endpoint", "list"]:
            return json.dumps([{"name": "test-model"}] if active[0] else [])
        raise AssertionError(args)

    def preflight():
        d.rates = RATES

    def smoke(info):
        d.metrics["status"] = "mock_controller_success"

    def cleanup():
        d.metrics["proxy_deleted"] = True

    monkeypatch.setattr(d, "command", command)
    monkeypatch.setattr(d, "preflight", preflight)
    monkeypatch.setattr(d, "smoke", smoke)
    monkeypatch.setattr(d, "cleanup_proxy", cleanup)
    assert d.execute() == (0 if ready else 1)
    assert not active[0] and d.metrics["endpoint_stopped_verified"]
    assert sum(args[:2] == ["endpoint", "create"] for args in calls) == 1
    assert d.metrics["model_calls_attempted"] == 0
    if small:
        assert any(args[:2] == ["endpoint", "logs"] for args in calls)
    assert (run / "finalization.json").exists()
    with pytest.raises(ValueError, match="finalized"):
        module.Diagnostic(run)


def test_unapproved_4b_cannot_contact_modal_or_finalize(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    run = tmp_path / "artifacts/research_runs/unapproved"
    (run / "raw").mkdir(parents=True)
    p = dict(
        run_id=run.name,
        underlying_model="Qwen/Qwen3.5-4B",
        hf_revision="851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
        startup_seconds=480,
        inference_seconds=60,
        shutdown_seconds=60,
        max_calls=1,
        max_total_tokens=8448,
        retries=0,
        approved_max_usd=1.5,
        max_compute_usd_per_second=0.0021,
    )
    (run / "protocol.json").write_text(json.dumps(p))
    d = module.Diagnostic(run)
    monkeypatch.setattr(d, "preflight", lambda: pytest.fail("Unapproved preflight must never run"))
    with pytest.raises(FileNotFoundError):
        d.execute()
    assert not (run / "finalization.json").exists()
    (run / "approval.json").write_text(
        json.dumps(
            dict(approved_by_user=True, run_id=run.name, max_usd=1.5, protocol_sha256="wrong")
        )
    )
    with pytest.raises(ValueError, match="exact protocol"):
        d.execute()
