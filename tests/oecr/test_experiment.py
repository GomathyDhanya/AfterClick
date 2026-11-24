import json
import time

import httpx

from afterclick.oecr.experiment import run_experiment
from afterclick.tcope.budget import Factory
from tests.agent.test_native_tools import call, reply


def test_three_world_driver_and_public_model_boundary(tmp_path):
    (tmp_path / "raw").mkdir()
    (tmp_path / "trials.jsonl").touch()
    (tmp_path / "oracle_certificates.jsonl").touch()
    received = []

    def handler(request):
        data = json.loads(request.content)
        received.append(data)
        # No private serialized checkpoint, oracle, or labels supplied to model.
        assert all(
            x not in json.dumps(data)
            for x in ["tc_runtime", "collaborator_done", "certificate", "counterfactual_arm"]
        )
        if len(received) % 2:
            return reply(
                [
                    call("browser_fill", {"target": "Comment", "value": "Normal"}, "draft"),
                    call("browser_click", {"target": "Post"}, "post"),
                ]
            )
        # A second request exercises the history validator and resolved native IDs.
        assert any(
            m.get("role") == "tool" and m.get("tool_call_id") == "post" for m in data["messages"]
        )
        return reply([call("finish_task", {}, "f")])

    p = dict(
        startup_seconds=0,
        cleanup_seconds=1,
        max_usd=0.5,
        arm_call_caps={"corrected": 6},
        max_input_tokens=16384,
        max_output_tokens=512,
        request_timeout_seconds=1,
        max_rate_usd_per_second=0.00135,
        public_task_hashes=[],
        max_calls=6,
        max_total_reserved_tokens=101376,
        per_continuation_calls=2,
        cases=[
            dict(
                id="offline-driver",
                seed=901,
                kind="priority",
                new_value="High",
                instruction="Read the current Priority.",
                arm_order=["fresh", "faithful", "source"],
            )
        ],
    )
    info = dict(
        service_url="https://fixture.modal.direct",
        model_name="AfterClick",
        repo_id="fixture",
        revision="fixture",
    )
    f = Factory(
        tmp_path, p, info, time.monotonic() + 120, 23, transport=httpx.MockTransport(handler)
    )
    try:
        run_experiment("oecr", f, tmp_path, time.monotonic() + 120)
    finally:
        f.close()
    trials = [json.loads(s) for s in (tmp_path / "trials.jsonl").read_text().splitlines()]
    assert len(received) == 6
    assert [t["causal_valid"] for t in trials] == [False, True, True]
    assert all(t["report"]["model_calls"] == 2 for t in trials)

    assert all(t["report"]["comment_bodies"] == ["Normal"] for t in trials)


def test_pending_native_result_restores_exact_ids_and_rejects_duplicate(tmp_path):
    import copy

    import pytest

    from afterclick.oecr.experiment import conversation
    from research_ops.scripts.p1_existing import smoke_input
    from tests.tcope.test_execution import make

    a = make(tmp_path, lambda r: reply([call("browser_read", {}, "read-pending")]))
    bdir = tmp_path / "clone"
    bdir.mkdir()
    b = make(bdir, lambda r: reply([call("finish_task", {}, "finish-after-result")]))
    try:
        data = smoke_input()
        a.decide(**data)
        cp = conversation(a)
        b.messages = copy.deepcopy(cp["messages"])
        b.pending_ids = set(cp["pending_ids"])
        b.seen_ids = set(cp["seen_ids"])
        assert conversation(b) == cp
        b.tool_result("read-pending", status="completed", **data)
        with pytest.raises(ValueError, match="Unknown/already resolved"):
            b.tool_result("read-pending", status="completed", **data)
        assert b.decide(**data)[0]["id"] == "finish-after-result"
    finally:
        a.close()
        b.close()
