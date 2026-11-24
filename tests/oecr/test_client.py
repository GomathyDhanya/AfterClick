import copy
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from afterclick import domain
from afterclick.agent.modal_policy import atomic_json
from afterclick.oecr.client import attach, capture, certify, validate
from afterclick.tcope.workload_specs import workload_suite
from afterclick.tcope.workloads import WorkloadWorld

BASE = Path(os.environ.get("OECR_EVIDENCE_DIR", "/tmp/afterclick-oecr-tests"))
BASE.mkdir(parents=True, exist_ok=True)


@pytest.mark.parametrize(
    "condition",
    [
        "fresh",
        "stale_collaborator",
        "pending_autosave",
        "delayed_sse",
        "delayed_ack",
        "corrupt_checkpoint",
        "pending_native_result",
        "hidden_external_receipt",
    ],
)
def test_client_reconstruction(condition):
    spec = workload_suite()[0 if condition == "hidden_external_receipt" else 6]
    source = WorkloadWorld(spec)
    source.initialize()
    # Explicit controlled-clock cut: no background core ticker during capture.
    source.frozen_initial = source.snapshot()
    clone = None
    conversation = {
        "messages": [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "pending-1",
                        "type": "function",
                        "function": {
                            "name": "browser_read",
                            "arguments": '{"target":"Description"}',
                        },
                    }
                ],
            }
        ],
        "pending_ids": ["pending-1"],
        "seen_ids": ["pending-1"],
        "history": [],
    }
    rows = {}
    try:
        with sync_playwright() as pw, source.serve() as origin:
            browser = pw.chromium.launch()
            page = browser.new_page()
            g = attach(page, origin, source)
            page.evaluate("window.oecr.pause()")
            source.browser_pause(page)
            if condition in ["stale_collaborator", "delayed_sse"]:
                source.step(250)
                if condition == "delayed_sse":
                    domain.advance(source.db, 2000)
                    page.wait_for_function("window.oecr.queue().length>0")
            if condition == "hidden_external_receipt":
                source.step(20000)
            if condition == "pending_autosave":
                page.get_by_label("Description", exact=True).fill("Pending local edit")
            if condition == "delayed_ack":
                # Real request intercepted before transport; capture must reject outstanding write.
                pending = []
                page.route(
                    "**/api/tasks/TASK-42",
                    lambda route: (
                        pending.append(route)
                        if route.request.method == "PATCH"
                        else route.fallback()
                    ),
                )
                page.get_by_label("Description", exact=True).fill("Unacknowledged edit")
                page.wait_for_timeout(750)
                assert pending
                with pytest.raises(Exception, match="OECR_UNSUPPORTED_INFLIGHT"):
                    capture(source, g, conversation)
                # Let the same write resolve, then explicitly take a NEW cut.
                pending[0].continue_()
                expect(page.get_by_role("status")).to_have_text("✓ Committed")
                page.wait_for_function("!window.oecr.inflight()")
                rows = {
                    "original_cut_supported": False,
                    "rejected": True,
                    "consistent_cut_alternative": True,
                    "reason": "new cut after transport resolution",
                    "model_calls": 0,
                }
            env = capture(source, g, conversation)
            cp = validate(env)
            atomic_json(BASE / (condition + "-checkpoint.json"), env)
            if condition == "corrupt_checkpoint":
                damaged = copy.deepcopy(env)
                damaged["payload"]["client"]["draft"]["priority"] = "Critical"
                with pytest.raises(ValueError, match="INTEGRITY"):
                    validate(damaged)
                rows = {
                    "supported": False,
                    "rejected": True,
                    "reason": "tampered snapshot",
                    "model_calls": 0,
                }
                atomic_json(BASE / (condition + ".json"), rows)
                browser.close()
                return
            clone = WorkloadWorld(spec)
            clone.initialize(cp)
            with clone.serve() as other:
                q = browser.new_page()
                cg = attach(q, other, clone, cp)
                cert = certify(clone, cg, cp, conversation)
                rows = {**rows, "supported": True, "certificate": cert, "model_calls": 0}
                atomic_json(BASE / (condition + ".json"), rows)
                assert cert["valid"], cert
                # Fresh browser comparator shares the backend but not saved React state.
                baseline = browser.new_page()
                bg = attach(baseline, other, clone)
                baseline.evaluate("window.oecr.pause()")
                clone.browser_pause(baseline)
                from afterclick.agent.browser_observation import observe

                rows["fresh_browser_observation_equal"] = observe(bg) == cp["observation"]
                baseline.close()
                if condition == "pending_native_result":
                    bad = copy.deepcopy(conversation)
                    bad["pending_ids"] = []
                    assert not certify(clone, cg, cp, bad)["valid"]
                if condition in ["stale_collaborator", "delayed_sse"]:
                    assert q.get_by_label("Priority", exact=True).input_value() == "Normal"
                    assert cp["world"]["tasks"][0]["priority"] == "High"
                    if condition == "stale_collaborator":
                        q.evaluate("window.oecr.refresh()")
                    else:
                        q.evaluate("window.oecr.resume()")
                    expect(q.get_by_label("Priority", exact=True)).to_have_value("High")
                    rows["subsequent_update_preserved"] = True
                if condition == "pending_autosave":
                    q.evaluate("window.oecr.resume()")
                    expect(q.get_by_role("status")).to_have_text("✓ Committed")
                    assert clone.snapshot()["tasks"][0]["description"] == "Pending local edit"
                    assert len(clone.snapshot()["operations"]) == 1
                    page.evaluate("window.oecr.resume()")
                    expect(page.get_by_role("status")).to_have_text("✓ Committed")
                    assert (
                        source.snapshot()["tasks"][0]["description"]
                        == clone.snapshot()["tasks"][0]["description"]
                    )
                    assert len(source.snapshot()["operations"]) == 1
                    rows["single_autosave_committed"] = True
                    rows["source_clone_continuation_agrees"] = True
                if condition == "hidden_external_receipt":
                    assert len(clone.snapshot()["tc_receipts"]) == 1
                    assert cp["browser_payload"]["public_state"]["observed_receipts"] == 0
                    rows["historical_receipt_preserved_while_unobserved"] = True
                atomic_json(BASE / (condition + ".json"), rows)
                q.close()
            browser.close()
    finally:
        if clone:
            clone.db.drop_experiment()
        source.db.drop_experiment()


