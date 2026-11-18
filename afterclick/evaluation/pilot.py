"""Measured PostgreSQL oracle-validation pilot, not an adaptive browser benchmark.

All cases are explicitly planted. False-success cases inject a *claim*, not fabricated
state/effects. The independent verifier does not accept planner claims as input.
"""

import argparse
import json
from pathlib import Path
from uuid import uuid4

from afterclick import domain
from afterclick.contracts.schema import load_contract
from afterclick.evaluation.effect_oracle import evaluate_effects
from afterclick.evaluation.recovery_reference import verify_recovery
from afterclick.infrastructure.db import Database, digest
from afterclick.recovery.conditional import compensate_owned_workflow
from afterclick.replay.demo import canonical, source_manifest

CONTRACT_PATHS = [
    "fixtures/tasks/review-readiness-v2.json",
    "fixtures/tasks/priority-escalation-v1.json",
    "fixtures/tasks/status-summary-v1.json",
]
EXPECTED = {
    "early": "VERIFIED_RECOVERABLE",
    "late": "VERIFIED_UNRECOVERABLE",
    "conflict": "CONFLICT",
    "harmless": "VERIFIED_RECOVERABLE",
    "unknown": "UNKNOWN",
    "censored": "CENSORED",
    "false_success": "PARTIAL",
    "preservation": "VERIFIED_RECOVERABLE",
}


def prepare(db, contract, *, delivery_delay=100):
    checkpoints, outcomes = [], []
    for index in range(3):
        domain.reset_experiment(db, contract.seed, worker_delay=100, delivery_delay=delivery_delay)
        goal = contract.goals[0]
        domain.patch_task(
            db, goal.record_id, {goal.field: "Document API v2 integration."}, 1, "goal", "goal"
        )
        checkpoints.append(domain.snapshot(db))
        if index < 2:
            domain.advance(db, contract.horizon)
            outcomes.append(domain.snapshot(db))
    valid = all(digest(canonical(c)) == digest(canonical(checkpoints[0])) for c in checkpoints)
    valid = valid and digest(canonical(outcomes[0])) == digest(canonical(outcomes[1]))
    return outcomes[0], {
        "valid": valid,
        "checkpoint_hashes": [digest(canonical(c)) for c in checkpoints],
        "suppressed_placebo_hashes": [digest(canonical(o)) for o in outcomes],
        "method": "three reset/prefix reconstructions and two suppressed continuations",
        "backend_only": True,
        "delivery_delay": delivery_delay,
        "worker_delay": 100,
    }


def run_case(db, contract, mode):
    reference, validity = prepare(
        db, contract, delivery_delay=1000 if mode == "false_success" else 100
    )
    field = contract.selected_action.field
    root_id = contract.selected_action.record_id
    current = next(t for t in domain.snapshot(db)["tasks"] if t["id"] == root_id)
    value = (
        current[field]
        if mode == "harmless"
        else {"reviewed": True, "priority": "Critical", "status": "Done"}[field]
    )
    domain.patch_task(db, root_id, {field: value}, current["version"], "selected", "selected")
    time = 200 if mode == "late" else 150
    domain.advance(db, time)
    if mode in {"conflict", "preservation"}:
        current = next(t for t in domain.snapshot(db)["tasks"] if t["id"] == root_id)
        changes = {field: value} if mode == "conflict" else {"description": "API v2 human addition"}
        domain.patch_task(db, root_id, changes, current["version"], "human", "human", "human")
    before = domain.snapshot(db)
    attempt = {"status": "NOT_ATTEMPTED"}
    if mode not in {"harmless", "false_success"}:
        attempt = compensate_owned_workflow(db, "selected")
    complete = mode not in {"censored", "conflict"}
    if complete:
        domain.advance(db, contract.horizon)
    after = domain.snapshot(db)
    certificate = verify_recovery(
        contract,
        before,
        after,
        reference,
        "selected",
        reference_validated=validity["valid"],
        requests_quiescent=mode != "unknown",
        horizon_complete=complete,
    )
    return {
        "contract": contract.model_dump(),
        "mode": mode,
        "fixture_type": "planted backend case",
        "reference": reference,
        "reference_certificate": validity,
        "before": before,
        "after": after,
        "recovery_attempt": attempt,
        "injected_false_planner_claim": "VERIFIED_RECOVERABLE" if mode == "false_success" else None,
        "certificate": certificate,
        "expected_class": EXPECTED[mode],
        "effects": evaluate_effects(contract, after),
        "passed": certificate["classification"] == EXPECTED[mode],
    }


def run(output):
    run_id = uuid4().hex
    directory = output / run_id
    directory.mkdir(parents=True)
    report = {
        "run_id": run_id,
        "data_mode": "measured planted PostgreSQL oracle-validation cases",
        "manifest": source_manifest(),
        "cases": [],
        "errors": [],
    }
    for path in CONTRACT_PATHS:
        contract = load_contract(path)
        for mode in EXPECTED:
            db = Database("ac_pilot_" + uuid4().hex)
            try:
                db.migrate()
                case = run_case(db, contract, mode)
                report["cases"].append(case)
                print(
                    f"{contract.workflow_family}/{mode}: {case['certificate']['classification']}",
                    flush=True,
                )
                (directory / f"{contract.workflow_family}-{mode}.json").write_text(
                    json.dumps(case, indent=2)
                )
            except Exception as exc:
                import traceback

                report["errors"].append(
                    {
                        "contract": contract.contract_id,
                        "mode": mode,
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                )
            finally:
                db.drop_experiment()
    report["passed"] = (
        not report["errors"]
        and len(report["cases"]) == 24
        and all(c["passed"] for c in report["cases"])
    )
    (directory / "report.json").write_text(json.dumps(report, indent=2))
    (output / "report.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/oracle-pilot"))
    report = run(parser.parse_args().output)
    if not report["passed"]:
        raise SystemExit("Oracle pilot failed; all cases/errors retained in report.json")
