"""Bounded offline diagnosis of the failed two-action live task; no network clients."""

import argparse
import hashlib
import json
import traceback
from pathlib import Path

from afterclick.agent.decision_schema import CONDITIONAL, conditional_schema
from afterclick.agent.modal_policy import ModalConfig, RecordedOpenAIPolicy, atomic_json


def run(directory):
    protocol = json.loads((directory / "protocol.json").read_text())
    if (directory / "raw/started.json").exists():
        raise ValueError("Use a fresh registered run; preserve previous attempts")
    assert protocol["cost_cap_usd"] == 0 and protocol["attempt_budget"] == 11
    source = directory.parent / protocol["source_run_id"]
    atomic_json(directory / "raw/started.json", {"source": str(source)})
    records = [json.loads(s) for s in (source / "model_calls.jsonl").read_text().splitlines()]
    records = [r for r in records if r["event"] == "finished"]
    attempted = 0
    error = None
    try:
        assert len(records) == 11
        assert len({r["request_sha256"] for r in records}) == 11
        assert all(r["evidence_kind"] == "live_modal" for r in records)
        config = ModalConfig(**records[0]["config"])
        recorded = RecordedOpenAIPolicy(config, records)
        select = {"kind": "select", "target": "Priority", "value": "High"}
        CONDITIONAL.validate_python(select)
        for index, record in enumerate(records):
            attempted += 1
            payload = json.loads(record["request"]["messages"][1]["content"])
            decision = recorded.decide(**payload)
            assert decision.model_dump() == record["decision"]
            request_schema = record["request"]["response_format"]["json_schema"]["schema"]
            assert request_schema == conditional_schema()
            if index >= 3:
                assert "priority to High" in payload["task"]["instruction"]
                assert payload["observation"]["inputs"]["Priority"] == "Normal"
                assert any(
                    g["field"] == "priority" and g["value"] == "High"
                    for g in payload["task"]["goals"]
                )
            row = dict(
                schema_version=1,
                run_id=directory.name,
                case_id=f"record-{index}",
                source_request_id=record["request_id"],
                request_sha256=record["request_sha256"],
                recorded_replay=True,
                independent_live_sample=False,
                valid=True,
                decision=decision.model_dump(),
                model_calls=0,
                cost_usd=0,
            )
            with (directory / "trials.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
        multi = json.loads((source / "multi_action_task/report.json").read_text())
        assert not multi["accepted"] and not multi["task"]["success"]
        assert multi["distinct_changed_controls"] == ["Description"]
        assert multi["effects"]["unauthorized_event_ids"] == []
        for step in multi["steps"][1:]:
            assert "API v2" in step["observation"]["inputs"]["Description"]
            assert step["decision"]["kind"] == "fill"
            assert step["decision"]["target"] == "Description"
        atomic_json(
            directory / "raw/task-audit.json",
            dict(
                omitted_priority_instruction=False,
                omitted_priority_goal=False,
                visible_priority_stays_normal=True,
                description_already_satisfied_before_repeated_actions=True,
                repeated_satisfied_subgoal_actions=7,
                adapter_cache_hits=0,
                distinct_request_hashes=11,
                pydantic_select_priority_allowed=True,
                installed_grammar_select_reachability=None,
                no_unauthorized_effects_in_these_two_tasks=True,
            ),
        )
    except BaseException:
        error = traceback.format_exc()
        (directory / "raw/error.txt").write_text(error)
        with (directory / "trials.jsonl").open("a") as f:
            f.write(json.dumps(dict(event="interrupted_or_failed", error=error)) + "\n")
    atomic_json(
        directory / "metrics.json",
        dict(
            schema_version=1,
            attempted=attempted,
            valid=attempted if error is None else None,
            invalid=0 if error is None else 1,
            unknown=0,
            censored=0,
            passed=error is None,
            model_calls=0,
            cost_usd=0,
            source_journal_sha256=hashlib.sha256(
                (source / "model_calls.jsonl").read_bytes()
            ).hexdigest(),
        ),
    )
    if error:
        raise RuntimeError("Offline audit failed; preserved raw/error.txt")
    print(
        "11/11 recorded outputs match; task and visible Priority present; "
        "model/grammar cause unresolved"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run(args.run)


if __name__ == "__main__":
    main()
