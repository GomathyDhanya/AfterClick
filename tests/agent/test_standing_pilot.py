from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from afterclick.agent.action_parser import Decision
from research_ops.scripts import p1_standing


def test_guarded_keeps_single_budget_journal_and_blocks_uncertain_requests():
    policy = SimpleNamespace(journal="global", usage_summary=lambda: {"uncertain": True})
    guarded = p1_standing.Guarded(policy, float("inf"))
    guarded.journal = "branch-local"
    assert policy.journal == "global"
    with pytest.raises(TimeoutError):
        guarded.before_branch()


def test_visible_retry_guard_uses_no_model_or_hidden_information(tmp_path):
    payload = p1_standing.smoke_input()
    payload["observation"]["save_status"] = "Failed"
    payload["observation"]["controls"].append(
        {"role": "button", "name": "Retry save", "enabled": True}
    )
    policy = SimpleNamespace(
        usage_summary=lambda: {"uncertain": False},
        decide=lambda **kwargs: pytest.fail("Guard must resolve UI state before model mutation"),
    )
    journal = tmp_path / "guard.jsonl"
    guarded = p1_standing.Guarded(policy, float("inf"), journal)
    assert guarded.decide(**payload).target == "Retry save"
    assert '"model_call": false' in journal.read_text()
    payload["observation"]["oracle"] = "forbidden"
    with pytest.raises(ValueError):
        guarded.decide(**payload)


def test_revised_scope_preserves_failed_multiaction_and_requires_replay(tmp_path, monkeypatch):
    policy = SimpleNamespace(
        decide=lambda **kwargs: Decision(kind="read", target="Description", value=""),
        usage_summary=lambda: {"uncertain": False},
    )
    monkeypatch.setattr(p1_standing, "sync_playwright", MagicMock())
    monkeypatch.setattr(
        p1_standing,
        "browser_task",
        lambda browser, contract, policy, path, steps: {"accepted": path.name == "legitimate_task"},
    )
    monkeypatch.setattr(
        p1_standing,
        "run_case",
        lambda *args, **kwargs: {
            "certificate": {"valid": True},
            "branches": {"execute": {"task": {"success": True}}},
        },
    )
    report = p1_standing.validate(policy, tmp_path, float("inf"))
    assert not report["stages"][2]["accepted"]
    assert report["stages"][3]["accepted"]
    assert not report["multi_action_gates_replay"]


def test_no_network_without_frozen_protocol_and_standing_authorization(tmp_path):
    with pytest.raises(FileNotFoundError):
        p1_standing.execute(tmp_path)
