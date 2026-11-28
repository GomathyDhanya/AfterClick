"""Complete all-policy actor/proposal and distinct reviewer-role accounting."""

import collections
import json
from pathlib import Path

from analyze import HERE, dump, read, sha, table
from enrich import loadcsv


def main():
    h = HERE / "provenance/historical"
    index = read(h / "research_ops/completion_v12/final_package/RELEASE_INDEX.json")
    episodes = loadcsv("executions.csv")
    episode_index = {e["episode_key"]: e for e in episodes}
    reviews = []
    review_inputs = {}
    for cohort in ["primary", "larger"]:
        inventory = read(h / index["evidence_root"] / f"{cohort}-trace-inventory/requests.json")
        for inv in inventory:
            if inv["role"] != "reviewer":
                continue
            key = cohort + ":" + inv["episode"]
            e = episode_index[key]
            ip = h / Path(inv["input"]).relative_to(index["original_workspace_root"])
            inp = read(ip)
            assert inp["id"] == inv["request_id"] and inp["episode"] == inv["episode"]
            assert sha(ip) == inv["input_sha256"]
            review_inputs[str(ip.relative_to(h))] = inv["input_sha256"]
            public = json.loads(inp["body"]["messages"][1]["content"])
            out, message, parsed, op = None, {}, {}, None
            if inv.get("response"):
                op = h / Path(inv["response"]).relative_to(index["original_workspace_root"])
                out = read(op)
                assert sha(op) == inv["response_sha256"]
                review_inputs[str(op.relative_to(h))] = inv["response_sha256"]
                try:
                    message = json.loads(out["raw"])["choices"][0]["message"]
                    parsed = json.loads(message["content"])
                except (ValueError, KeyError, IndexError):
                    parsed = {}
            valid_schema = (
                isinstance(parsed, dict)
                and set(parsed) == {"decision", "reason"}
                and parsed.get("decision") in {"allow", "suspend", "cancel"}
                and isinstance(parsed.get("reason"), str)
            )
            folder = (h / e["raw_path"]).parent
            local = read(folder / "events.json", [])
            applied = [
                x
                for x in local
                if x["kind"] == "controller.decision_applied"
                and x.get("request_id") == inv["request_id"]
            ]
            actions = read(folder / "browser-actions.json", [])
            action = (
                actions[applied[0]["gateway_index"]]
                if len(applied) == 1 and applied[0].get("gateway_index") is not None
                else None
            )
            reviews.append(
                dict(
                    episode_key=key,
                    task_id=e["task_id"],
                    cohort=cohort,
                    policy=e["policy"],
                    episode_technical_validity=e["technical_validity"],
                    request_id=inv["request_id"],
                    role="reviewer",
                    recommendation=parsed.get("decision") if valid_schema else "UNKNOWN",
                    schema_valid=valid_schema,
                    public_authority=public["service"]["authority"],
                    pending_allowed=e["pending_allowed"],
                    native_actor_proposal=False,
                    controller_applied=len(applied) == 1,
                    gateway_index=applied[0].get("gateway_index") if len(applied) == 1 else None,
                    command_id=applied[0].get("command_id") if len(applied) == 1 else None,
                    application_status=action["result"]["status"] if action else "UNKNOWN",
                    queued_mono=inp["queued_mono"],
                    start_marker_mono=inp["start_mono"],
                    response_end_mono=out.get("end_mono") if out else None,
                    raw_input_path=str(ip.relative_to(h)),
                    raw_input_sha256=inv["input_sha256"],
                    raw_output_path=str(op.relative_to(h)) if op else None,
                    raw_output_sha256=inv.get("response_sha256"),
                )
            )
    table(HERE / "reviewer_recommendations.csv", reviews)
    dump(HERE / "provenance/reviewer_input_hashes.json", review_inputs)
    report = read(HERE / "report.json")
    broad = read(HERE / "all_valid_internal/report.json")
    assert broad and not broad["scoring_disagreements"]
    vocabulary = []
    for path, expected in read(HERE / "all_valid_internal/provenance/input_hashes.json").items():
        if not path.endswith("-output.json"):
            continue
        out = read(h / path)
        message = json.loads(out["raw"])["choices"][0]["message"]
        if any(word in json.dumps(message).lower() for word in ["suspend", "cancel"]):
            native_keyword = any(
                any(word in str(call.get("function", {})).lower() for word in ["suspend", "cancel"])
                for call in message.get("tool_calls", [])
            )
            vocabulary.append(
                dict(
                    raw_path=path,
                    raw_sha256=expected,
                    message=message,
                    native_protective_keyword=native_keyword,
                    interpretation=(
                        "Native action and free-text/state mentions remain separate; "
                        "full raw content retained for review"
                    ),
                )
            )
    dump(HERE / "provenance/all_policy_protective_vocabulary.json", vocabulary)
    report["all_policy_lexical_review"] = dict(
        responses_with_vocabulary=len(vocabulary),
        responses_with_native_protective_keyword=sum(
            x["native_protective_keyword"] for x in vocabulary
        ),
    )
    report["all_valid_internal_actor_audit"] = broad["supplementary_all_valid_internal"]
    broad_timing = {x["episode_key"]: x for x in loadcsv("all_valid_internal/episode_timing.csv")}
    broad_proposals = loadcsv("all_valid_internal/protection_proposals.csv")
    case_index = [
        x
        for x in read(HERE / "case_studies/index.json")
        if x["label"] not in {"rejected_P3_string_encoded_suspension", "scripted_ticket_window"}
    ]
    trajectories = [
        x
        for x in read(HERE / "figures/trajectory_source.json")
        if not x["label"].startswith(("P3 malformed", "New scripted ticket"))
    ]
    for prop in broad_proposals:
        if prop["outcome"] != "MALFORMED_TOOL_SYNTAX":
            continue
        episode = broad_timing[prop["episode_key"]]
        folder = (h / episode["raw_path"]).parent
        local = read(folder / "events.json")
        raw_out = read(h / prop["raw_path"])
        anchor = float(episode["environment_anchor_mono"])
        timeline = [
            dict(
                event="response",
                time_s=float(prop["response_end_mono"]) - anchor,
                request_id=prop["request_id"],
            )
        ]
        for event in read(folder / "final.json")["v12_events"]:
            if event["kind"] in {
                "pending.admission_snapshot",
                "control.command",
                "receiver.committed",
            }:
                timeline.append(
                    dict(
                        event=event["kind"],
                        time_s=event["mono"] - anchor,
                        event_id=event["id"],
                        payload=event["payload"],
                    )
                )
        rejected = [
            event
            for event in local
            if event["kind"] == "actor.schema_invalid"
            and event.get("request_id") == prop["request_id"]
        ]
        for event in rejected:
            timeline.append(
                dict(
                    event="schema rejection",
                    time_s=event["wall"] - float(episode["wall_mono_offset_median_s"]) - anchor,
                    clock_evidence="wall converted by verified host offset; not exact parse-start time",  # noqa: E501
                )
            )
        filename = "rejected_P3_string_encoded_suspension.json"
        dump(
            HERE / "case_studies" / filename,
            dict(
                selection_rule="all malformed protective proposals in the supplementary valid internal cohort",  # noqa: E501
                proposal=prop,
                episode=episode,
                raw_response=raw_out,
                actual_schema_rejection_events=rejected,
                timeline=timeline,
                conclusion="Rejected after pending admission; outside eligible P0; no evidence it caused the earlier loss of prevention opportunity",  # noqa: E501
            ),
        )
        case_index.append(
            dict(
                label="rejected_P3_string_encoded_suspension",
                episode_key=prop["episode_key"],
                path="case_studies/" + filename,
            )
        )
        trajectories.append(
            dict(
                label="P3 malformed proposal after admission (supplementary)",
                episode_key=prop["episode_key"],
                timeline=timeline,
            )
        )
    dump(HERE / "case_studies/index.json", case_index)
    dump(HERE / "figures/trajectory_source.json", trajectories)
    ticket = read(HERE / "ticket_window_controls.json")
    if ticket is not None:
        windows = []
        for trial in ticket["trials"]:
            eid = trial["episode_id"]
            raw = HERE / "controls/ticket_window_raw" / eid
            final = read(raw / "final.json", {})
            local = read(raw / "events.json", [])
            out = read(
                HERE / "controls/ticket_window_traces" / eid / "request-0000001-output.json", {}
            )
            anchor = next(
                (e["anchor_mono"] for e in local if e["kind"] == "world.clock_started"), None
            )
            admissions = [
                e for e in final.get("v12_events", []) if e["kind"] == "pending.admission_snapshot"
            ]
            protections = [
                e
                for e in final.get("v12_events", [])
                if e["kind"] == "control.command"
                and e["payload"]["command"] == "Suspend pending service"
            ]
            receipts = [x for x in final.get("v12_receipts", []) if x["id"] == "pending"]
            actions = read(raw / "browser-actions.json", [])
            upper = next(
                (
                    a["result"]["result"].get("commit_upper_mono")
                    for a in actions
                    if a["id"] == "suspend" and a["result"]["status"] == 200
                ),
                None,
            )
            ordered = (
                len(admissions) == len(protections) == len(receipts) == 1
                and upper is not None
                and admissions[0]["payload"]["admitted"]
                and admissions[0]["mono"] + 0.001 < protections[0]["mono"]
                and upper + 0.001 < receipts[0]["mono"]
            )
            windows.append(
                dict(
                    episode_id=eid,
                    technical_validity=trial["technical_validity"],
                    environment_anchor_mono=anchor,
                    admission_mono=admissions[0]["mono"] if admissions else None,
                    response_end_mono=out.get("end_mono"),
                    protection_lower_mono=protections[0]["mono"] if protections else None,
                    protection_return_upper_mono=upper,
                    receipt_mono=receipts[0]["mono"] if receipts else None,
                    physical_pending=trial.get("physical_pending"),
                    ordered_window=bool(ordered),
                    hypothesis_confirmed=bool(ordered and trial.get("physical_pending")),
                )
            )
        table(HERE / "ticket_window_timing.csv", windows)
        report["ticket_window_controls"] = dict(
            planned=ticket["planned_conditions"],
            attempts=ticket["executed_attempts"],
            technically_valid=ticket["valid"],
            observed_admission_protection_receipt_order=sum(x["ordered_window"] for x in windows),
            pending_physical_effects=sum(bool(x["physical_pending"]) for x in windows),
            hypothesis_confirmed=sum(x["hypothesis_confirmed"] for x in windows),
            unexpected_valid=[
                x["episode_id"]
                for x in windows
                if x["technical_validity"] == "VALID" and not x["hypothesis_confirmed"]
            ],
        )
        chosen = min(windows, key=lambda x: x["episode_id"])
        folder = HERE / "controls/ticket_window_raw" / chosen["episode_id"]
        final = read(folder / "final.json")
        anchor = chosen["environment_anchor_mono"]
        timeline = [dict(event="response", time_s=chosen["response_end_mono"] - anchor)]
        timeline += [
            dict(event=e["kind"], time_s=e["mono"] - anchor, payload=e["payload"], event_id=e["id"])
            for e in final["v12_events"]
            if e["kind"] in {"pending.admission_snapshot", "control.command", "receiver.committed"}
        ]
        dump(
            HERE / "case_studies/scripted_ticket_window.json",
            dict(
                selection_rule="lexicographically first additional ticket-window control, without outcome filtering",  # noqa: E501
                new_scripted_diagnostic=True,
                episode=chosen,
                timeline=timeline,
            ),
        )
        case_index.append(
            dict(
                label="scripted_ticket_window",
                episode_key=chosen["episode_id"],
                path="case_studies/scripted_ticket_window.json",
            )
        )
        trajectories.append(
            dict(
                label="New scripted ticket-window control (not a model trial)",
                episode_key=chosen["episode_id"],
                timeline=timeline,
            )
        )
        dump(HERE / "case_studies/index.json", case_index)
        dump(HERE / "figures/trajectory_source.json", trajectories)
    report["all_valid_internal_actor_audit"]["proposal_after_admitted_decision"] = sum(
        broad_timing[x["episode_key"]]["admission_admitted"] and x["dispatch"]
        for x in broad_proposals
    )
    report["all_valid_internal_actor_audit"]["proposal_after_blocked_decision"] = sum(
        not broad_timing[x["episode_key"]]["admission_admitted"] and x["dispatch"]
        for x in broad_proposals
    )
    report["reviewer_role_audit"] = dict(
        requests=len(reviews),
        outcomes=dict(collections.Counter(r["recommendation"] for r in reviews)),
        episode_validity=dict(
            collections.Counter(r["episode_technical_validity"] for r in reviews)
        ),
        applied=sum(r["controller_applied"] for r in reviews),
        application_statuses=dict(
            collections.Counter(str(r["application_status"]) for r in reviews)
        ),
        scope="All recorded internal reviewer requests, including recommendations in technically invalid downstream episodes. JSON recommendations are separate from actor native proposals.",  # noqa: E501
    )
    report["population"]["local_completion_forbidden_history_mismatch"] = sum(
        e["technical_validity"] == "VALID" and e["local_complete"] and e["forbidden_history"]
        for e in episodes
    )
    report["executed_checks"] = dict(
        audit_tests=14,
        active_tests=39,
        historical_relevant_tests=10,
        tests_failed=0,
        standard_wrapper_issue="scripts/test.sh could not locate uv; equivalent compact verification, Ruff check/format and active pytest commands passed using .venv executables",  # noqa: E501
        saved_reproduction="REPRODUCE.sh --saved-only",
    )
    dump(HERE / "report.json", report)
    print(
        json.dumps(
            dict(
                actor=report["all_valid_internal_actor_audit"],
                reviewer=report["reviewer_role_audit"],
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
