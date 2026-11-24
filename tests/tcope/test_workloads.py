import copy
from dataclasses import replace

import pytest
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import text

from afterclick.agent.browser_observation import observe
from afterclick.agent.gateway import Action
from afterclick.tcope.gateway import ServiceGateway
from afterclick.tcope.workload_oracle import evaluate_workload
from afterclick.tcope.workload_specs import workload_suite
from afterclick.tcope.workloads import WorkloadWorld


def setup(index, **schedule):
    spec = workload_suite()[index]
    spec = replace(spec, schedule={**spec.schedule, **schedule})
    world = WorkloadWorld(spec)
    world.initialize()
    return spec, world


def test_notice_cancellation_and_historical_receipt(tmp_path):
    spec, w = setup(0, deadline_ms=50, ack_lag_ms=2000)
    try:
        with w.serve():
            w.action("Cancel notice", "control", "scripted-test", "unused")
            w.step(100)
            assert not w.snapshot()["tc_receipts"]
        assert w.public()["cancellation"] == "requested"
    finally:
        w.db.drop_experiment()
    spec, w = setup(0, deadline_ms=50, ack_lag_ms=2000)
    try:
        with w.serve():
            w.step(100)
            before = w.snapshot()
            assert len(before["tc_receipts"]) == 1
            assert w.public()["observed_receipts"] == 0  # Receipt != observation arrival.
            w.action("Cancel notice", "control", "scripted-test", "unused")
            assert len(w.snapshot()["tc_receipts"]) == 1
            with pytest.raises(Exception):
                with w.db.transaction() as c:
                    c.execute(text("DELETE FROM tc_receipts"))
        corrupt = copy.deepcopy(before)
        corrupt["tc_events"] = []
        assert not evaluate_workload(spec, before, corrupt, "scripted-test", set(), [])[
            "receiver_consistent"
        ]
    finally:
        w.db.drop_experiment()


def test_permission_frontier_precedes_read_even_after_revocation():
    spec, w = setup(2, deadline_ms=50, read_ms=100)
    try:
        with w.serve():
            w.step(60)
            assert not w.snapshot()["tc_receipts"]
            w.action("Revoke access", "control", "scripted-test", "revoke")
            w.step(110)
            assert len(w.snapshot()["tc_receipts"]) == 1
            assert w.public()["permission"] == "revoked"
    finally:
        w.db.drop_experiment()
    spec, w = setup(2, deadline_ms=50, read_ms=100)
    try:
        with w.serve():
            w.action("Revoke access", "control", "scripted-test", "revoke")
            w.step(60)
            w.action("Verify access", "control", "scripted-test", "verify")
            w.action("Grant access", "control", "scripted-test", "grant")
            w.step(110)
            assert not w.snapshot()["tc_receipts"]
            assert w.public()["request_resolved"] and w.public()["permission"] == "granted"
    finally:
        w.db.drop_experiment()


def test_resource_observer_idempotence_and_stale_verification():
    spec, w = setup(5, action_delay_ms=20, missing_ack=True)
    try:
        with w.serve():
            w.action("Authorize resource", "a1", "scripted-test", "reserve")
            w.action("Verify resource", "a2", "scripted-test", "verify-before")
            w.action("Capture resource", "a3", "scripted-test", "capture-one")
            w.step(30)
            assert len(w.snapshot()["tc_receipts"]) == 1
            assert w.public()["observed_receipts"] == 0  # A past check is not future knowledge.
            assert w.snapshot()["tc_accounts"][0]["units"] == 2
            w.action("Verify resource", "a4", "scripted-test", "verify-after")
            assert w.public()["observed_receipts"] == 1
            w.action("Retry resource", "a5", "scripted-test", "ignored")
            w.step(60)
            assert len(w.snapshot()["tc_receipts"]) == 1
            assert w.snapshot()["tc_accounts"][0]["units"] == 2
            w.action("Capture resource", "a6", "scripted-test", "different-intent")
            w.step(90)
            assert len(w.snapshot()["tc_receipts"]) == 2
            assert w.snapshot()["tc_accounts"][0]["units"] == 1
    finally:
        w.db.drop_experiment()


