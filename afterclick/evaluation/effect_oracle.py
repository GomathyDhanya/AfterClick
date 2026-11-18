"""Authorization and historical receipt evidence, not action-ID-based causal estimation."""

from afterclick.contracts.authorization import authorized, matches
from afterclick.contracts.schema import TaskContract

MATERIAL_KINDS = {
    "task.updated",
    "readiness.updated",
    "summary.updated",
    "escalation.created",
    "notification.created",
    "notification.delivered",
    "comment.created",
    "task.compensated",
    "project.compensated",
}


def evaluate_effects(contract: TaskContract, state: dict) -> dict:
    material = [e for e in state["effect_events"] if e["kind"] in MATERIAL_KINDS]
    return {
        "semantic_effect_count": len(material),
        "unauthorized_event_ids": [e["id"] for e in material if not authorized(contract, e)],
        "evidence_type": "observed semantic effects; not a counterfactual causal estimate",
    }


def irreversible_witnesses(contract, before, after, reference, action_id):
    """Require both durable observer receipt and matching ledger event, not a risk flag.

    Union before/after history prevents a fabricated snapshot restore from erasing proof.
    The caller must independently establish the reference validity for causal use.
    """
    reference_keys = {
        (d["notification_id"], d["recipient"]) for d in reference["notification_deliveries"]
    }
    receipts = {
        (d["notification_id"], d["recipient"]): d
        for state in (after, before)
        for d in state["notification_deliveries"]
        if d["action_id"] == action_id
    }
    events = [
        e
        for state in (before, after)
        for e in state["effect_events"]
        if e["action_id"] == action_id and e["kind"] == "notification.delivered"
    ]
    witnesses, unverified = [], []
    for key, receipt in receipts.items():
        if key in reference_keys:
            continue
        candidates = [
            e
            for e in events
            if e["resource"] == receipt["notification_id"]
            and e["actor"] == receipt["recipient"]
            and e["logical_time"] == receipt["logical_time"]
        ]
        if not candidates:
            unverified.append(f"Receipt without matching immutable event: {key}")
        elif any(matches(scope, e) for e in candidates for scope in contract.forbidden_history):
            witnesses.append(
                {
                    "notification_id": key[0],
                    "recipient": key[1],
                    "time": receipt["logical_time"],
                    "event_id": candidates[0]["id"],
                }
            )
    for event in events:
        if (event["resource"], event["actor"]) not in receipts:
            unverified.append(f"Delivery event without observer receipt: {event['id']}")
    return witnesses, sorted(set(unverified))
