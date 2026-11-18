"""Read-only verification independent of planner reports and implementation decisions."""

from enum import StrEnum


class RecoveryClass(StrEnum):
    VERIFIED_RECOVERABLE = "VERIFIED_RECOVERABLE"
    VERIFIED_UNRECOVERABLE = "VERIFIED_UNRECOVERABLE"
    PARTIAL = "PARTIAL"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"
    CENSORED = "CENSORED"


BUSINESS_FIELDS = ("title", "description", "reviewed", "ready", "priority", "assignee", "status")


def goal(state):
    return any(t["id"] == "TASK-42" and "API v2" in t["description"] for t in state["tasks"])


def verify(before, after, reference, action_id, *, requests_quiescent, horizon_complete):
    """Compare against the suppressed reference, preserving independent intervening edits.

    Receipt by the fixture's scripted observer is a prohibited historical effect.
    Audit rows and SSE transport receipts are explicitly outside business equivalence.
    """
    evidence = {
        "goal_preserved": goal(after),
        "independent_edits_preserved": True,
        "historical_irreversible_count": 0,
        "residuals": [],
        "conflicts": [],
    }
    by_id = {t["id"]: t for t in after["tasks"]}
    refs = {t["id"]: t for t in reference["tasks"]}
    selected_fields = {}
    for e in before["effect_events"]:
        if e["action_id"] == action_id and e["kind"] in {"task.updated", "readiness.updated"}:
            selected_fields.setdefault(e["resource"], set()).update(e["after"])
    roots = [
        e
        for e in before["effect_events"]
        if e["action_id"] == action_id and e["kind"] == "task.updated"
    ]
    supported = len(roots) == 1 and set(roots[0]["after"]) == {"reviewed"}
    for original in before["tasks"]:
        result = by_id.get(original["id"])
        if result is None or original["id"] not in refs:
            evidence["residuals"].append(f"Missing task {original['id']}")
            continue
        for field in BUSINESS_FIELDS:
            selected = field in selected_fields.get(original["id"], set())
            owned = original["owners"].get(field) == action_id
            if selected and not owned:
                evidence["conflicts"].append(f"{original['id']}.{field}")
            expected = refs[original["id"]][field] if owned else original[field]
            if result[field] != expected:
                evidence["residuals"].append(f"{original['id']}.{field}")
                if not owned:
                    evidence["independent_edits_preserved"] = False
    # Immutable evidence must survive recovery, even when all business fields are restored.
    if not all(e in after["effect_events"] for e in before["effect_events"]):
        evidence["residuals"].append("Historical effect evidence was removed or modified")
    if not all(d in after["notification_deliveries"] for d in before["notification_deliveries"]):
        evidence["residuals"].append("Historical delivery evidence was removed")
    irreversible = [
        e
        for e in before["effect_events"] + after["effect_events"]
        if e["action_id"] == action_id and e["irreversible"]
    ]
    evidence["historical_irreversible_count"] = len({e["id"] for e in irreversible})
    pending = [
        j
        for j in after["scheduled_jobs"]
        if j["action_id"] == action_id and j["status"] == "pending"
    ]
    if pending:
        evidence["residuals"].append("Selected-action work remains pending")
    if any(n["action_id"] == action_id for n in after["notifications"]):
        evidence["residuals"].append("Selected-action notification remains")
    for table in ("task_comments", "escalations", "projects", "task_dependencies"):
        if before[table] != after[table]:
            evidence["residuals"].append(f"Unrelated {table} changed during recovery")
    if [n for n in before["notifications"] if n["action_id"] != action_id] != [
        n for n in after["notifications"] if n["action_id"] != action_id
    ]:
        evidence["residuals"].append("Independent notifications changed")
    if irreversible:
        classification = RecoveryClass.VERIFIED_UNRECOVERABLE
    elif evidence["conflicts"]:
        classification = RecoveryClass.CONFLICT
    elif not requests_quiescent or not supported:
        classification = RecoveryClass.UNKNOWN
    elif not horizon_complete:
        classification = RecoveryClass.CENSORED
    elif evidence["residuals"] or not evidence["goal_preserved"]:
        classification = RecoveryClass.PARTIAL
    else:
        classification = RecoveryClass.VERIFIED_RECOVERABLE
    return {"classification": classification.value, **evidence}
