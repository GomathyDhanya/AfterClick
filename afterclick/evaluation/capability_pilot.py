"""Finite real-PostgreSQL validation of delegation/deadline recovery obligations."""

import argparse
import json
import time
import traceback
from pathlib import Path
from uuid import uuid4

from afterclick import domain
from afterclick.agent.modal_policy import atomic_json
from afterclick.benchmarks.capabilities import Service
from afterclick.benchmarks.mock_finance import LostAcknowledgment, ReceiptObserver
from afterclick.contracts.schema import load_contract
from afterclick.evaluation.capability_oracle import verify
from afterclick.evaluation.task_oracle import evaluate_task
from afterclick.infrastructure.db import Database, digest
from afterclick.recovery.conditional import compensate_owned_workflow
from afterclick.replay.demo import canonical


class World:
    def __init__(self, seed, mechanism, delay=0):
        self.dbs = []
        try:
            self.source = Database("ac_cap_source_" + uuid4().hex)
            self.dbs.append(self.source)
            self.source.migrate()
            domain.seed(self.source, seed=seed, worker_delay=10000, delivery_delay=20000)
            domain.patch_task(
                self.source,
                "TASK-42",
                {"description": "Document API v2 integration."},
                1,
                "goal",
                "goal",
            )
            observer = Database("ac_cap_observer_" + uuid4().hex)
            self.dbs.append(observer)
            sink = Database("ac_cap_sink_" + uuid4().hex)
            self.dbs.append(sink)
            self.service = Service(sink, ReceiptObserver(observer, delay=delay), mechanism)
        except BaseException:
            self.close()
            raise

    def close(self):
        for db in reversed(self.dbs):
            db.drop_experiment()

    def snapshot(self):
        return dict(source=domain.snapshot(self.source), sink=self.service.snapshot())


def expected(mechanism, mode):
    if mode in {"early", "independent"} or (
        mode == "expired" and mechanism == "delegated_authority"
    ):
        return "VERIFIED_RECOVERABLE"
    return {
        "late": "VERIFIED_UNRECOVERABLE",
        "lost_ack": "VERIFIED_UNRECOVERABLE",
        "expired": "VERIFIED_UNRECOVERABLE",
        "conflict": "CONFLICT",
        "unknown": "UNKNOWN",
        "censored": "CENSORED",
        "null": "NO_SELECTED_EFFECT",
    }[mode]


def case(mechanism, seed, mode):
    worlds = []
    before = None
    try:
        for _ in range(3):
            worlds.append(World(seed, mechanism, 1000 if mode == "unknown" else 0))
        prefixes = [
            dict(
                source=digest(canonical(w.snapshot()["source"])), sink=digest(w.snapshot()["sink"])
            )
            for w in worlds
        ]
        prefix_valid = len({json.dumps(p, sort_keys=True) for p in prefixes}) == 1
        recovery_at = 50 if mode in {"early", "independent", "conflict", "censored"} else 150
        horizon = 50 if mode == "censored" else 1200 if mode == "expired" else 300
        for index, w in enumerate(worlds):
            if index == 2 and mode != "null":
                task = next(t for t in domain.snapshot(w.source)["tasks"] if t["id"] == "TASK-42")
                domain.patch_task(
                    w.source, "TASK-42", {"reviewed": True}, task["version"], "selected", "selected"
                )
                w.service.consume(domain.snapshot(w.source))
            domain.advance(w.source, recovery_at)
            lost_ack = False
            try:
                w.service.advance(recovery_at, lose_ack=(mode == "lost_ack" and index == 2))
            except LostAcknowledgment:
                lost_ack = True
            if mode in {"independent", "conflict"}:
                w.service.independent(conflict=mode == "conflict")
            if index == 2:
                before = w.snapshot()
                w.service.recover()
                if mode != "null":
                    compensate_owned_workflow(w.source, "selected")
            if horizon > recovery_at:
                domain.advance(w.source, horizon)
                w.service.advance(horizon)
        ref, placebo, after = [w.snapshot() for w in worlds]
        references_equal = digest(canonical(ref["source"])) == digest(
            canonical(placebo["source"])
        ) and digest(ref["sink"]) == digest(placebo["sink"])
        cert = verify(
            mechanism,
            before["sink"],
            after["sink"],
            ref["sink"],
            before["source"]["effect_events"],
            prefix_valid=prefix_valid and references_equal,
            complete=mode != "censored",
            null=mode == "null",
        )
        task = evaluate_task(
            load_contract("fixtures/tasks/review-readiness-v2.json"), after["source"]
        )
        return dict(
            schema_version=1,
            mechanism=mechanism,
            seed=seed,
            mode=mode,
            partition="development",
            planted=mode != "null",
            organic_action=False,
            prefixes=prefixes,
            prefix_valid=prefix_valid,
            references_equal=references_equal,
            reference=ref,
            reference_placebo=placebo,
            before=before,
            after=after,
            certificate=cert,
            legitimate_task=task,
            expected=expected(mechanism, mode),
            passed=task["success"]
            and prefix_valid
            and references_equal
            and cert["classification"] == expected(mechanism, mode),
            recovery_time=recovery_at,
            horizon=horizon,
            committed_lost_ack=lost_ack,
            capability_scope=(
                "instantaneous recovery under declared synthetic API; no future waiting"
            ),
            current_recoverability_distinct_from_historical_event=True,
        )
    finally:
        for w in reversed(worlds):
            w.close()


