"""Versioned same-execution metric comparison using preserved certified facts only."""

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from afterclick.recovery.oracle import BUSINESS_FIELDS
from afterclick.review.semantics import Evidence, score
from afterclick.tcope.driver import append
from research_ops.scripts.audit_recoverability import project


def derive(row, raw):
    label = row["classification"]
    cert = raw["certificate"]
    state = project(row, raw)
    source = raw.get("source_after", raw.get("after"))
    if "source" in source:
        source = source["source"]
    reference = raw["reference"].get("source", raw["reference"])
    byid = {x["id"]: x for x in reference["tasks"]}
    local = all(t[k] == byid[t["id"]][k] for t in source["tasks"] for k in BUSINESS_FIELDS)
    epistemic = label if label in {"UNKNOWN", "CENSORED"} else "KNOWN"
    history = cert.get("historical_forbidden_event")
    if history is None:
        if "irreversible_witnesses" in cert:
            history = bool(cert["irreversible_witnesses"])
        elif "historical_irreversible_count" in cert:
            history = cert["historical_irreversible_count"] > 0
        elif row["mechanism"] == "mock_payment_fee":
            # Immutable accounting loss is a direct recorded witness, not inferred from label.
            history = state.fee_burned
    independent = cert.get("independent_edits_preserved", cert.get("independent_edit_preserved"))
    goal = raw.get("legitimate_task", {}).get("success", cert.get("goal_preserved"))
    # Some finance certificates split source preservation from external accounting.
    if independent is None:
        independent = raw.get("source_certificate", {}).get("independent_edits_preserved")
    if goal is None:
        goal = raw.get("source_certificate", {}).get("goal_preserved")
    return score(
        Evidence(
            state,
            local,
            None if history is None else not history,
            goal,
            independent,
            prevention_witness=None,
            epistemic=epistemic,
        )
    )


def run(output):
    if (output / "raw/started.json").exists():
        raise ValueError("Fresh registered run required")
    atomic_json(output / "raw/started.json", dict(schema_version=2, mode="derived_saved_evidence"))
    rows = []
    for name in ["p2-20261123-distinct-mechanisms-v1", "p2-capability-diversity-v1"]:
        source = Path("artifacts/research_runs") / name
        for line in (source / "trials.jsonl").read_text().splitlines():
            row = json.loads(line)
            raw = json.loads((source / row["raw_reference"]).read_text())
            derived = derive(row, raw)
            result = dict(
                source_run=name,
                case_id=row["case_id"],
                mechanism=row["mechanism"],
                seed=row["seed"],
                mode=row["mode"],
                lineage_group=row["lineage_group"],
                historical_label=row["classification"],
                raw_reference=str(source / row["raw_reference"]),
                **derived,
            )
            append(output / "trials.jsonl", result)
            rows.append(result)
    predicates = [
        "local_rollback_success",
        "current_state_recoverable",
        "full_history_contract_recoverable",
        "prevention_feasible",
        "safe_task_complete",
    ]
    comparisons = {}
    for a, b in itertools.combinations(predicates, 2):
        available = [r for r in rows if r[a] is not None and r[b] is not None]
        comparisons[a + "__vs__" + b] = dict(
            eligible=len(available),
            disagree=sum(r[a] != r[b] for r in available),
            unresolved=len(rows) - len(available),
        )
    bymechanism = {
        m: {k: dict(Counter(str(r[k]) for r in rows if r["mechanism"] == m)) for k in predicates}
        for m in sorted({r["mechanism"] for r in rows})
    }
    metrics = dict(
        schema_version=2,
        attempted=len(rows),
        valid=len(rows),
        invalid=0,
        unknown=sum(r["measurement_status"] == "UNKNOWN" for r in rows),
        censored=sum(r["measurement_status"] == "CENSORED" for r in rows),
        counts_overlap_validity=True,
        model_calls=0,
        modal_usd=0,
        comparisons=comparisons,
        by_mechanism=bymechanism,
        current_yes_full_no=[
            r["case_id"]
            for r in rows
            if r["current_state_recoverable"] is True
            and r["full_history_contract_recoverable"] is False
        ],
        prevention_not_identifiable=len(rows),
        policy_ranking=(
            "Not estimable: backend modes are fixtures/procedures, not randomized agent policies"
        ),
    )
    atomic_json(output / "metrics.json", metrics)
    append(
        output / "oracle_certificates.jsonl",
        dict(
            kind="versioned_projection",
            historical_labels_unchanged=True,
            prevention_missing_not_inferred=True,
            old_projection="research_ops/scripts/audit_recoverability.py:project",
            limitation=(
                "Same bounded state projection; not a new independently validated abstraction"
            ),
        ),
    )
    print(json.dumps(metrics))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    run(p.parse_args().run)
