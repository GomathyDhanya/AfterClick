"""Explicit model-visible allowlist. This module never reads research state."""

import json


def observe(gateway):
    visible = gateway.observe()
    page = gateway.page
    controls = []
    for label, value in visible["inputs"].items():
        element = page.get_by_label(label, exact=True)
        controls.append(
            {"role": "input", "name": label, "value": value, "enabled": element.is_enabled()}
        )
    for element in page.get_by_role("button").all():
        if element.is_visible():
            controls.append(
                {"role": "button", "name": element.inner_text(), "enabled": element.is_enabled()}
            )
    result = {
        "text": visible["text"],
        "inputs": visible["inputs"],
        "controls": controls,
        "save_status": page.get_by_role("status").inner_text(),
    }
    if len(json.dumps(result).encode()) > 24000:
        raise ValueError("Observation exceeds bounded context; no silent truncation")
    return result


def public_history(history, *, blind_interventions=True):
    # Exclude action IDs, intervention labels, hidden ACK evidence, raw request logs,
    # error traces, pre-observation hashes, and every backend/oracle field.
    result = []
    for entry in history:
        feedback = entry["feedback"]["status"]
        if blind_interventions and feedback == "suppressed":
            # Suppression twins use a controlled neutral acknowledgment. The raw
            # Gateway trace retains suppression; the policy cannot see the arm label.
            feedback = "completed"
        result.append({"action": dict(entry["action"]), "feedback": feedback})
    return result


def public_task(contract):
    return {
        "instruction": contract.instruction,
        "goals": [goal.model_dump() for goal in contract.goals],
    }
