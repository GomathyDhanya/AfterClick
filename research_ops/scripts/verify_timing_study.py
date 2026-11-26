"Read-only re-score saved live branches and verify their immutable evidence inputs."

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from afterclick.extensions.native_tools import parse_call
from afterclick.model_sprint.records import sha
from afterclick.oecr.client import validate
from afterclick.review.study_runner import task
from afterclick.tcope.provenance import provenance
from afterclick.tcope.workload_oracle import evaluate_workload
from research_ops.scripts.analyze_timing_study import read_lines


def verify(run):
    p = json.loads((run / "protocol.json").read_text())
    checked = 0
    for name, expected in p["source_hashes"].items():
        assert sha(run / "raw/source-qualified" / name) == expected, name
        checked += 1
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
    generations = 0
    native_calls = 0
    for record in read_lines(run / "model_calls.jsonl"):
        if record["event"] != "finished":
            continue
        assert record["status"] == "completed" and not record["billing_uncertain"]
        cfg = record["config"]
        assert cfg["underlying_model"] == p["model"] and cfg["model_revision"] == p["revision"]
        body = record["request"]
        assert body["tool_choice"] == "auto" and "tools" in body and "response_format" not in body
        response = record["response"]
        u = response["usage"]
        assert u["prompt_tokens"] + u["completion_tokens"] == u["total_tokens"]
        assert (
            u["completion_tokens"] <= p["max_output_tokens"]
            and u["prompt_tokens"] <= p["max_input_tokens"]
        )
        for call in response["choices"][0]["message"].get("tool_calls", []):
            parse_call(call)
            native_calls += 1
        generations += 1
    for row in p["cases"]:
        base = run / "raw" / row["id"]
        if not (base / "source-checkpoint.json").exists():
            continue
        cp = validate(json.loads((base / "source-checkpoint.json").read_text()))
        assert json.loads((base / "source-certificate.json").read_text())["valid"]
        for arm in row["arm_order"]:
            a = base / arm
            if not (a / "report.json").exists():
                continue
            report = json.loads((a / "report.json").read_text())
            final = json.loads((a / "final.json").read_text())
            assert json.loads((a / "certificate.json").read_text())["valid"]
            oracle = evaluate_workload(task(row), cp["initial_state"], final, actor, allowed, [])
            for key in [
                "goal_success",
                "safe_task_success",
                "unauthorized_mock_receipt_ids",
                "unauthorized_irreversible_event_ids",
                "unauthorized_write_event_ids",
                "mock_receipts",
                "receiver_consistent",
                "provenance_errors",
            ]:
                assert oracle[key] == report["oracle"][key], (
                    row["id"],
                    arm,
                    key,
                    oracle[key],
                    report["oracle"][key],
                )
            assert oracle["receiver_consistent"] and not oracle["provenance_errors"]
            assert final["tc_runtime"][0]["clock_ms"] >= p.get("min_observation_clock_ms", 0)
            arms += 1
    return dict(
        run_id=run.name,
        verified_archived_sources=checked,
        rescored_arms=arms,
        genuine_generations=generations,
        native_tool_calls=native_calls,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, nargs="+", required=True)
    a = ap.parse_args()
    print(json.dumps([verify(r) for r in a.runs], indent=2))
