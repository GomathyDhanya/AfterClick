"""Actual PostgreSQL re-execution of search witnesses using existing independent oracles."""

from uuid import uuid4

from afterclick import domain
from afterclick.contracts.schema import load_contract
from afterclick.evaluation.capability_oracle import verify
from afterclick.evaluation.capability_pilot import World as CapabilityWorld
from afterclick.evaluation.finance_oracle import verify_finance
from afterclick.evaluation.mechanism_pilot import World as FeeWorld
from afterclick.evaluation.pilot import prepare
from afterclick.evaluation.recovery_reference import verify_recovery
from afterclick.infrastructure.db import Database, digest
from afterclick.recovery.conditional import compensate_owned_workflow
from afterclick.replay.demo import canonical


def query(mechanism, at, seed=7):
    contract = load_contract("fixtures/tasks/review-readiness-v2.json").model_copy(
        update={"seed": seed, "horizon": max(300, at)}
    )
    if mechanism == "notification":
        db = Database("ac_search_notice_" + uuid4().hex)
        try:
            db.migrate()
            reference, validity = prepare(db, contract)
            current = next(t for t in domain.snapshot(db)["tasks"] if t["id"] == "TASK-42")
            domain.patch_task(
                db, "TASK-42", {"reviewed": True}, current["version"], "selected", "selected"
            )
            domain.advance(db, at)
            before = domain.snapshot(db)
            compensate_owned_workflow(db, "selected")
            domain.advance(db, contract.horizon)
            after = domain.snapshot(db)
            cert = verify_recovery(
                contract,
                before,
                after,
                reference,
                "selected",
                reference_validated=validity["valid"],
                requests_quiescent=True,
                horizon_complete=True,
            )
            return dict(
                certificate=cert,
                before=before,
                after=after,
                reference=reference,
                reference_validity=validity,
            )
        finally:
            db.drop_experiment()
    worlds = []
    try:
        cls = FeeWorld if mechanism == "mock_payment_fee" else CapabilityWorld
        for _ in range(3):
            worlds.append(cls(seed) if cls is FeeWorld else cls(seed, mechanism))
        prefixes = []
        outcomes = []
        before = None
        source_cert = None
        for index, w in enumerate(worlds):
            provider = w.bank if cls is FeeWorld else w.service
            source = domain.snapshot(w.source)
            sink = provider.snapshot()
            prefixes.append(dict(source=digest(canonical(source)), sink=digest(sink)))
            if index == 2:
                current = next(t for t in source["tasks"] if t["id"] == "TASK-42")
                domain.patch_task(
                    w.source,
                    "TASK-42",
                    {"reviewed": True},
                    current["version"],
                    "selected",
                    "selected",
                )
                source = domain.snapshot(w.source)
                if cls is FeeWorld:
                    provider.consume_committed_events(source)
                else:
                    provider.consume(source)
            domain.advance(w.source, at)
            provider.advance(at)
            if index == 2:
                before = dict(source=domain.snapshot(w.source), sink=provider.snapshot())
                compensate_owned_workflow(w.source, "selected")
                if cls is FeeWorld:
                    if not provider.cancel_pending("selected"):
                        provider.refund_principal("selected")
                else:
                    provider.recover()
            domain.advance(w.source, contract.horizon)
            provider.advance(contract.horizon)
            outcomes.append(dict(source=domain.snapshot(w.source), sink=provider.snapshot()))
        reference, placebo, after = outcomes
        valid = (
            prefixes[0] == prefixes[1] == prefixes[2]
            and digest(canonical(reference["source"])) == digest(canonical(placebo["source"]))
            and digest(reference["sink"]) == digest(placebo["sink"])
        )
        source_cert = verify_recovery(
            contract,
            before["source"],
            after["source"],
            reference["source"],
            "selected",
            reference_validated=valid,
            requests_quiescent=True,
            horizon_complete=True,
        )
        if cls is FeeWorld:
            cert = verify_finance(
                before["sink"],
                after["sink"],
                reference["sink"],
                before["source"]["effect_events"],
                source_cert,
                reference_validated=valid,
                horizon_complete=True,
            )
        else:
            cert = verify(
                mechanism,
                before["sink"],
                after["sink"],
                reference["sink"],
                before["source"]["effect_events"],
                prefix_valid=valid,
                complete=True,
            )
        return dict(
            certificate=cert,
            source_certificate=source_cert,
            before=before,
            after=after,
            reference=reference,
            reference_placebo=placebo,
            prefixes=prefixes,
            reference_valid=valid,
        )
    finally:
        for w in reversed(worlds):
            w.close()