def test_public_allowlist_excludes_hidden_schedule_and_outcome():
    spec, w = setup(0)
    try:
        p = w.public()
        assert not set(p) & {
            "deadline",
            "read_due",
            "ticket",
            "done",
            "pending",
            "nonce",
            "oracle",
            "source_group",
        }
        assert set(spec.public()) == {"instruction", "goals"} and spec.public()["goals"] == []
        assert all(t.partition == "confirmation" for t in workload_suite("confirmation"))
        assert not {t.source_group for t in workload_suite()} & {
            t.source_group for t in workload_suite("confirmation")
        }
    finally:
        w.db.drop_experiment()


@pytest.mark.browser
def test_flowboard_extension_uses_real_gateway_and_public_commit_audit(tmp_path):
    spec, w = setup(1)
    context = None
    try:
        with w.serve() as origin, sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            gateway = ServiceGateway(page, origin)
            gateway.act(Action("navigate", "/"))
            expect(page.get_by_role("button", name="Send notice", exact=True)).to_be_visible()
            gateway.source = dict(
                kind="scripted-test",
                actor="scripted-test",
                model=None,
                revision=None,
                tool_call_id=None,
            )
            gateway.act(Action("fill", "Comment", spec.comment))
            page.wait_for_timeout(650)
            gateway.act(Action("click", "Post"))
            page.wait_for_timeout(700)
            state = w.snapshot()
            assert state["task_comments"][0]["body"] == spec.comment
            acks = [e for e in state["tc_events"] if e["kind"] == "core.commit_ack"]
            assert acks and acks[-1]["payload"]["operation_id"] == state["task_comments"][0]["id"]
            assert not gateway.pending
            payload = w.browser_checkpoint(page, observe(gateway))
            assert payload["public_state"]["service"] == "publication"
            browser.close()
            context = None
    finally:
        # Playwright context manager closes all browser contexts on errors too.
        w.db.drop_experiment()


@pytest.mark.browser
def test_actual_ui_checkpoint_restores_service_cache_and_mock_continuation(tmp_path):
    import json

    from afterclick.tcope.driver import run_task
    from tests.agent.test_native_tools import call, reply
    from tests.tcope.test_execution import make

    spec = workload_suite()[1]
    batches = [
        [
            call(
                "browser_fill",
                {"target": "Description", "value": spec.expected["description"]},
                "desc",
            ),
            call("browser_fill", {"target": "Comment", "value": spec.comment}, "draft"),
        ],
        [call("browser_click", {"target": "Post"}, "post")],
        [call("browser_click", {"target": "Send notice"}, "send")],
        [call("finish_task", {}, "done")],
    ]
    policy = make(tmp_path / "parent", lambda request: reply(batches.pop(0)))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        parent = run_task(
            browser,
            spec,
            policy,
            tmp_path / "parent-world",
            float("inf"),
            world=WorkloadWorld(spec),
        )
        assert parent["valid"], parent.get("error") or parent.get("oracle_error")
        assert parent["oracle"]["safe_task_success"], parent["oracle"]
        cp = json.loads((tmp_path / "parent-world/checkpoint-03.json").read_text())
        branch_policy = make(
            tmp_path / "branch", lambda request: reply([call("finish_task", {}, "branch-done")])
        )
        branch = run_task(
            browser,
            spec,
            branch_policy,
            tmp_path / "branch-world",
            float("inf"),
            world=WorkloadWorld(spec),
            checkpoint=cp,
            intervention={"kind": "execute"},
        )
        assert branch["valid"], branch.get("error") or branch.get("oracle_error")
        assert branch["reconstruction"]["full_public_observation_equal"]
        assert branch["oracle"]["safe_task_success"], branch["oracle"]
        assert branch["model_calls"] == 1 and not branch["live_continuation"]
        browser.close()
    policy.close()
    branch_policy.close()


def test_identical_public_observations_do_not_reveal_hidden_effect_time():
    cases = []
    try:
        for frontier in [50, 100]:
            spec, w = setup(0, deadline_ms=frontier, ack_lag_ms=2000)
            cases.append(w)
            with w.serve():
                w.step(60)
        assert cases[0].public() == cases[1].public()
        assert len(cases[0].snapshot()["tc_receipts"]) == 1
        assert not cases[1].snapshot()["tc_receipts"]
    finally:
        for w in cases:
            w.db.drop_experiment()
