"""Unknown content must survive any local fixed-GPU accounting reconciliation."""

import json
import pytest
from research_ops.scripts import reconcile_afterclick_v12_finance as closure


def save(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v))


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(closure, "ROOT", tmp_path)
    state = tmp_path / "research_ops/completion_v12/FINANCE_STATE.json"
    monkeypatch.setattr(closure, "STATE", state)
    state.parent.mkdir(parents=True)
    run = tmp_path / "trial"
    raw = run / "raw"
    raw.mkdir(parents=True)
    (tmp_path / "research_ops/SPEND_STATE.lock").touch()
    last = dict(
        run_id="trial",
        usage=dict(calls=8, tokens=100, uncertain=2),
        guard_charge_usd=1.0,
        elapsed_seconds=100,
        rate_usd_per_second=0.005,
        metered_before_usd=15,
        idle_verified=True,
    )
    initial = dict(
        active=None, unresolved_request=True, account_metered_highwater_usd=15.5, runs=[last]
    )
    save(state, initial)
    save(run / "lifecycle.json", dict(usage=last["usage"], idle_verified=True, min0_restored=True))
    save(
        raw / "settings-final-min0.json",
        dict(
            current_settings=dict(
                min_containers=0, buffer_containers=0, max_containers=1, scaledown_window=2
            )
        ),
    )
    save(raw / "containers-after-0.json", [])
    save(raw / "cpu-app-info.json", dict(app_id="ap-fixture"))
    save(raw / "endpoint.json", dict(app_id="ap-endpoint"))

    def cli(args, path):
        value = (
            dict(lifecycle=dict(state="stopped", stopped_at="observed"))
            if args[0] == "app"
            else []
            if args[0] == "container"
            else dict(
                billed_cost="0", metered_cost="15.5", metered_cost_breakdown=dict(llm_tokens="0")
            )
        )
        save(path, value)
        return value

    monkeypatch.setattr(closure, "cli", cli)
    return run, state, initial


def test_gpu_closure_keeps_unknown_responses_and_original_reservation(tmp_path, monkeypatch):
    run, state, initial = fixture(tmp_path, monkeypatch)
    closure.main(run)
    result = json.loads(state.read_text())
    assert result["runs"][0] == initial["runs"][0]
    assert result["runs"][0]["usage"]["uncertain"] == 2
    assert result["unresolved_request"] is False
    assert sum(r["guard_charge_usd"] for r in result["runs"]) == 0.625
    assert (
        json.loads((run / "raw/financial-closure-reconciliation/ledger-before.json").read_text())
        == initial
    )


def test_nonzero_minimum_blocks_reconciliation_without_ledger_mutation(tmp_path, monkeypatch):
    run, state, initial = fixture(tmp_path, monkeypatch)
    save(
        run / "raw/settings-final-min0.json",
        dict(
            current_settings=dict(
                min_containers=1, buffer_containers=0, max_containers=1, scaledown_window=2
            )
        ),
    )
    with pytest.raises(AssertionError):
        closure.main(run)
    assert json.loads(state.read_text()) == initial
