"""A fake financial provider and separate durable receipt observer.

All amounts are synthetic integer units. No network/payment provider is used.
Recovery capabilities are cancel-pending and refund-principal; captured fees are
absorbing under this explicitly limited simulation API. This is not a claim
about real financial law or every physically possible compensation strategy.
"""

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    delete,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB

from afterclick.infrastructure.db import digest

bank_metadata = MetaData()
clock = Table(
    "fake_bank_clock",
    bank_metadata,
    Column("id", Integer, primary_key=True),
    Column("logical_time", Integer, nullable=False),
    Column("initial_wallet", Integer, nullable=False),
)
accounts = Table(
    "fake_accounts",
    bank_metadata,
    Column("name", String, primary_key=True),
    Column("units", Integer, nullable=False),
)
intents = Table(
    "fake_intents",
    bank_metadata,
    Column("root", String, primary_key=True),
    Column("source_event_hash", String, nullable=False),
    Column("status", String, nullable=False),
    Column("due", Integer, nullable=False),
    Column("principal", Integer, nullable=False),
    Column("fee", Integer, nullable=False),
)
ledger = Table(
    "fake_ledger",
    bank_metadata,
    Column("id", Integer, primary_key=True),
    Column("root", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("logical_time", Integer, nullable=False),
    Column("postings", JSONB, nullable=False),
)
receipt_metadata = MetaData()
receipts = Table(
    "fake_observer_receipts",
    receipt_metadata,
    Column("operation", String, primary_key=True),
    Column("root", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("ledger_id", Integer, nullable=False),
    Column("event_time", Integer, nullable=False),
    Column("arrival_time", Integer, nullable=False),
    Column("postings_hash", String, nullable=False),
)
pending_receipts = Table(
    "fake_receipt_queue",
    receipt_metadata,
    Column("operation", String, primary_key=True),
    Column("due", Integer, nullable=False),
    Column("event", JSONB, nullable=False),
)
receipt_clock = Table(
    "fake_receipt_clock",
    receipt_metadata,
    Column("id", Integer, primary_key=True),
    Column("logical_time", Integer, nullable=False),
    Column("delay", Integer, nullable=False),
)


def install(db, metadata):
    if not db.schema.startswith("ac_"):
        raise ValueError("Fake providers require isolated ac_* schemas")
    with db.engine.begin() as c:
        c.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{db.schema}"'))
        metadata.create_all(c)


class LostAcknowledgment(RuntimeError):
    pass


class ReceiptObserver:
    def __init__(self, db, delay=0):
        self.db = db
        install(db, receipt_metadata)
        if type(delay) is not int or delay < 0:
            raise ValueError("Nonnegative receipt delay required")
        with db.transaction() as c:
            if not c.execute(select(receipt_clock)).first():
                c.execute(insert(receipt_clock).values(id=1, logical_time=0, delay=delay))

    def receive(self, event):
        operation = f"{event['kind']}:{event['root']}:{event['id']}"
        with self.db.transaction() as c:
            if (
                c.execute(select(receipts).where(receipts.c.operation == operation)).first()
                or c.execute(
                    select(pending_receipts).where(pending_receipts.c.operation == operation)
                ).first()
            ):
                return
            delay = c.execute(select(receipt_clock.c.delay)).scalar_one()
            c.execute(
                insert(pending_receipts).values(
                    operation=operation, due=event["logical_time"] + delay, event=event
                )
            )
        self.advance(event["logical_time"])

    def advance(self, target):
        with self.db.transaction() as c:
            now = c.execute(select(receipt_clock.c.logical_time)).scalar_one()
            if target < now:
                raise ValueError("Observer time cannot move backwards")
            due = [
                dict(r)
                for r in c.execute(
                    select(pending_receipts)
                    .where(pending_receipts.c.due <= target)
                    .order_by(pending_receipts.c.due, pending_receipts.c.operation)
                ).mappings()
            ]
            for item in due:
                event = item["event"]
                c.execute(
                    insert(receipts).values(
                        operation=item["operation"],
                        root=event["root"],
                        kind=event["kind"],
                        ledger_id=event["id"],
                        event_time=event["logical_time"],
                        arrival_time=item["due"],
                        postings_hash=digest(event["postings"]),
                    )
                )
                c.execute(
                    delete(pending_receipts).where(
                        pending_receipts.c.operation == item["operation"]
                    )
                )
            c.execute(update(receipt_clock).values(logical_time=target))

    def snapshot(self):
        with self.db.engine.begin() as c:
            return [
                dict(r)
                for r in c.execute(select(receipts).order_by(receipts.c.operation)).mappings()
            ]

    def pending_state(self):
        with self.db.engine.begin() as c:
            return {
                "clock": dict(c.execute(select(receipt_clock)).mappings().one()),
                "pending": [
                    dict(r)
                    for r in c.execute(
                        select(pending_receipts).order_by(pending_receipts.c.operation)
                    ).mappings()
                ],
            }


class FakeBank:
    def __init__(self, db, observer):
        self.db, self.observer = db, observer
        self.calls = []
        install(db, bank_metadata)
        with db.transaction() as c:
            if not c.execute(select(clock)).first():
                c.execute(insert(clock).values(id=1, logical_time=0, initial_wallet=100))
                c.execute(
                    insert(accounts),
                    [
                        {"name": n, "units": 100 if n == "wallet" else 0}
                        for n in ("wallet", "merchant", "fee_burn", "external")
                    ],
                )

    def consume_committed_events(self, state):
        """React to committed values only, without access to branch/mode/oracle labels."""
        for event in state["effect_events"]:
            if (
                event["kind"] != "task.updated"
                or event["resource"] != "TASK-42"
                or (event.get("after") or {}).get("reviewed") is not True
                or (event.get("before") or {}).get("reviewed") is not False
            ):
                continue
            root = event["action_id"]
            with self.db.transaction() as c:
                if c.execute(select(intents).where(intents.c.root == root)).first():
                    continue
                c.execute(
                    insert(intents).values(
                        root=root,
                        source_event_hash=digest(event),
                        status="pending",
                        due=event["logical_time"] + 100,
                        principal=10,
                        fee=1,
                    )
                )
            self.calls.append({"method": "authorize", "root": root, "response": "pending"})

    def _post(self, c, root, kind, now, postings):
        if sum(postings.values()) != 0:
            raise ValueError("Unbalanced synthetic transaction")
        previous = c.execute(select(clock.c.logical_time)).scalar_one()
        if now < previous:
            raise ValueError("Financial commits cannot precede the provider clock")
        c.execute(update(clock).values(logical_time=now))
        for name, delta in postings.items():
            c.execute(
                update(accounts)
                .where(accounts.c.name == name)
                .values(units=accounts.c.units + delta)
            )
        key = c.execute(
            insert(ledger)
            .values(root=root, kind=kind, logical_time=now, postings=postings)
            .returning(ledger.c.id)
        ).scalar_one()
        return dict(id=key, root=root, kind=kind, logical_time=now, postings=postings)

    def capture(self, root, at, *, drop_ack=False):
        event = None
        with self.db.transaction() as c:
            item = dict(c.execute(select(intents).where(intents.c.root == root)).mappings().one())
            if item["status"] in {"captured", "refunded"}:
                return {"status": "duplicate_no_new_effect"}
            if item["status"] != "pending" or at < item["due"]:
                raise ValueError("Capture is not enabled")
            wallet = c.execute(
                select(accounts.c.units).where(accounts.c.name == "wallet")
            ).scalar_one()
            if wallet < item["principal"] + item["fee"]:
                raise ValueError("Insufficient fake units")
            event = self._post(
                c,
                root,
                "capture",
                at,
                dict(
                    wallet=-item["principal"] - item["fee"],
                    merchant=item["principal"],
                    fee_burn=item["fee"],
                ),
            )
            c.execute(update(intents).where(intents.c.root == root).values(status="captured"))
        # Separate transaction/schema: source rollback and provider refund cannot erase observation.
        self.observer.receive(event)
        self.calls.append(
            {"method": "capture", "root": root, "response": "lost_ack" if drop_ack else "committed"}
        )
        if drop_ack:
            raise LostAcknowledgment("Fake response lost after commit; no automatic retry")
        return {"status": "committed"}

    def advance(self, target, *, drop_ack=False):
        with self.db.transaction() as c:
            now = c.execute(select(clock.c.logical_time)).scalar_one()
            if target < now:
                raise ValueError("External logical time cannot move backwards")
            pending = [
                dict(x)
                for x in c.execute(
                    select(intents)
                    .where(intents.c.status == "pending", intents.c.due <= target)
                    .order_by(intents.c.due, intents.c.root)
                ).mappings()
            ]
        for item in pending:
            try:
                self.capture(item["root"], item["due"], drop_ack=drop_ack)
            except LostAcknowledgment:
                pass
        with self.db.transaction() as c:
            c.execute(update(clock).values(logical_time=target))
        self.observer.advance(target)

    def cancel_pending(self, root):
        with self.db.transaction() as c:
            changed = c.execute(
                update(intents)
                .where(intents.c.root == root, intents.c.status == "pending")
                .values(status="cancelled")
            ).rowcount
        self.calls.append({"method": "cancel_pending", "root": root, "cancelled": bool(changed)})
        return bool(changed)

    def refund_principal(self, root):
        event = None
        with self.db.transaction() as c:
            item = c.execute(select(intents).where(intents.c.root == root)).mappings().one()
            if item["status"] != "captured":
                return False
            now = c.execute(select(clock.c.logical_time)).scalar_one()
            event = self._post(
                c, root, "refund", now, dict(wallet=item["principal"], merchant=-item["principal"])
            )
            c.execute(update(intents).where(intents.c.root == root).values(status="refunded"))
        self.observer.receive(event)
        self.calls.append({"method": "refund_principal", "root": root, "refunded": True})
        return True

    def independent_credit(self, units=4):
        if type(units) is not int or units <= 0:
            raise ValueError("Positive synthetic units required")
        with self.db.transaction() as c:
            now = c.execute(select(clock.c.logical_time)).scalar_one()
            event = self._post(
                c, "independent-credit", "credit", now, dict(wallet=units, external=-units)
            )
        self.observer.receive(event)
        self.calls.append({"method": "independent_credit", "units": units, "actor": "collaborator"})

    def snapshot(self):
        with self.db.engine.begin() as c:
            c.exec_driver_sql("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            result = {
                t.name: [dict(r) for r in c.execute(select(t).order_by(*t.primary_key)).mappings()]
                for t in (clock, accounts, intents, ledger)
            }
        result["observer_receipts"] = self.observer.snapshot()
        result["observer_state"] = self.observer.pending_state()
        return result
