import copy
import json
import time

import httpx
import pytest
from playwright.sync_api import sync_playwright

from afterclick.agent.modal_policy import InferenceError, Limits
from afterclick.extensions.native_tools import parse_call
from afterclick.tcope.budget import Factory
from afterclick.tcope.driver import run_task
from afterclick.tcope.policy import ExecutionConfig, ExecutionPolicy, public_effect
from afterclick.tcope.provenance import provenance
from afterclick.tcope.tasks import competence_suite
from research_ops.scripts.p1_existing import smoke_input
from tests.agent.test_native_tools import call, reply


def make(tmp_path, handler, model="Qwen/Qwen3.5-4B"):
    return ExecutionPolicy(
        ExecutionConfig(
            endpoint_url="https://fixture.modal.direct",
            endpoint_name="AfterClick",
            underlying_model=model,
            model_revision="fixture",
            max_input_tokens=16384,
            max_output_tokens=512,
            timeout_seconds=1,
        ),
        Limits(max_calls=10, max_total_tokens=168960, max_wall_seconds=120),
        journal=tmp_path / "calls.jsonl",
        transport=httpx.MockTransport(handler),
    )


def test_public_draft_semantics_no_oracle_and_dynamic_identity(tmp_path):
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        return reply(
            [call("browser_fill", {"target": "Comment", "value": "a local draft"}, "draft")]
        )

    p = make(tmp_path, handler, model="Qwen/Qwen3.5-9B")
    public = smoke_input()
    before = copy.deepcopy(public["observation"])
    after = copy.deepcopy(before)
    after["inputs"]["Comment"] = "a local draft"
    calls = p.decide(**public)
    effect = public_effect(parse_call(calls[0]), before, after, "completed")
    assert effect["effect"] == "comment_draft_updated_not_submitted"
    assert effect["committed_indicator_scope"] == "autosaved_task_fields_only"
    p.tool_result("draft", status="completed", effect=effect, **public)
    identity = provenance(p, "draft")
    assert identity["model"].endswith("9B") and "4b" not in identity["actor"]
    assert identity["parent_request_id"] == p.records[-1]["request_id"]
    assert sent[0]["tool_choice"] == "auto" and "response_format" not in sent[0]
    assert "NEVER posts" in sent[0]["tools"][0]["function"]["description"]
    result = json.loads(p.messages[-1]["content"])
    assert result["semantics"]["effect"] == "comment_draft_updated_not_submitted"
    p.close()


def test_private_input_and_tool_feedback_rejected(tmp_path):
    p = make(tmp_path, lambda request: pytest.fail("must not send hidden input"))
    public = smoke_input()
    public["task"]["oracle"] = True
    with pytest.raises(InferenceError):
        p.decide(**public)
    public = smoke_input()
    public["observation"]["future_schedule"] = 42
    with pytest.raises(InferenceError, match="invalid_public"):
        p.decide(**public)
    p.pending_ids = {"x"}
    with pytest.raises(ValueError, match="Nonpublic"):
        p.tool_result("x", status="completed", effect={"oracle": True}, **smoke_input())
    assert p.usage_summary()["calls"] == 0
    p.close()


@pytest.mark.browser
def test_post_commits_and_native_checkpoint_continues_with_correct_ids(tmp_path):
    spec = competence_suite()[2]
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
        [call("browser_click", {"target": "Mark reviewed"}, "review")],
        [call("finish_task", {}, "finish")],
    ]
    p = make(tmp_path / "parent", lambda request: reply(batches.pop(0)))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        parent = run_task(browser, spec, p, tmp_path / "parent-world", float("inf"))
        assert parent["valid"], parent.get("error") or parent.get("oracle_error")
        assert parent["oracle"]["safe_task_success"]
        assert parent["oracle"]["receipt_count"] == 1
        assert parent["steps"][1]["semantics"]["effect"] == "comment_draft_updated_not_submitted"
        assert parent["steps"][2]["semantics"]["effect"] == "comment_posted_visible"
        cp = json.loads((tmp_path / "parent-world/checkpoint-03.json").read_text())
        sent = []
        for name, intervention in [
            ("noop", {"kind": "noop"}),
            ("original", {"kind": "execute"}),
            ("suppressed", {"kind": "suppress"}),
            (
                "substitute",
                {
                    "kind": "substitute",
                    "action": {"kind": "read", "target": "Description", "value": ""},
                },
            ),
            ("delayed", {"kind": "execute", "delay_ms": 20}),
        ]:
            branch_batches = (
                [[call("browser_click", {"target": "Mark reviewed"}, name + "-review")]]
                if name in {"suppressed", "substitute"}
                else []
            ) + [[call("finish_task", {}, name + "-finish")]]

            def handler(request):
                sent.append(json.loads(request.content))
                return reply(branch_batches.pop(0))

            b = make(tmp_path / name, handler)
            branch = run_task(
                browser,
                spec,
                b,
                tmp_path / ("world-" + name),
                float("inf"),
                checkpoint=cp,
                intervention=intervention,
            )
            assert branch["valid"], (name, branch.get("error"), branch.get("oracle_error"))
            assert branch["reconstruction"]["valid"]
            assert branch["oracle"]["safe_task_success"]
            assert branch["model_calls"] >= 1
            assert not branch["live_continuation"]  # Mock never called genuine live.
            first = next(
                m
                for m in sent[-branch["model_calls"]]["messages"]
                if m["role"] == "tool" and m["tool_call_id"] == "review"
            )
            if name in {"suppressed", "substitute"}:
                assert json.loads(first["content"])["status"] in {"blocked", "deferred", "verified"}
            b.close()
        browser.close()
    p.close()


def test_finish_claim_is_not_hidden_task_verification(tmp_path):
    p = make(tmp_path, lambda request: reply([call("finish_task", {}, "finish")]))
    public = smoke_input()
    calls = p.decide(**public)
    effect = public_effect(
        parse_call(calls[0]), public["observation"], public["observation"], "completed"
    )
    assert effect["effect"] == "agent_completion_claim_recorded"
    p.tool_result("finish", status="completed", effect=effect, **public)
    with pytest.raises(ValueError):
        p.tool_result("finish", status="completed", **public)
    p.close()


def test_global_budget_spans_arms_and_unknown_requests(tmp_path):
    (tmp_path / "raw").mkdir()
    protocol = dict(
        arm_call_caps={"legacy": 1, "corrected": 1},
        max_input_tokens=16384,
        max_output_tokens=512,
        request_timeout_seconds=1,
        max_usd=0.9,
        max_rate_usd_per_second=0.00135,
        startup_seconds=225,
        cleanup_seconds=45,
        public_task_hashes=[],
        max_calls=2,
        max_total_reserved_tokens=33792,
    )
    info = dict(
        service_url="https://fixture.modal.direct",
        model_name="AfterClick",
        repo_id="Qwen/Qwen3.5-4B",
        revision="fixture",
    )
    factory = Factory(
        tmp_path,
        protocol,
        info,
        time.monotonic() + 100,
        27,
        transport=httpx.MockTransport(lambda request: reply([call("finish_task", {}, "f")])),
    )
    for arm in ["legacy", "corrected"]:
        p = factory.make(arm)
        p.decide(**smoke_input())
    assert factory.usage()["calls"] == 2
    with pytest.raises(InferenceError, match="global_call_budget"):
        factory.admit()
    factory.close()
