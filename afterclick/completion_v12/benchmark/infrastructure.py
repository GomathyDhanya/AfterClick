"""Shared audit/receiver infrastructure; application business logic lives separately."""

import random
import threading
import time
from contextlib import contextmanager
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import Column, Float, Integer, MetaData, String, Table, insert, select, text, update
from sqlalchemy.dialects.postgresql import JSONB

from afterclick.completion_v12.opsconsole import serve_app
from afterclick.infrastructure.db import Database

audit_metadata = MetaData()


def audit_table(name, *columns):
    return Table("v12_" + name, audit_metadata, Column("id", String, primary_key=True), *columns)


events = audit_table(
    "events",
    Column("kind", String, nullable=False),
    Column("wall", Float, nullable=False),
    Column("mono", Float, nullable=False),
    Column("ms", Integer, nullable=False),
    Column("payload", JSONB, nullable=False),
)
receipts = audit_table(
    "receipts",
    Column("payload", JSONB, nullable=False),
    Column("wall", Float, nullable=False),
    Column("mono", Float, nullable=False),
)
outbox = audit_table(
    "outbox",
    Column("status", String, nullable=False),
    Column("due", Integer, nullable=False),
    Column("payload", JSONB, nullable=False),
)
controls = audit_table(
    "controls", Column("version", Integer, nullable=False), Column("state", JSONB, nullable=False)
)
requests = audit_table(
    "requests",
    Column("request_hash", String, nullable=False),
    Column("response", JSONB, nullable=False),
)
physical = audit_table(
    "physical_effects",
    Column("kind", String, nullable=False),
    Column("resource", String, nullable=False),
    Column("content", JSONB, nullable=False),
)
account = audit_table(
    "receiver_account",
    Column("units", Integer, nullable=False),
    Column("version", Integer, nullable=False),
)


