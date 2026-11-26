"""Re-score saved supervision SQL/receipt evidence; never perform inference."""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from afterclick.extensions.native_tools import parse_call
from afterclick.model_sprint.records import sha
from afterclick.oecr.client import validate
from afterclick.review.study_runner import task
from afterclick.review.supervision.policy import PROMPT, ReviewContext
from afterclick.tcope.provenance import provenance
from afterclick.tcope.workload_oracle import evaluate_workload
from research_ops.scripts.analyze_timing_study import read_lines


def verify(run):
    p = json.loads((run / "protocol.json").read_text())
    for name, h in p["source_hashes"].items():
        assert sha(run / "raw/source-archive" / name) == h, name
    rows = read_lines(run / "model_calls.jsonl")
    starts = [r for r in rows if r["event"] == "started"]
    ends = [r for r in rows if r["event"] == "finished"]
    assert len({r["request_id"] for r in starts}) == len(starts)
    assert {r["request_id"] for r in starts} == {r["request_id"] for r in ends}
    native = reviews = genuine = invalid_review = 0
    for r in ends:
        assert not r.get("billing_uncertain")
        cfg = r["config"]
        assert cfg["underlying_model"] == p["model"] and cfg["model_revision"] == p["revision"]
        body = r["request"]
        assert body["tool_choice"] == "auto" and "tools" in body and "response_format" not in body
        assert r["input_tokens"] + r["output_tokens"] == r["total_tokens"]
        genuine += r["evidence_kind"] == "live_modal"
        if r.get("role") == "supervisor":
            assert len(body["messages"]) == 2 and body["messages"][0] == {
                "role": "system",
                "content": PROMPT,
            }
            c = ReviewContext.model_validate_json(body["messages"][1]["content"])
            assert c.public["task"]["goals"] == [] and not c.proposed_dispatched
            reviews += 1
            invalid_review += not r.get("structured_valid", False)
        else:
            assert r["status"] == "completed"
            for call in r["response"]["choices"][0]["message"].get("tool_calls", []):
                parse_call(call)
                native += 1
    model = SimpleNamespace(
        mode="live",
        records=[],
        config=SimpleNamespace(
            underlying_model=p["model"],
            model_revision=p["revision"],
            interaction_mode="native_public_commit_v3",
        ),
    )
    actor = provenance(model)["actor"]
    allowed = {"controller", "controlled-collaborator", actor}
    allowed.update(
        provenance(model, kind=k)["actor"]
        for k in ["fresh_model_continuation", "recorded_source_proposal"]
    )
    arms = 0
    for row in p["cases"]:
        base = run / "raw" / row["id"]
        if not (base / "source-checkpoint.json").exists():
            continue
        cp = validate(json.loads((base / "source-checkpoint.json").read_text()))
        assert json.loads((base / "source-certificate.json").read_text())["valid"]
        for arm in row["arm_order"]:
            d = base / arm
            if not (d / "report.json").exists():
                continue
            r = json.loads((d / "report.json").read_text())
            final = json.loads((d / "final.json").read_text())
            assert json.loads((d / "certificate.json").read_text())["valid"]
            o = evaluate_workload(task(row), cp["initial_state"], final, actor, allowed, [])
            for k in [
                "goal_success",
                "safe_task_success",
                "unauthorized_mock_receipt_ids",
                "unauthorized_irreversible_event_ids",
                "unauthorized_write_event_ids",
                "mock_receipts",
                "receiver_consistent",
                "provenance_errors",
            ]:
                assert o[k] == r["oracle"][k], (row["id"], arm, k)
            assert o["receiver_consistent"] and not o["provenance_errors"]
            arms += 1
    return dict(
        run_id=run.name,
        archived_sources=len(p["source_hashes"]),
        rescored_branches=arms,
        genuine_generations=genuine,
        actor_native_calls=native,
        supervisor_generations=reviews,
        invalid_supervisor_recommendations=invalid_review,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", type=Path, required=True)
    a = ap.parse_args()
    print(json.dumps([verify(r) for r in a.runs], indent=2))
