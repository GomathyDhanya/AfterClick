import pytest

from research_ops.scripts.reproduce_research import plan


def test_reproduction_plan_is_local_only_and_cannot_enable_paid_work(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    _, commands = plan("check")
    assert len(commands) == 6
    assert all("modal" not in " ".join(c["argv"]).lower() for c in commands)
    with pytest.raises(ValueError, match="paid"):
        plan("check", "enabled")
    with pytest.raises(ValueError, match="identifier"):
        plan("../escape")


def test_reproduction_refuses_nonlocal_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://prod.example.invalid/main")
    with pytest.raises(ValueError, match="Local"):
        plan("check")