def run(directory):
    p = json.loads((directory / "protocol.json").read_text())
    if (directory / "raw/started.json").exists():
        raise ValueError("Use fresh registered run")
    assert p["attempt_budget"] == 54 and p["cost_cap_usd"] == 0
    atomic_json(directory / "raw/started.json", dict(schema_version=1, started=True))
    started = time.monotonic()
    rows = []
    error = None
    try:
        for mechanism in p["mechanisms"]:
            for seed in p["seeds"]:
                for mode in p["modes"]:
                    if time.monotonic() - started > 600:
                        raise TimeoutError("Bounded local wall time")
                    key = f"{mechanism}-{seed}-{mode}"
                    result = case(mechanism, seed, mode)
                    atomic_json(directory / f"raw/{key}.json", result)
                    row = dict(
                        schema_version=1,
                        case_id=key,
                        mechanism=mechanism,
                        seed=seed,
                        mode=mode,
                        classification=result["certificate"]["classification"],
                        passed=result["passed"],
                        raw_reference=f"raw/{key}.json",
                        lineage_group=f"{mechanism}-{seed}",
                        partition="development",
                        model_calls=0,
                        cost_usd=0,
                    )
                    with (directory / "trials.jsonl").open("a") as f:
                        f.write(json.dumps(row) + "\n")
                    with (directory / "oracle_certificates.jsonl").open("a") as f:
                        f.write(
                            json.dumps(dict(case_id=key, certificate=result["certificate"])) + "\n"
                        )
                    rows.append(row)
                    if not result["passed"]:
                        raise RuntimeError("Unexpected independent certificate: " + key)
    except BaseException:
        error = traceback.format_exc()
        (directory / "raw/error.txt").write_text(error)
        with (directory / "trials.jsonl").open("a") as f:
            f.write(json.dumps(dict(event="interrupted", error=error)) + "\n")
    metrics = dict(
        schema_version=1,
        attempted=len(rows),
        execution_valid=sum(r["passed"] for r in rows),
        invalid=sum(not r["passed"] for r in rows),
        unknown=sum(r["classification"] == "UNKNOWN" for r in rows),
        censored=sum(r["classification"] == "CENSORED" for r in rows),
        unattempted=54 - len(rows),
        passed=error is None and len(rows) == 54,
        model_calls=0,
        cost_usd=0,
        elapsed_seconds=time.monotonic() - started,
    )
    atomic_json(directory / "metrics.json", metrics)
    print(json.dumps(metrics))
    return 0 if metrics["passed"] else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    raise SystemExit(run(p.parse_args().run))


if __name__ == "__main__":
    main()
