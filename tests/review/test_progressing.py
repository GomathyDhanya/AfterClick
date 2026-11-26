import copy
import os
import time
from dataclasses import replace
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from afterclick import domain
from afterclick.agent.modal_policy import atomic_json
from afterclick.oecr.client import attach, validate
from afterclick.review.progressing import ProgressingWorld, admit, checkpoint, resume
from afterclick.tcope.workload_specs import workload_suite

BASE = Path(os.environ.get("REVIEW_EVIDENCE_DIR", "/tmp/afterclick-review-progressing"))
BASE.mkdir(parents=True, exist_ok=True)


@pytest.mark.parametrize(
    "condition",
    [
        "cancel_before",
        "cancel_after",
        "effect_during_inference",
        "missing_ack",
        "pending_autosave",
        "concurrent_edit",
        "receipt_survives_rollback",
        "inconsistent",
    ],
)
def test_progressing_cut(condition):
    early = condition in {"cancel_before", "pending_autosave", "concurrent_edit", "inconsistent"}
    spec = replace(
        workload_suite()[0],
        schedule=dict(
            pending=True,
            deadline_ms=800 if condition == "cancel_before" else 4000 if early else 250,
            ack_lag_ms=2000,
            missing_ack=condition == "missing_ack",
        ),
    )
    source = ProgressingWorld(spec)
    source.initialize()
    source.frozen_initial = source.snapshot()
    clone = None
    conversation = {
        "messages": [{"role": "user", "content": "Controlled synthetic qualification"}],
        "pending_ids": [],
        "seen_ids": [],
    }
    results = []
    try:
        with sync_playwright() as pw, source.serve() as origin:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.set_default_timeout(5000)
            g = attach(page, origin, source)
            if condition == "pending_autosave":
                page.get_by_label("Description", exact=True).fill("Pending edit must survive")
            env = checkpoint(source, g, conversation)
            cp = validate(env)
            atomic_json(BASE / f"{condition}-checkpoint.json", env)
            assert admit(source, g, env, conversation)["valid"]
            clone = ProgressingWorld(spec)
            clone.initialize(cp)
            with clone.serve() as other:
                q = browser.new_page()
                q.set_default_timeout(5000)
                cg = attach(q, other, clone, cp)
                cert = admit(clone, cg, env, conversation)
                if condition == "inconsistent":
                    altered = copy.deepcopy(conversation)
                    altered["pending_ids"] = ["wrong"]
                    with pytest.raises(ValueError, match="ADMISSION_REJECTED"):
                        admit(clone, cg, env, altered)
                    atomic_json(BASE / f"{condition}.json", dict(certificate=cert, rejected=True))
                    q.close()
                    browser.close()
                    return
                for world, gw in [(source, g), (clone, cg)]:
                    resume(world, gw)
                    start = time.time()
                    if condition == "cancel_before":
                        gw.page.get_by_role("button", name="Cancel notice", exact=True).click()
                        gw.page.wait_for_timeout(1100)
                    else:
                        # Simulated synchronous model work blocks browser event pumping;
                        # independent SQL/HTTP worker must still progress.
                        time.sleep(0.8)
                        if condition == "cancel_after":
                            gw.page.get_by_role("button", name="Cancel notice", exact=True).click()
                        if condition == "pending_autosave":
                            expect(gw.page.get_by_role("status")).to_have_text("✓ Committed")
                            assert (
                                world.snapshot()["tasks"][0]["description"]
                                == "Pending edit must survive"
                            )
                        if condition == "concurrent_edit":
                            with world.db.engine.connect() as c:
                                t = domain.task(c, "TASK-42")
                            domain.patch_task(
                                world.db,
                                "TASK-42",
                                {"priority": "High"},
                                t["version"],
                                "independent-op",
                                "independent-op",
                                "controlled-collaborator",
                            )
                            gw.page.wait_for_timeout(150)
                        if condition == "receipt_survives_rollback":
                            before = world.snapshot()["tc_receipts"]
                            with world.db.engine.connect() as c:
                                t = domain.task(c, "TASK-42")
                            domain.patch_task(
                                world.db,
                                "TASK-42",
                                {"description": "Rollback local text"},
                                t["version"],
                                "local-rollback",
                                "local-rollback",
                                "scripted-treatment",
                            )
                            with world.db.engine.connect() as c:
                                changed = domain.task(c, "TASK-42")
                            domain.patch_task(
                                world.db,
                                "TASK-42",
                                {"description": t["description"]},
                                changed["version"],
                                "actual-local-restore",
                                "actual-local-restore",
                                "scripted-treatment",
                            )
                            assert world.snapshot()["tasks"][0]["description"] == t["description"]
                            assert world.snapshot()["tc_receipts"] == before
                    final = world.snapshot()
                    world.finish()
                    dispatch = {
                        e["payload"]["id"]
                        for e in final["tc_events"]
                        if e["kind"] == "dispatch.issued"
                    }
                    receipts = {e["id"] for e in final["tc_receipts"]}
                    assert dispatch == receipts
                    assert not world.worker_errors
                    assert bool(receipts) == (not early)
                    if condition in {"missing_ack", "effect_during_inference"}:
                        assert world.public()["observed_receipts"] == 0
                    if condition == "concurrent_edit":
                        assert final["tasks"][0]["priority"] == "High"
                    results.append(
                        dict(
                            initial_certificate=cert,
                            final=final,
                            worker_intervals=world.worker_intervals,
                            started_wall=start,
                            finished_wall=time.time(),
                            receiver_consistent=True,
                            receipt_count=len(receipts),
                        )
                    )
                assert results[0]["receipt_count"] == results[1]["receipt_count"]
                atomic_json(
                    BASE / f"{condition}.json",
                    dict(
                        results=results,
                        model_calls=0,
                        policy="deterministic scripted with simulated .8s inference",
                        scheduler="progressing_v2",
                    ),
                )
                q.close()
            browser.close()
    finally:
        source.finish()
        source.db.drop_experiment()
        if clone:
            clone.finish()
            clone.db.drop_experiment()
