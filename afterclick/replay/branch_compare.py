"""Replay validity is independent of model/task success."""

from afterclick.infrastructure.db import digest
from afterclick.replay.semantic_alignment import align

CONDITIONS = (
    "execute",
    "suppress_fixed",
    "suppress_adaptive",
    "lost_ack",
    "null_execute",
    "null_suppress",
)


def certify(branches):
    required = [name + suffix for name in CONDITIONS for suffix in ("", "_placebo")]
    missing = [name for name in required if not branches.get(name, {}).get("valid")]
    if missing:
        return {"valid": False, "missing_or_failed_branches": missing}
    hashes = {name: digest(branches[name]["checkpoint"]) for name in required}
    prefix = len(set(hashes.values())) == 1
    placebos = {
        name: branches[name]["outcome_hash"] == branches[name + "_placebo"]["outcome_hash"]
        and branches[name]["continuation_hash"] == branches[name + "_placebo"]["continuation_hash"]
        for name in CONDITIONS
    }
    null = branches["null_execute"]["outcome_hash"] == branches["null_suppress"]["outcome_hash"]
    ack = all(
        branches[n].get("ack_evidence", {}).get("verified")
        for n in ("lost_ack", "lost_ack_placebo")
    )
    return {
        "valid": prefix and all(placebos.values()) and null and ack,
        "prefix_equivalent": prefix,
        "checkpoint_hashes": hashes,
        "fixed_policy_placebos": placebos,
        "null_business_outcomes_match": null,
        "committed_lost_ack_verified": ack,
        "excluded_from_equivalence": ["SSE consumer receipt identity/count"],
        "scope": "planted selected action; frozen backend decision window; "
        "recorded-action placebos, not repeated stochastic LLM equivalence",
    }


def compare(branches, certificate):
    if not certificate["valid"]:
        return {"status": "INVALID", "intervention_supported": []}
    contrasts = {}
    for name in ("suppress_fixed", "suppress_adaptive", "lost_ack", "null_suppress"):
        baseline = "null_execute" if name == "null_suppress" else "execute"
        left, right = branches[baseline], branches[name]
        contrasts[name] = {
            "goal_difference": int(left["task"]["success"]) - int(right["task"]["success"]),
            "semantic_effects": align(left["state"], right["state"]),
            "fixed_actions_semantically_valid": all(s["executed"] for s in right["steps"]),
            "interpretation": "paired realized trajectory contrast, not population necessity",
        }
    return {
        "status": "VALID",
        "intervention_supported": contrasts,
        "population_necessity": "NOT_ESTIMATED",
    }