def test_equal_dom_does_not_preserve_autosave_semantics():
    """Falsification: visible draft alone omits the executable dirty-field buffer."""
    spec = workload_suite()[6]
    source = WorkloadWorld(spec)
    source.initialize()
    source.frozen_initial = source.snapshot()
    clone = None
    try:
        with sync_playwright() as pw, source.serve() as origin:
            browser = pw.chromium.launch()
            page = browser.new_page()
            g = attach(page, origin, source)
            page.get_by_label("Description", exact=True).fill(
                "Visible draft is not a committed write"
            )
            cp = validate(capture(source, g, {}))
            partial = copy.deepcopy(cp)
            partial["client"]["dirty"] = {}
            clone = WorkloadWorld(spec)
            clone.initialize(cp)
            with clone.serve() as other:
                q = browser.new_page()
                cg = attach(q, other, clone, partial)
                cert = certify(clone, cg, cp, {})
                assert cert["checks"]["observation_equal"]
                assert not cert["checks"]["client_equal"]
                q.evaluate("window.oecr.resume()")
                q.wait_for_timeout(900)
                assert (
                    clone.snapshot()["tasks"][0]["description"]
                    != "Visible draft is not a committed write"
                )
                atomic_json(
                    BASE / "dom-only-ablation.json",
                    dict(
                        certificate=cert,
                        initial_dom_equal=True,
                        autosave_semantics_lost=True,
                        model_calls=0,
                    ),
                )
                q.close()
            browser.close()
    finally:
        if clone:
            clone.db.drop_experiment()
        source.db.drop_experiment()
