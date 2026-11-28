"""Preserve invalid-run reasons and inspect their raw protective proposals separately."""

import collections
import json
from pathlib import Path

from analyze import HERE, dump, encoded_protection_hints, parse_native, read, sha, table
from enrich import loadcsv


def main():
    h = HERE / "provenance/historical"
    release = read(h / "research_ops/completion_v12/final_package/RELEASE_INDEX.json")
    episodes = [e for e in loadcsv("executions.csv") if e["technical_validity"] != "VALID"]
    by_episode = {}
    for cohort in ["primary", "larger"]:
        for inv in read(h / release["evidence_root"] / f"{cohort}-trace-inventory/requests.json"):
            if inv["role"] == "actor":
                by_episode.setdefault(cohort + ":" + inv["episode"], []).append(inv)
    population, proposals, source_hashes = [], [], {}
    for ep in episodes:
        rp = h / ep["raw_path"]
        result = read(rp)
        events = read(rp.parent / "events.json", [])
        actions = read(rp.parent / "browser-actions.json", [])
        requests = by_episode.get(ep["episode_key"], [])
        error = (result.get("error") or "").strip().splitlines()
        row = dict(
            episode_key=ep["episode_key"],
            task_id=ep["task_id"],
            cohort=ep["cohort"],
            policy=ep["policy"],
            clean=ep["clean"],
            pending_allowed=ep["pending_allowed"],
            original_technical_validity=ep["technical_validity"],
            terminal_exception=error[-1] if error else "UNKNOWN",
            score_available=result.get("score") is not None,
            actor_requests=len(requests),
            responses_received=0,
            protective_proposals=0,
            original_outcome_preserved=True,
            raw_path=ep["raw_path"],
            raw_sha256=sha(rp),
        )
        for inv in requests:
            ip = h / Path(inv["input"]).relative_to(release["original_workspace_root"])
            assert sha(ip) == inv["input_sha256"]
            source_hashes[str(ip.relative_to(h))] = inv["input_sha256"]
            if not inv.get("response"):
                continue
            op = h / Path(inv["response"]).relative_to(release["original_workspace_root"])
            assert sha(op) == inv["response_sha256"]
            source_hashes[str(op.relative_to(h))] = inv["response_sha256"]
            out = read(op)
            try:
                message = json.loads(out["raw"])["choices"][0]["message"]
            except (ValueError, KeyError, IndexError):
                continue
            row["responses_received"] += 1
            parsed = parse_native(message)
            for ci, call in enumerate(message.get("tool_calls", [])):
                fn = call.get("function", {})
                try:
                    args = json.loads(fn.get("arguments", ""))
                except (ValueError, TypeError):
                    args = {}
                acts = args.get("actions", []) if isinstance(args, dict) else []
                if isinstance(acts, list):
                    hints = [
                        (ai, a)
                        for ai, a in enumerate(acts)
                        if isinstance(a, dict) and a.get("id") in {"suspend", "cancel"}
                    ]
                else:
                    hints = [(None, dict(id=hint)) for hint in encoded_protection_hints(acts)]
                for ai, action in hints:
                    dispatched = [
                        e
                        for e in events
                        if e["kind"] == "actor.gateway_action"
                        and e.get("request_id") == inv["request_id"]
                        and e.get("tool_call_id") == call.get("id")
                        and e.get("action") == action
                    ]
                    event = dispatched[0] if len(dispatched) == 1 else None
                    observed = actions[event["gateway_index"]] if event else None
                    proposals.append(
                        dict(
                            episode_key=ep["episode_key"],
                            policy=ep["policy"],
                            clean=ep["clean"],
                            pending_allowed=ep["pending_allowed"],
                            original_technical_validity=ep["technical_validity"],
                            request_id=inv["request_id"],
                            tool_call_id=call.get("id"),
                            call_index=ci,
                            action_index=ai,
                            action=action,
                            parsed_schema=parsed is not None,
                            dispatch=bool(event),
                            application_status=observed["result"]["status"]
                            if observed
                            else "UNKNOWN",
                            outcome="MALFORMED_TOOL_SYNTAX"
                            if parsed is None
                            else "DISPATCH_RECORDED_INVALID_EPISODE"
                            if event
                            else "UNKNOWN_INVALID_EPISODE",
                            response_end_mono=out.get("end_mono"),
                            raw_path=str(op.relative_to(h)),
                            raw_sha256=inv["response_sha256"],
                            raw_pointer="/raw",
                            complete_episode_score="UNKNOWN",
                        )
                    )
                    row["protective_proposals"] += 1
        population.append(row)
    table(HERE / "invalid_executions.csv", population)
    table(
        HERE / "invalid_protection_proposals.csv",
        proposals,
        keys=None if proposals else ["episode_key", "request_id", "outcome"],
    )
    dump(HERE / "provenance/invalid_request_hashes.json", source_hashes)
    report = read(HERE / "report.json")
    report["invalid_population_audit"] = dict(
        episodes=len(population),
        terminal_exceptions=dict(collections.Counter(x["terminal_exception"] for x in population)),
        scores_available=sum(x["score_available"] for x in population),
        actor_requests=sum(x["actor_requests"] for x in population),
        responses_received=sum(x["responses_received"] for x in population),
        protective_proposals=len(proposals),
        proposal_episodes=len({x["episode_key"] for x in proposals}),
        proposal_outcomes=dict(collections.Counter(x["outcome"] for x in proposals)),
        scope=(
            "Invalid outcomes remain unknown and are not pooled with valid model failures; "
            "raw proposals are retained separately"
        ),
    )
    dump(HERE / "report.json", report)
    print(json.dumps(report["invalid_population_audit"], indent=2))


if __name__ == "__main__":
    main()
