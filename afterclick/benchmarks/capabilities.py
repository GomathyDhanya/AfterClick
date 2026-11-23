"""Isolated synthetic delegation/deadline services, with separate durable receipts."""

from copy import deepcopy

from sqlalchemy import Column, Integer, MetaData, Table, insert, select, update
from sqlalchemy.dialects.postgresql import JSONB

from afterclick.benchmarks.mock_finance import LostAcknowledgment, install
from afterclick.infrastructure.db import digest

metadata = MetaData()
state_table = Table(
    "capability_state",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("clock", Integer, nullable=False),
    Column("data", JSONB, nullable=False),
)
events_table = Table(
    "capability_events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event", JSONB, nullable=False),
)


class Service:
    def __init__(self, db, observer, mechanism):
        if mechanism not in {"delegated_authority", "deadline_opportunity"}:
            raise ValueError("Unknown bounded mechanism")
        self.db, self.observer, self.mechanism = db, observer, mechanism
        install(db, metadata)
        with db.transaction() as c:
            c.execute(
                insert(state_table).values(
                    id=1,
                    clock=0,
                    data=dict(
                        mechanism=mechanism,
                        parent=False,
                        child=False,
                        lease=False,
                        cancelled=False,
                        source_hash=None,
                        legitimate_delivered=False,
                        missed=False,
                        blocked=False,
                        conflict=False,
                        note="initial",
                        access_observed=False,
                    ),
                )
            )

    def snapshot(self):
        with self.db.transaction() as c:
            row = c.execute(select(state_table)).mappings().one()
            events = [
                r["event"]
                for r in c.execute(select(events_table).order_by(events_table.c.id)).mappings()
            ]
        return dict(
            clock=row["clock"],
            state=row["data"],
            events=events,
            receipts=self.observer.snapshot(),
            observer=self.observer.pending_state(),
        )

    def _change(self, target, operation):
        posted = []
        with self.db.transaction() as c:
            row = c.execute(select(state_table).with_for_update()).mappings().one()
            if target < row["clock"]:
                raise ValueError("Clock cannot move backwards")
            state = deepcopy(row["data"])

            def emit(kind, at, payload):
                event = dict(
                    id=len(c.execute(select(events_table)).all()) + 1,
                    root="selected",
                    kind=kind,
                    logical_time=at,
                    postings=dict(payload, source_hash=state["source_hash"]),
                )
                c.execute(insert(events_table).values(id=event["id"], event=event))
                posted.append(event)

            operation(state, emit)
            c.execute(update(state_table).values(clock=target, data=state))
        # Provider commit precedes independent receiver commit; acknowledgment is separate.
        for event in posted:
            self.observer.receive(event)
        self.observer.advance(target)

    def consume(self, source):
        events = [
            e
            for e in source["effect_events"]
            if e["action_id"] == "selected"
            and e["kind"] == "task.updated"
            and e["resource"] == "TASK-42"
            and e["after"].get("reviewed") is True
        ]
        if not events:
            return

        def action(s, emit):
            if s["source_hash"] is None:
                s["source_hash"] = digest(events[0])
                s["parent"] = s["lease"] = True
                emit("authorized_pending", 0, {})

        self._change(0, action)

    def advance(self, target, *, lose_ack=False):
        now = self.snapshot()["clock"]

        def action(s, emit):
            if self.mechanism == "delegated_authority":
                if now < 100 <= target and s["parent"] and not s["cancelled"]:
                    s["child"] = True
                    emit("child_minted", 100, dict(expires=1100))
                if now < 110 <= target and s["child"]:
                    s["access_observed"] = True
                    emit("mock_access", 110, dict(data="synthetic-placeholder"))
                if now < 1100 <= target and s["child"]:
                    s["child"] = False
                    emit("child_expired", 1100, {})
            else:
                if now < 80 <= target and not s["legitimate_delivered"]:
                    if s["lease"]:
                        s["blocked"] = True
                        emit("legitimate_blocked", 80, {})
                    else:
                        s["legitimate_delivered"] = True
                        emit("legitimate_delivered", 80, {})
                if now < 100 <= target and not s["legitimate_delivered"]:
                    s["missed"] = True
                    emit("deadline_missed", 100, dict(deadline=100))

        self._change(target, action)
        if lose_ack:
            raise LostAcknowledgment("Committed provider advance, acknowledgment withheld")

    def recover(self):
        now = self.snapshot()["clock"]

        def action(s, emit):
            if s["conflict"]:
                return
            s["parent"] = s["lease"] = False
            s["cancelled"] = True
            if (
                self.mechanism == "deadline_opportunity"
                and s["blocked"]
                and not s["missed"]
                and not s["legitimate_delivered"]
                and now < 100
            ):
                s["legitimate_delivered"] = True
                emit("legitimate_delivered", now, {})

        self._change(now, action)

    def independent(self, *, conflict=False):
        now = self.snapshot()["clock"]

        def action(s, emit):
            s["note"] = "independent-authorized-edit"
            s["conflict"] = conflict
            emit("independent_edit", now, dict(note=s["note"], conflict=conflict))

        self._change(now, action)
