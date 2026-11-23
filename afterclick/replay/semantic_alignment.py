"""Align observable business effects, not action numbers or generated row IDs."""

from collections import Counter

from afterclick.evaluation.effect_oracle import MATERIAL_KINDS
from afterclick.infrastructure.db import digest


def semantic_effects(state):
    events = {event["id"]: event for event in state["effect_events"]}

    def resource(event, visited=frozenset()):
        if event["id"] in visited:
            return {"unresolved": "parent_cycle"}
        if event["kind"] in {
            "notification.created",
            "notification.delivered",
            "escalation.created",
        }:
            parents = [events[p] for p in event["parents"] if p in events]
            if len(parents) != 1:
                return {"unresolved": event["resource"]}
            return resource(parents[0], visited | {event["id"]})
        return event["resource"]

    result = []
    for event in events.values():
        if event["kind"] not in MATERIAL_KINDS:
            continue
        # Field-level transitions allow alignment when tools batch or split edits.
        before, after = event["before"] or {}, event["after"] or {}
        fields = sorted(set(before) | set(after))
        for field in fields or [None]:
            effect = {
                "kind": event["kind"],
                "resource": resource(event),
                "field": field,
                "before": before.get(field),
                "after": after.get(field),
            }
            result.append(
                {
                    "signature": digest(effect),
                    "effect": effect,
                    "event_id": event["id"],
                    "action_id": event["action_id"],
                }
            )
    return result


def align(left, right):
    a, b = semantic_effects(left), semantic_effects(right)
    ac, bc = Counter(e["signature"] for e in a), Counter(e["signature"] for e in b)
    descriptions = {e["signature"]: e["effect"] for e in a + b}
    return {
        "matched_count": sum((ac & bc).values()),
        "only_left": [{"effect": descriptions[k], "count": n} for k, n in (ac - bc).items()],
        "only_right": [{"effect": descriptions[k], "count": n} for k, n in (bc - ac).items()],
        "method": "multiset of business record/field transitions; generated IDs via parent roots",
    }


def evidence_edges(state):
    events = state["effect_events"]
    return {
        "provenance": [{"action_id": e["action_id"], "event_id": e["id"]} for e in events],
        "declared_parent": [{"source": p, "target": e["id"]} for e in events for p in e["parents"]],
        "happens_before": [
            {"source": a["id"], "target": b["id"]} for a, b in zip(events, events[1:])
        ],
        "data_dependency": [],
        "limitations": "Journal order and declared parents do not prove causal necessity. "
        "No dynamic read-set instrumentation; data dependencies not inferred.",
    }


def fixed_precondition(decision, original, current):
    if decision.kind in {"done", "navigate", "wait", "read"}:
        return True
    role = "button" if decision.kind == "click" else "input"
    target = decision.target
    old = [c for c in original["controls"] if c["role"] == role and c["name"] == target]
    new = [c for c in current["controls"] if c["role"] == role and c["name"] == target]
    if len(old) != 1 or len(new) != 1 or not new[0]["enabled"]:
        return False
    if role == "input" and old[0]["value"] != new[0]["value"]:
        return False
    return original["save_status"] == current["save_status"]
