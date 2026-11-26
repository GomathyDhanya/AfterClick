import json
import time
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from afterclick.review.budgeted_transport import BudgetedToolTransport, SharedFactory
from afterclick.review.finance import ReviewSupervisor


def test_historical_or_proposed_approval_cannot_open_paid_path(tmp_path):
    p = tmp_path / "approval.json"
    p.write_text(json.dumps(dict(status="PROPOSED_NOT_AUTHORIZED_NOT_QUEUED")))
    with pytest.raises(ValueError, match="not been explicitly approved"):
        ReviewSupervisor(tmp_path / "ledger.json", p)
    with pytest.raises(ValueError, match="Explicit approved shared reservation"):
        BudgetedToolTransport(None)


def test_mock_shared_native_calls_are_capped_and_journaled(tmp_path):
    f = SharedFactory.__new__(SharedFactory)
    f.run = tmp_path
    f.settings = {}
    f.instances = []
    f.deadline = time.monotonic() + 60
    f.trial_call_start = None
    f.trial_call_cap = None
    f.protocol = dict(
        max_calls=1,
        max_total_reserved_tokens=16896,
        max_input_tokens=16384,
        max_output_tokens=512,
        request_timeout_seconds=1,
    )
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            json=dict(
                choices=[dict(message=dict(role="assistant", content="done"))],
                usage=dict(prompt_tokens=10, completion_tokens=1, total_tokens=11),
            ),
        )

    t = BudgetedToolTransport(f, transport=httpx.MockTransport(handler))
    request = dict(
        model="AfterClick",
        messages=[dict(role="user", content="Read synthetic fixture")],
        tools=[],
        tool_choice="auto",
        max_tokens=512,
    )
    try:
        t(request)
        assert f.usage()["calls"] == 1 and f.usage()["known_total_tokens"] == 11
        with pytest.raises(Exception, match="global_call_budget"):
            t(request)
    finally:
        t.close()
    f.close()
    assert len(seen) == 1


def test_explicit_transfer_preserves_old_charges_and_finish_contract(tmp_path):
    ledger = tmp_path / "ledger.json"
    approval = tmp_path / "approval.json"
    old = dict(run_id="old", category="trajectories", guard_charge_usd=3.44)
    ledger.write_text(
        json.dumps(
            dict(
                allowance_usd=20,
                baseline_credit_usd=28.11,
                baseline_metered_usd=2,
                account_metered_highwater_usd=8.4,
                account_additional_highwater_usd=6.4,
                active=None,
                runs=[old],
                unresolved_request=False,
            )
        )
    )
    approval.write_text(
        json.dumps(
            dict(
                status="explicitly_approved_by_user",
                user_message_sha256="MOCK_ONLY",
                experiment_id="w4-review-live-development-v1",
                transfer_from="contingency",
                max_usd=1.25,
                expires_utc=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
            )
        )
    )
    bill = dict(metered_cost="8.4", billed_cost="0")
    with ReviewSupervisor(ledger, approval) as s:
        reservation = s.reserve_review(bill, 14)
        assert reservation["reserved_usd"] == 1.25
        s.finish(bill, 10, 0.00135, idle_verified=True)
        assert s.data["runs"][0] == old
        assert s.data["allowance_usd"] == 20 and s.data["active"] is None
        assert s.data["runs"][-1]["category"] == "contingency"
