"""Exhaustive finite closure and saved-state projection checks, offline and bounded."""

import argparse
import itertools
import json
from dataclasses import asdict
from pathlib import Path

from afterclick.agent.modal_policy import atomic_json
from afterclick.research.recoverability import State, strategy


def project(row, raw):
    mechanism = row["mechanism"]
    source = raw.get("source_after", raw.get("after"))
    if "source" in source:
        source = source["source"]
    reviewed = next(t["reviewed"] for t in source["tasks"] if t["id"] == "TASK-42")
    foreign = row["classification"] == "CONFLICT"
    if mechanism == "notification":
        return State(
            owned_source=reviewed,
            pending=bool(source["notifications"]),
            knowledge_observed=bool(source["notification_deliveries"]),
            foreign_owner=foreign,
        )
    if mechanism == "mock_payment_fee":
        sink = raw["sink_after"]
        accounts = {a["name"]: a["units"] for a in sink["fake_accounts"]}
        return State(
            owned_source=reviewed,
            pending=any(i["status"] == "pending" for i in sink["fake_intents"]),
            principal=accounts["merchant"] > 0,
            fee_burned=accounts["fee_burn"] > 0,
            foreign_owner=foreign,
        )
    state = raw["after"]["sink"]["state"]
    return State(
        owned_source=reviewed,
        pending=state["parent"] or state["lease"],
        child_live=state["child"],
        deadline_missed=state["missed"],
        foreign_owner=foreign,
    )


def run(directory):
    if (directory / "raw/started.json").exists():
        raise ValueError("Fresh registered directory required")
    atomic_json(directory / "raw/started.json", dict(started=True))
    p = json.loads((directory / "protocol.json").read_text())
    rows = []
    known = 0
    partial_feasible = 0
    errors = []
    for source_id in p["inputs"]:
        source = directory.parent / source_id
        for text in (source / "trials.jsonl").read_text().splitlines():
            row = json.loads(text)
            if "raw_reference" not in row:
                continue
            raw = json.loads((source / row["raw_reference"]).read_text())
            state = project(row, raw)
            witness = strategy(state)
            label = row["classification"]
            expected = {
                "VERIFIED_RECOVERABLE": True,
                "VERIFIED_UNRECOVERABLE": False,
                "NO_SELECTED_EFFECT": True,
            }.get(label)
            if expected is not None:
                known += 1
                if (witness is not None) != expected:
                    errors.append(row["case_id"])
            if label == "PARTIAL" and witness is not None:
                partial_feasible += 1
            result = dict(
                schema_version=1,
                source_run=source_id,
                case_id=row["case_id"],
                oracle_class=label,
                abstract_state=asdict(state),
                admissible_strategy=witness,
                physical_feasible=witness is not None,
                epistemic_label_retained=True,
                known_assertion_compared=expected is not None,
            )
            with (directory / "trials.jsonl").open("a") as f:
                f.write(json.dumps(result) + "\n")
            rows.append(result)
    exhaustive = []
    for bits in itertools.product([False, True], repeat=8):
        state = State(*bits)
        witness = strategy(state)
        expected = not any(bits[3:7]) and not (bits[7] and (bits[0] or bits[1]))
        assert (witness is not None) == expected
        exhaustive.append(dict(state=asdict(state), strategy=witness))
    atomic_json(directory / "raw/exhaustive-states.json", dict(states=exhaustive))
    metrics = dict(
        schema_version=1,
        attempted=len(rows),
        known_oracle_assertions_compared=known,
        known_disagreements=len(errors),
        partial_implementation_failures_with_feasible_strategy=partial_feasible,
        exhaustive_abstract_states=len(exhaustive),
        passed=not errors and len(rows) == 102,
        model_calls=0,
        cost_usd=0,
        unclassified_epistemic_or_conflict_cases=len(rows) - known,
    )
    atomic_json(directory / "metrics.json", metrics)
    print(json.dumps(metrics))
    if errors:
        raise AssertionError(errors)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    run(p.parse_args().run)


if __name__ == "__main__":
    main()
