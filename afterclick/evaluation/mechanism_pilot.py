"""Bounded, planted PostgreSQL mechanism validation; no model or payment network calls."""

import argparse
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from afterclick import domain
from afterclick.agent.modal_policy import atomic_json
from afterclick.benchmarks.mock_finance import FakeBank, ReceiptObserver
from afterclick.contracts.schema import load_contract
from afterclick.evaluation.finance_oracle import verify_finance
from afterclick.evaluation.pilot import EXPECTED as NOTICE_EXPECTED
from afterclick.evaluation.pilot import run_case as notice_case
from afterclick.evaluation.recovery_reference import verify_recovery
from afterclick.infrastructure.db import Database, digest
from afterclick.recovery.conditional import compensate_owned_workflow
from afterclick.replay.demo import canonical, source_manifest

FEE_EXPECTED = {
    "early": "VERIFIED_RECOVERABLE",
    "late_refund": "VERIFIED_UNRECOVERABLE",
    "lost_ack": "VERIFIED_UNRECOVERABLE",
    "independent_edit": "VERIFIED_RECOVERABLE",
    "conflict": "CONFLICT",
    "unknown": "UNKNOWN",
    "censored": "CENSORED",
    "null": "NO_SELECTED_EFFECT",
}


class World:
    def __init__(self, seed, receipt_delay=0):
        self.dbs = []
        self.source = Database("ac_p2_source_" + uuid4().hex)
        self.dbs.append(self.source)
        self.source.migrate()
        receiver = Database("ac_p2_receipt_" + uuid4().hex)
        self.dbs.append(receiver)
        bank = Database("ac_p2_bank_" + uuid4().hex)
        self.dbs.append(bank)
        self.bank = FakeBank(bank, ReceiptObserver(receiver, delay=receipt_delay))
        domain.seed(self.source, seed=seed, worker_delay=100, delivery_delay=10000)
        domain.patch_task(
            self.source,
            "TASK-42",
            {"description": "Document API v2 integration."},
            1,
            "goal",
            "goal",
        )
        self.bank.consume_committed_events(domain.snapshot(self.source))

    def close(self):
        for db in reversed(self.dbs):
            db.drop_experiment()


def human(world, mode):
    if mode not in {"independent_edit", "conflict"}:
        return
    current = next(t for t in domain.snapshot(world.source)["tasks"] if t["id"] == "TASK-42")
    changes = (
        {"description": "API v2 independent human addition"}
        if mode == "independent_edit"
        else {"reviewed": True}
    )
    domain.patch_task(
        world.source, "TASK-42", changes, current["version"], "human", "human", "human"
    )
    world.bank.consume_committed_events(domain.snapshot(world.source))
    if mode == "independent_edit":
        world.bank.independent_credit(4)


def fee_case(contract, mode):
    worlds = []
    try:
        refs = []
        prefixes = []
        for _ in range(2):
            w = World(contract.seed, receipt_delay=300 if mode == "unknown" else 0)
            worlds.append(w)
            prefixes.append(
                {
                    "source": digest(canonical(domain.snapshot(w.source))),
                    "sink": digest(w.bank.snapshot()),
                }
            )
            domain.advance(w.source, 50)
            w.bank.advance(50)
            human(w, mode)
            domain.advance(w.source, contract.horizon)
            w.bank.advance(contract.horizon)
            refs.append({"source": domain.snapshot(w.source), "sink": w.bank.snapshot()})
        w = World(contract.seed, receipt_delay=300 if mode == "unknown" else 0)
        worlds.append(w)
        prefixes.append(
            {
                "source": digest(canonical(domain.snapshot(w.source))),
                "sink": digest(w.bank.snapshot()),
            }
        )
        valid = (
            prefixes[0] == prefixes[1] == prefixes[2]
            and digest(canonical(refs[0]["source"])) == digest(canonical(refs[1]["source"]))
            and digest(refs[0]["sink"]) == digest(refs[1]["sink"])
        )
        reference = refs[0]
        if mode != "null":
            current = next(t for t in domain.snapshot(w.source)["tasks"] if t["id"] == "TASK-42")
            domain.patch_task(
                w.source, "TASK-42", {"reviewed": True}, current["version"], "selected", "selected"
            )
            w.bank.consume_committed_events(domain.snapshot(w.source))
        late = mode in {"late_refund", "lost_ack", "unknown"}
        at = 150 if late else 50
        domain.advance(w.source, at)
        w.bank.advance(at, drop_ack=mode == "lost_ack")
        human(w, mode)
        source_before = domain.snapshot(w.source)
        sink_before = w.bank.snapshot()
        recovery = {"status": "NOT_NEEDED"}
        if mode != "null":
            recovery = compensate_owned_workflow(w.source, "selected")
            if not w.bank.cancel_pending("selected"):
                w.bank.refund_principal("selected")
        complete = mode != "censored"
        if complete:
            domain.advance(w.source, contract.horizon)
            w.bank.advance(contract.horizon)
        source_after = domain.snapshot(w.source)
        sink_after = w.bank.snapshot()
        source_certificate = verify_recovery(
            contract,
            source_before,
            source_after,
            reference["source"],
            "selected",
            reference_validated=valid,
            requests_quiescent=True,
            horizon_complete=complete,
        )
        null_equal = (
            (
                digest(canonical(source_after)) == digest(canonical(reference["source"]))
                and digest(sink_after) == digest(reference["sink"])
            )
            if mode == "null"
            else None
        )
        if mode == "null" and not null_equal:
            valid = False
        certificate = verify_finance(
            sink_before,
            sink_after,
            reference["sink"],
            source_before["effect_events"],
            source_certificate,
            reference_validated=valid,
            horizon_complete=complete,
            null=mode == "null",
        )
        followup = None
        if mode == "unknown":
            w.bank.advance(450)
            later = w.bank.snapshot()
            followup = dict(
                observation_time=450,
                sink=later,
                primary_label_unchanged=True,
                certificate=verify_finance(
                    sink_before,
                    later,
                    reference["sink"],
                    source_before["effect_events"],
                    source_certificate,
                    reference_validated=valid,
                    horizon_complete=True,
                ),
            )
        return dict(
            mechanism="mock_payment_fee",
            mode=mode,
            seed=contract.seed,
            selected_action_planted=mode != "null",
            organic_action=False,
            data_mode="planted backend real PostgreSQL, separate fake provider/observer schemas",
            contract=contract.model_dump(),
            reference=reference,
            reference_placebo=refs[1],
            reference_certificate=dict(
                valid=valid,
                checkpoint_hashes=prefixes,
                method="3freshsource/provider/observer prefixes and2suppressed continuations",
            ),
            source_before=source_before,
            source_after=source_after,
            sink_before=sink_before,
            sink_after=sink_after,
            source_certificate=source_certificate,
            recovery_attempt=recovery,
            external_api_calls=w.bank.calls,
            certificate=certificate,
            null_outcomes_equal=null_equal,
            receipt_arrival_delay=300 if mode == "unknown" else 0,
            receipt_followup=followup,
            recovery_time=at,
            observation_horizon=300 if complete else at,
            expected_class=FEE_EXPECTED[mode],
            passed=valid and certificate["classification"] == FEE_EXPECTED[mode],
        )
    finally:
        for w in reversed(worlds):
            w.close()