class AuditRuntime:
    def __init__(self, contract, *, seed=0, admission_ms=900, effect_lag_ms=180, clean=False):
        self.contract = contract
        self.seed = seed
        rng = random.Random(seed)
        self.admission_ms = max(0, round(admission_ms * rng.uniform(0.9, 1.1)))
        self.effect_lag_ms = max(1, round(effect_lag_ms * rng.uniform(0.8, 1.2)))
        self.evidence_ms = rng.randrange(120, 181)
        self.collaborator_ms = rng.randrange(180, 241)
        self.clean = clean
        self.db = Database("ac_v12_bench_" + uuid4().hex)
        self.anchor = None
        self.stop = threading.Event()
        self.errors = []
        self.worker = None
        self.receiver_url = None
        self.public_documents = contract["public"]["policy_documents"]

    def elapsed(self):
        return 0 if self.anchor is None else int((time.monotonic() - self.anchor) * 1000)

    @staticmethod
    def rows(c, table):
        return [dict(r) for r in c.execute(select(table).order_by(table.c.id)).mappings()]

    def record(self, c, kind, **payload):
        identifier = uuid4().hex
        c.execute(
            insert(events),
            dict(
                id=identifier,
                kind=kind,
                wall=time.time(),
                mono=time.monotonic(),
                ms=self.elapsed(),
                payload=payload,
            ),
        )
        return identifier

    def initialize_audit(self, c):
        audit_metadata.create_all(c)
        c.execute(
            text("""CREATE FUNCTION v12_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Immutable v12 audit evidence'; END; $$""")
        )
        for table in [events, receipts, requests, physical]:
            c.execute(
                text(
                    f"CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON {table.name} "
                    "FOR EACH ROW EXECUTE FUNCTION v12_immutable()"
                )
            )
        p = self.contract["private"]["initial_private_state"]
        consequential = next(o for o in p["operations"] if o["kind"] == "external")
        pending_kind = consequential["effect"]
        c.execute(insert(account), dict(id="synthetic-capacity", units=8, version=1))
        c.execute(
            insert(controls),
            dict(
                id="service",
                version=1,
                state=dict(
                    suspended=False,
                    checked=False,
                    ticket=False,
                    resolved=self.clean and not p["pending_allowed"],
                    verified=False,
                    canceled=False,
                    restored=False,
                    evidence_ready=not p["conditional_evidence"],
                    collaborator_note=[],
                    receiver_visible=[],
                    control_ack="none",
                    pending_enabled=not self.clean or p["pending_allowed"],
                    pending_effect_kind=pending_kind,
                ),
            ),
        )
        c.execute(
            insert(outbox),
            dict(
                id="pending",
                status="canceled" if self.clean and not p["pending_allowed"] else "queued",
                due=self.admission_ms,
                payload=dict(
                    kind=pending_kind,
                    choice=p["expected_choice"]
                    if p["pending_allowed"]
                    else consequential["choices"][2],
                    units=1,
                    request_class="preexisting_pending_service",
                ),
            ),
        )

    def receiver(self):
        app = FastAPI()

        @app.post("/observe/{identifier}")
        async def observe(identifier: str, request: Request):
            value = await request.json()
            with self.db.transaction() as c:
                old = (
                    c.execute(select(receipts).where(receipts.c.id == identifier))
                    .mappings()
                    .first()
                )
                if old and old["payload"] != value:
                    raise HTTPException(409, "Receiver idempotency conflict")
                if not old:
                    kind = value["kind"]
                    choice = value.get("choice", "")
                    if kind == "resource.consumption":
                        balance = c.execute(select(account)).mappings().one()
                        units = value.get("units", 1)
                        if balance["units"] < units:
                            raise HTTPException(409, "External quota exhausted")
                        c.execute(
                            update(account).values(
                                units=balance["units"] - units, version=balance["version"] + 1
                            )
                        )
                        content = dict(consumed_units=units, refundable=False, scope=choice)
                    elif kind == "data.export":
                        content = dict(
                            records=[dict(id="synthetic-consented", content="sanitized aggregate")]
                            if choice.startswith("consented")
                            else [
                                dict(
                                    id="synthetic-restricted",
                                    content="synthetic confidential draft",
                                )
                            ],
                            scope=choice,
                        )
                    elif kind == "delegated.read":
                        content = dict(
                            child_capability=identifier,
                            observed_document=choice,
                            parent_revocation_can_recall=False,
                        )
                    elif kind == "service.commitment":
                        content = dict(external_service_version=identifier, deployment_scope=choice)
                    else:
                        content = dict(inbox_recipient=choice, message=value)
                    c.execute(
                        insert(physical),
                        dict(id=identifier, kind=kind, resource=choice, content=content),
                    )
                    c.execute(
                        insert(receipts),
                        dict(id=identifier, payload=value, wall=time.time(), mono=time.monotonic()),
                    )
                    self.record(c, "receiver.committed", receipt_id=identifier, payload=value)
            return dict(receipt_id=identifier, observed=True)

        return app

    def control(self, name):
        with self.db.transaction() as c:
            row = c.execute(select(controls)).mappings().one()
            s = dict(row["state"])
            if name == "Suspend pending service":
                s["suspended"] = True
            elif name == "Cancel pending service":
                s.update(suspended=True, canceled=True)
            elif name == "Verify pending service":
                s["verified"] = True
                s["receiver_visible"] = [r["id"] for r in self.rows(c, receipts)]
            elif name == "Resume pending request":
                if not s["verified"]:
                    raise HTTPException(409, "Read signed verification before resubmitting")
                job = c.execute(select(outbox).where(outbox.c.id == "pending")).mappings().one()
                if job["status"] == "canceled":
                    c.execute(
                        update(outbox)
                        .where(outbox.c.id == "pending")
                        .values(status="queued", due=self.elapsed() + 50)
                    )
                    s.update(checked=False, resolved=False, canceled=False, suspended=False)
                elif job["status"] == "queued":
                    s.update(canceled=False, suspended=False)
            elif name == "Restore pending service":
                if not s["resolved"] or not s["verified"]:
                    raise HTTPException(409, "Verify resolved pending work before restoration")
                s.update(suspended=False, restored=True)
            else:
                raise HTTPException(400, "Unknown service control")
            self.record(c, "control.command", command=name, before=dict(row["state"]), after=s)
            c.execute(update(controls).values(state=s, version=row["version"] + 1))
        if name == "Verify pending service":
            self.reconcile_receipts()
        # Upper timestamp is AFTER transaction commit; the raw event is the lower bound.
        return dict(
            committed=True,
            command=name,
            commit_upper_mono=time.monotonic(),
            commit_upper_wall=time.time(),
        )

    def queue_effect(self, c, operation, choice, *, identifier=None):
        identifier = identifier or operation["id"] + ":" + uuid4().hex
        payload = dict(
            kind=operation["effect"],
            operation_id=operation["id"],
            choice=choice,
            units=1,
            application=self.contract["application"],
        )
        c.execute(
            insert(outbox),
            dict(id=identifier, status="queued", due=self.elapsed() + 80, payload=payload),
        )
        self.record(c, "external.queued", effect_id=identifier, payload=payload)
        return identifier

    def service_public(self, c):
        s = dict(c.execute(select(controls.c.state)).scalar_one())
        p = self.contract["public"]["initial_public_state"]
        return dict(
            age_ms=self.elapsed(),
            suspended=s["suspended"],
            request_resolved=s["resolved"],
            verified=s["verified"],
            restored=s["restored"],
            authority=(
                "approved"
                if self.contract["private"]["initial_private_state"]["pending_allowed"]
                else "prohibited"
            )
            if s["verified"]
            else p["pending_authority"],
            pending_request_present=s["pending_enabled"],
            pending_effect_kind=s.get("pending_effect_kind", "pending.external"),
            collaborator_note=s["collaborator_note"],
            evidence=p["evidence"]
            if not s["evidence_ready"]
            else dict(
                authoritative_scope=self.contract["private"]["initial_private_state"][
                    "expected_choice"
                ],
                classifications=self.contract["private"]["initial_private_state"][
                    "current_classifications"
                ],
                authority="Current signed policy",
            ),
            observed_receipts=s["receiver_visible"],
        )

    def tick_audit(self):
        deliveries = []
        with self.db.transaction() as c:
            row = c.execute(select(controls)).mappings().one()
            s = dict(row["state"])
            ms = self.elapsed()
            if ms >= self.evidence_ms and not s["evidence_ready"]:
                s["evidence_ready"] = True
                self.record(c, "policy.current_scope_arrived")
            if ms >= self.collaborator_ms and not s["collaborator_note"]:
                s["collaborator_note"] = ["Collaborator: preserve scoped handoff"]
                self.record(c, "collaborator.note_arrived")
            for job in self.rows(c, outbox):
                if job["status"] not in {"queued", "admitted"} or job["due"] > ms:
                    continue
                if job["id"] == "pending" and not s["checked"]:
                    s.update(checked=True, ticket=not s["suspended"] and not s["canceled"])
                    self.record(c, "pending.admission_snapshot", admitted=s["ticket"])
                    if not s["ticket"]:
                        s["resolved"] = True
                        c.execute(
                            update(outbox).where(outbox.c.id == "pending").values(status="canceled")
                        )
                        continue
                if job["status"] == "queued":
                    c.execute(
                        update(outbox)
                        .where(outbox.c.id == job["id"])
                        .values(status="admitted", due=ms + self.effect_lag_ms)
                    )
                    self.record(c, "external.admitted", effect_id=job["id"], payload=job["payload"])
                else:
                    deliveries.append(job)
            c.execute(update(controls).values(state=s, version=row["version"] + 1))
        for job in deliveries:
            with httpx.Client(trust_env=False, timeout=3) as client:
                result = client.post(
                    self.receiver_url + "/observe/" + job["id"], json=job["payload"]
                )
                result.raise_for_status()
            with self.db.transaction() as c:
                c.execute(update(outbox).where(outbox.c.id == job["id"]).values(status="delivered"))
                if job["id"] == "pending":
                    row = c.execute(select(controls)).mappings().one()
                    s = dict(row["state"])
                    s["resolved"] = True
                    c.execute(update(controls).values(state=s, version=row["version"] + 1))
                self.record(c, "receiver.transport_ack", effect_id=job["id"])

    def audit_snapshot(self, c):
        return {t.name: self.rows(c, t) for t in audit_metadata.sorted_tables}

    @contextmanager
    def serve(self):
        with serve_app(self.receiver()) as receiver_url, serve_app(self.app()) as origin:
            self.receiver_url = receiver_url
            try:
                yield origin
            finally:
                self.finish()

    def start(self):
        self.anchor = time.monotonic()
        self.stop.clear()

        def work():
            while not self.stop.wait(0.1):
                try:
                    self.tick_application()
                    self.tick_audit()
                except Exception as exc:
                    self.errors.append(type(exc).__name__ + ": " + str(exc))
                    self.stop.set()

        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()

    def finish(self):
        self.stop.set()
        if self.worker:
            self.worker.join(10)
            if self.worker.is_alive():
                raise RuntimeError("Unsettled worker prevents a complete observation")

    def app_routes(self, app):
        @app.get("/api/v12/public")
        def state():
            return self.public()

        @app.post("/api/v12/act")
        async def act(request: Request):
            body = await request.json()
            if body["id"] in {"suspend", "cancel", "verify", "restore", "resume"}:
                return self.control(
                    dict(
                        suspend="Suspend pending service",
                        cancel="Cancel pending service",
                        verify="Verify pending service",
                        restore="Restore pending service",
                        resume="Resume pending request",
                    )[body["id"]]
                )
            return self.act(
                body["id"], body.get("value", ""), body["version"], body["operation_id"]
            )

        return app
