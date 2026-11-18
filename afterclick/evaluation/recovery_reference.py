"""Independent bounded verifier. No imports of domain mutations, planner, or model.

It verifies executed compensation witnesses. It is not an exhaustive feasibility solver.
Only historical observer receipts prove impossibility within the stated capability model.
"""

from afterclick.contracts.schema import BUSINESS_FIELDS, TaskContract
from afterclick.evaluation.effect_oracle import irreversible_witnesses
from afterclick.evaluation.task_oracle import evaluate_task

FIELD_EFFECTS = {
    "task.updated": "tasks",
    "readiness.updated": "tasks",
    "summary.updated": "projects",
}
KNOWN_KINDS = {
    *FIELD_EFFECTS,
    "outbox.published",
    "notification.created",
    "notification.delivered",
    "escalation.created",
}


def verify_recovery(
    contract: TaskContract,
    before,
    after,
    reference,
    action_id,
    *,
    reference_validated: bool,
    requests_quiescent: bool,
    horizon_complete: bool,
):
    required_tables = {
        "tasks",
        "projects",
        "effect_events",
        "notification_deliveries",
        "scheduled_jobs",
        "notifications",
        "escalations",
        "task_comments",
        "task_dependencies",
        "runtime",
    }
    complete_evidence = all(required_tables <= state.keys() for state in (before, after, reference))
    if not complete_evidence:
        return {
            "oracle_version": "contract-recovery-v1",
            "contract_id": contract.contract_id,
            "classification": "UNKNOWN",
            "goal_preserved": False,
            "independent_edits_preserved": False,
            "first_verified_irreversible_time": None,
            "uncertainty_reasons": ["Incomplete state evidence"],
            "irreversible_witnesses": [],
        }
    root_events = [
        e
        for e in before["effect_events"]
        if e["action_id"] == action_id and e["kind"] == "task.updated"
    ]
    events = [e for e in before["effect_events"] if e["action_id"] == action_id]
    affected = {}
    unknown = []
    if horizon_complete and after["runtime"][0]["logical_time"] < contract.horizon:
        unknown.append("Claimed horizon has not been observed")
    for event in events:
        table = FIELD_EFFECTS.get(event["kind"])
        if table:
            affected.setdefault((table, event["resource"]), set()).update(event["after"] or {})
        elif event["kind"] not in KNOWN_KINDS:
            unknown.append(f"Unsupported semantic effect {event['kind']}")
    if (
        len(root_events) != 1
        or root_events[0]["resource"] != contract.selected_action.record_id
        or (set(root_events[0]["after"]) != {contract.selected_action.field})
    ):
        unknown.append("Unsupported or missing selected root mutation")
    required = {"restore_owned_field", "cancel_pending", "delete_owned_derived"}
    if any(e["kind"] == "summary.updated" for e in events):
        required.add("restore_owned_summary")
    if not required <= set(contract.supported_compensations):
        unknown.append("Contract does not declare the necessary recovery interfaces")
    if any(e["action_id"] == action_id for e in reference["effect_events"]):
        unknown.append("Suppressed reference contains the selected action")
    residuals, conflicts, preservation_errors = [], [], []
    for table, fields in BUSINESS_FIELDS.items():
        originals = {r["id"]: r for r in before[table]}
        results = {r["id"]: r for r in after[table]}
        refs = {r["id"]: r for r in reference[table]}
        if set(originals) != set(results) or set(originals) != set(refs):
            preservation_errors.append(f"{table}: record set changed or reference incomplete")
        for record_id, original in originals.items():
            if record_id not in results or record_id not in refs:
                continue
            result = results[record_id]
            if table == "tasks" and result["project_id"] != original["project_id"]:
                preservation_errors.append(f"{table}.{record_id}.project_id")
            for field in fields:
                path = f"{table}.{record_id}.{field}"
                selected = field in affected.get((table, record_id), set())
                owned = selected and original["owners"].get(field) == action_id
                if selected and not owned:
                    conflicts.append(path)
                expected = refs[record_id][field] if owned else original[field]
                if result[field] != expected:
                    residuals.append(path)
                    if not owned:
                        preservation_errors.append(path)
                if not owned and (
                    result["owners"].get(field) != original["owners"].get(field)
                    or result["field_revisions"][field] != original["field_revisions"][field]
                ):
                    preservation_errors.append(f"{path}: independent ownership/revision changed")
                if (
                    owned
                    and original[field] != expected
                    and result[field] == expected
                    and (
                        result["field_revisions"][field] <= original["field_revisions"][field]
                        or result["version"] <= original["version"]
                    )
                ):
                    residuals.append(f"{path}: restoration lacks a new committed revision")
    # Owned derived records must disappear; independently owned records must survive exactly.
    for table in ("notifications", "escalations"):
        independent = [r for r in before[table] if r["action_id"] != action_id]
        independent_after = [r for r in after[table] if r["action_id"] != action_id]
        if independent != independent_after:
            preservation_errors.append(f"Independent {table} changed")
        if any(r["action_id"] == action_id for r in after[table]):
            residuals.append(f"Owned {table} remain")
    for table in ("task_comments", "task_dependencies"):
        if before[table] != after[table]:
            preservation_errors.append(f"Independent {table} changed")
    for table in ("effect_events", "notification_deliveries"):
        if not all(row in after[table] for row in before[table]):
            preservation_errors.append(f"Immutable {table} erased or modified")
    if any(
        j["action_id"] == action_id and j["status"] == "pending" for j in after["scheduled_jobs"]
    ):
        residuals.append("Selected-action work remains pending")
    witnesses, incomplete_proof = irreversible_witnesses(
        contract, before, after, reference, action_id
    )
    unknown.extend(incomplete_proof)
    success = evaluate_task(contract, after)["success"]
    if not reference_validated:
        classification = "UNKNOWN"
        unknown.append("Reference has not passed independent validity checks")
    elif witnesses:
        classification = "VERIFIED_UNRECOVERABLE"
    elif conflicts:
        classification = "CONFLICT"
    elif not requests_quiescent or unknown:
        classification = "UNKNOWN"
    elif not horizon_complete:
        classification = "CENSORED"
    elif residuals or preservation_errors or not success:
        classification = "PARTIAL"
    else:
        classification = "VERIFIED_RECOVERABLE"
    return {
        "oracle_version": "contract-recovery-v1",
        "contract_id": contract.contract_id,
        "classification": classification,
        "goal_preserved": success,
        "independent_edits_preserved": not preservation_errors,
        "residuals": residuals,
        "conflicts": conflicts,
        "preservation_errors": preservation_errors,
        "uncertainty_reasons": unknown,
        "irreversible_witnesses": witnesses,
        "first_verified_irreversible_time": (
            min(w["time"] for w in witnesses) - root_events[0]["logical_time"]
            if witnesses and len(root_events) == 1
            else None
        ),
        "irreversible_time_origin": "selected action logical time",
        "observation_horizon": contract.horizon,
        "horizon_complete": horizon_complete,
        "reference_validated": reference_validated,
        "requests_quiescent": requests_quiescent,
        "target_definition": "historical arrival is absorbing; current recovery class is separate",
    }