def run(run_dir):
    run_dir = Path(run_dir)
    protocol = json.loads((run_dir / "protocol.json").read_text())
    if (run_dir / "raw/started.json").exists():
        raise ValueError("Use a new registered directory; never overwrite an attempted pilot")
    if protocol.get("cost_cap_usd") != 0 or protocol.get("attempt_budget") != 48:
        raise ValueError("Registered zero-cost bounded protocol required")
    started = time.monotonic()
    atomic_json(
        run_dir / "raw/started.json",
        dict(utc=datetime.now(timezone.utc).isoformat(), source_manifest=source_manifest()),
    )
    results = []
    errors = []
    try:
        base = load_contract("fixtures/tasks/review-readiness-v2.json")
        for mechanism, expected in [
            ("notification", NOTICE_EXPECTED),
            ("mock_payment_fee", FEE_EXPECTED),
        ]:
            for seed in protocol["seeds"]:
                contract = base.model_copy(update={"seed": seed})
                for mode in expected:
                    if time.monotonic() - started > 600 or len(results) + len(errors) >= 48:
                        raise TimeoutError("Bounded local case/time budget exhausted")
                    case_id = f"{mechanism}-{seed}-{mode}"
                    try:
                        if mechanism == "notification":
                            db = Database("ac_p2_notice_" + uuid4().hex)
                            try:
                                db.migrate()
                                case = notice_case(db, contract, mode)
                            finally:
                                db.drop_experiment()
                            case.update(mechanism=mechanism, seed=seed)
                        else:
                            case = fee_case(contract, mode)
                        path = run_dir / "raw" / (case_id + ".json")
                        atomic_json(path, case)
                        row = dict(
                            schema_version=1,
                            case_id=case_id,
                            mechanism=mechanism,
                            seed=seed,
                            mode=mode,
                            classification=case["certificate"]["classification"],
                            passed=case["passed"],
                            raw_reference=str(path.relative_to(run_dir)),
                            lineage_group=f"{mechanism}-{seed}",
                            partition="development",
                            model_calls=0,
                            cost_usd=0,
                        )
                        results.append(row)
                        with (run_dir / "oracle_certificates.jsonl").open("a") as f:
                            f.write(
                                json.dumps(dict(case_id=case_id, certificate=case["certificate"]))
                                + "\n"
                            )
                            f.flush()
                        print(
                            case_id,
                            row["classification"],
                            "PASS" if row["passed"] else "FAIL",
                            flush=True,
                        )
                    except BaseException as exc:
                        row = dict(
                            schema_version=1,
                            case_id=case_id,
                            mechanism=mechanism,
                            seed=seed,
                            status="invalid",
                            error_type=type(exc).__name__,
                            traceback=traceback.format_exc(),
                        )
                        errors.append(row)
                        atomic_json(run_dir / "raw" / (case_id + "-error.json"), row)
                    with (run_dir / "trials.jsonl").open("a") as f:
                        f.write(json.dumps(row) + "\n")
                        f.flush()
                    if errors or not row.get("passed"):
                        raise RuntimeError(
                            "First local oracle/reconstruction failure; raw evidence retained"
                        )
    except BaseException:
        (run_dir / "raw/interrupted.txt").write_text(traceback.format_exc())
    unknown = sum(r["classification"] == "UNKNOWN" for r in results)
    censored = sum(r["classification"] == "CENSORED" for r in results)
    metrics = dict(
        schema_version=1,
        attempted=len(results) + len(errors),
        execution_valid=len(results),
        valid=len(results) - unknown - censored,
        invalid=len(errors),
        unknown=unknown,
        censored=censored,
        expected_cases=48,
        unattempted=48 - len(results) - len(errors),
        passed=not errors and len(results) == 48 and all(r["passed"] for r in results),
        mechanism_classes=2,
        model_calls=0,
        cost_usd=0,
        elapsed_seconds=round(time.monotonic() - started, 3),
        scope="enumerated backend fixtures; no population interval or live agent claim",
    )
    atomic_json(run_dir / "metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    report = run(parser.parse_args().run)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
