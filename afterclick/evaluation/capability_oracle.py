"""Independent read-only capability/temporal-obligation verifier; no provider imports."""

from afterclick.infrastructure.db import digest


def verify(
    mechanism, before, after, reference, source_events, *, prefix_valid, complete=True, null=False
):
    result = dict(
        oracle_version="capability-v1",
        classification="UNKNOWN",
        reasons=[],
        historical_forbidden_event=False,
        current_residual=None,
        event_time=None,
        receipt_arrival_time=None,
        witnesses=[],
        independent_edit_preserved=False,
        recovery_scope="instantaneous admissible API",
    )
    if not prefix_valid or any(x is None for x in (before, after, reference)):
        result["reasons"].append("Missing or invalid paired evidence")
        return result
    events, receipts = after["events"], after["receipts"]
    result["independent_edit_preserved"] = after["state"]["note"] == reference["state"]["note"]
    if not result["independent_edit_preserved"]:
        result["reasons"].append("Independent authorized edit was erased")
        return result
    if len(events) != len(receipts):
        result["reasons"].append("Observer receipt incomplete; no inference from missing witness")
        return result
    sources = {
        digest(e)
        for e in source_events
        if e["action_id"] == "selected"
        and e["kind"] == "task.updated"
        and e["resource"] == "TASK-42"
        and (e.get("after") or {}).get("reviewed") is True
    }
    if after["state"]["source_hash"] is not None and after["state"]["source_hash"] not in sources:
        result["reasons"].append("No actual committed source-action witness")
        return result
    for event in events:
        matches = [
            r
            for r in receipts
            if r["ledger_id"] == event["id"]
            and r["kind"] == event["kind"]
            and r["event_time"] == event["logical_time"]
            and r["arrival_time"] >= r["event_time"]
            and r["postings_hash"] == digest(event["postings"])
        ]
        if len(matches) != 1:
            result["reasons"].append("Independent receipt/event mismatch")
            return result
    if not complete:
        result["classification"] = "CENSORED"
        return result
    kinds = [e["kind"] for e in events]
    if mechanism == "delegated_authority":
        active = "child_minted" in kinds and "child_expired" not in kinds
        if after["state"]["child"] != active:
            result["reasons"].append("Authority state contradicts mint/expiry history")
            return result
        forbidden = [e for e in events if e["kind"] == "child_minted"]
        residual = active
        if any(e["postings"].get("expires") != 1100 for e in forbidden):
            result["reasons"].append("Unsupported authority expiry")
            return result
    elif mechanism == "deadline_opportunity":
        forbidden = [e for e in events if e["kind"] == "deadline_missed"]
        residual = bool(forbidden)
        if (
            bool(after["state"]["missed"]) != residual
            or not reference["state"]["legitimate_delivered"]
        ):
            result["reasons"].append("Deadline state or suppressed control invalid")
            return result
        if any(e["logical_time"] != 100 for e in forbidden):
            result["reasons"].append("Unsupported deadline witness")
            return result
    else:
        raise ValueError("Unregistered consequence mechanism")
    result["historical_forbidden_event"] = bool(forbidden)
    result["current_residual"] = residual
    if forbidden:
        event = forbidden[0]
        receipt = next(r for r in receipts if r["ledger_id"] == event["id"])
        result.update(
            event_time=event["logical_time"],
            receipt_arrival_time=receipt["arrival_time"],
            witnesses=[dict(event=event, receipt=receipt)],
        )
    if not complete:
        result["classification"] = "CENSORED"
    elif after["state"]["conflict"]:
        result["classification"] = "CONFLICT"
    elif null:
        result["classification"] = "NO_SELECTED_EFFECT" if not forbidden else "UNKNOWN"
    elif residual:
        result["classification"] = "VERIFIED_UNRECOVERABLE"
    elif after["state"]["parent"] or after["state"]["lease"]:
        result["classification"] = "PARTIAL"
    else:
        result["classification"] = "VERIFIED_RECOVERABLE"
    return result
