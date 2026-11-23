import json

import pytest

from afterclick.research.finance import Supervisor


def ledger(tmp_path):
    p = tmp_path / "ledger.json"
    p.write_text(
        json.dumps(
            dict(
                active=None,
                runs=[],
                baseline_metered_usd=2,
                baseline_credit_usd=28,
                account_metered_highwater_usd=2,
                account_additional_highwater_usd=0,
                allowance_usd=20,
            )
        )
    )
    return p


def bill(value=2):
    return dict(metered_cost=str(value), billed_cost="0")


def test_ledger_rejects_concurrent_paid_runs_and_protects_reserve(tmp_path):
    p = ledger(tmp_path)
    with Supervisor(p) as s:
        with pytest.raises(ValueError, match="lock"):
            with Supervisor(p):
                pass
        with pytest.raises(ValueError, match="headroom"):
            s.reserve("large", "p1c", 3, bill(), 3)
        s.reserve("one", "p1c", 0.9, bill(), 3)
        s.data["active"]["metered_before_usd"] = 2
        s.save()
    with pytest.raises(ValueError, match="Unreconciled"):
        with Supervisor(p):
            pass


def test_account_lag_cannot_restore_spending_and_failed_cleanup_retains_cap(tmp_path):
    p = ledger(tmp_path)
    with Supervisor(p) as s:
        s.reconcile(bill(2.4))
        s.reconcile(bill(2.1))
        assert s.data["account_additional_highwater_usd"] == pytest.approx(0.4)
        s.reserve("one", "p1c", 0.5, bill(2.1), 3)
        s.data["active"]["metered_before_usd"] = 2.1
        s.finish(bill(2.2), 10, 0.00135, idle_verified=False)
        assert s.data["runs"][0]["guard_charge_usd"] == 0.5
        with pytest.raises(ValueError, match="reused"):
            s.reserve("one", "p1c", 0.5, bill(2.2), 3)
