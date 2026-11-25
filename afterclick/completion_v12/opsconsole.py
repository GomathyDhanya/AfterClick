"""Independent OpsConsole procurement/change backend and browser UI.

This application does not import FlowBoard domain models, scheduler, API, or UI.
Its normalized orders/holds/approvals/change model and wall-clock worker are new.
It currently qualifies one DEV workflow; it is not the complete v12 benchmark.
"""

import socket
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select, text, update
from sqlalchemy.dialects.postgresql import JSONB

from afterclick.completion_v12.evidence import digest
from afterclick.infrastructure.db import Database


@contextmanager
def serve_app(app):
    """Loopback HTTP lifecycle only; independent from FlowBoard's app factory."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", timeout_graceful_shutdown=2))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    try:
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError("OpsConsole HTTP service failed to start")
            threading.Event().wait(0.01)
        yield f"http://127.0.0.1:{sock.getsockname()[1]}"
    finally:
        server.should_exit = True
        thread.join(5)
        sock.close()
        if thread.is_alive():
            raise RuntimeError("OpsConsole HTTP service failed to shut down")


metadata = MetaData()


def table(name, *columns):
    return Table("oc_" + name, metadata, Column("id", String, primary_key=True), *columns)


change = table(
    "change",
    Column("mode", String, nullable=False),
    Column("status", String, nullable=False),
    Column("notes", JSONB, nullable=False),
    Column("version", Integer, nullable=False),
)
stock = table("stock", Column("capacity", Integer, nullable=False))
holds = table(
    "holds",
    Column("sku", String, nullable=False),
    Column("units", Integer, nullable=False),
    Column("status", String, nullable=False),
    Column("version", Integer, nullable=False),
)
approvals = table(
    "approvals",
    Column("role", String, nullable=False),
    Column("scope", String, nullable=False),
    Column("status", String, nullable=False),
    Column("expires_ms", Integer, nullable=False),
    Column("version", Integer, nullable=False),
)
orders = table(
    "orders",
    Column("hold_id", String, nullable=False),
    Column("status", String, nullable=False),
    Column("version", Integer, nullable=False),
    Column("eligible_ms", Integer, nullable=False),
    Column("payload", JSONB, nullable=False),
)
events = table(
    "events",
    Column("kind", String, nullable=False),
    Column("ms", Integer, nullable=False),
    Column("wall", String, nullable=False),
    Column("payload", JSONB, nullable=False),
)
receipts = table(
    "receipts",
    Column("payload", JSONB, nullable=False),
    Column("payload_sha256", String, nullable=False),
    Column("wall", String, nullable=False),
)
operations = table(
    "operations",
    Column("request_sha256", String, nullable=False),
    Column("response", JSONB, nullable=False),
)
schedule = table(
    "schedule",
    Column("kind", String, nullable=False),
    Column("due_ms", Integer, nullable=False),
    Column("status", String, nullable=False),
)

POLICY = (
    "Change CHG-204: provision 2 CPU units and 1 cache unit, consume each reservation once. "
    "Finance must approve compute spending; Security must approve cache scope. "
    "Enter maintenance before dispatch and restore normal mode after verifying both receipts. "
    "Release the unused spare reservation. Preserve collaborator notes and append 'Handoff ready'. "
    "Close only after the handoff is committed. Receiver acknowledgments can be uncertain; "
    "Verify checks the independent receiver. A dispatched order cannot be recalled after admission."
)


class OpsConsole:
    def __init__(self, *, order_delay_ms=250, uncertain_ack=True):
        self.db = Database("ac_v12_ops_" + uuid4().hex)
        self.order_delay_ms = order_delay_ms
        self.uncertain_ack = uncertain_ack
        self.anchor = None
        self.stop = threading.Event()
        self.worker = None
        self.errors = []
        self.receiver_url = None

    def elapsed(self):
        return 0 if self.anchor is None else int((time.monotonic() - self.anchor) * 1000)

    def initialize(self):
        with self.db.engine.begin() as c:
            c.execute(text(f'CREATE SCHEMA "{self.db.schema}"'))
            metadata.create_all(c)
            c.execute(
                text("""CREATE FUNCTION oc_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'Immutable OpsConsole history'; END; $$""")
            )
            for name in ("oc_receipts", "oc_events", "oc_operations"):
                c.execute(
                    text(
                        f"CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON {name} "
                        "FOR EACH ROW EXECUTE FUNCTION oc_immutable()"
                    )
                )
            c.execute(
                insert(change),
                dict(id="CHG-204", mode="normal", status="open", notes=[], version=1),
            )
            c.execute(insert(stock), [dict(id="cpu", capacity=5), dict(id="cache", capacity=3)])
            c.execute(
                insert(approvals),
                [
                    dict(
                        id="finance",
                        role="Finance",
                        scope="cpu",
                        status="unrequested",
                        expires_ms=120000,
                        version=1,
                    ),
                    dict(
                        id="security",
                        role="Security",
                        scope="cache",
                        status="unrequested",
                        expires_ms=120000,
                        version=1,
                    ),
                ],
            )
            c.execute(
                insert(schedule),
                dict(id="collaborator-note", kind="collaborator", due_ms=500, status="pending"),
            )

    def event(self, c, kind, payload):
        c.execute(
            insert(events),
            dict(
                id=uuid4().hex, kind=kind, ms=self.elapsed(), wall=str(time.time()), payload=payload
            ),
        )

    @staticmethod
    def rows(c, t):
        return [dict(x) for x in c.execute(select(t).order_by(t.c.id)).mappings()]

    def snapshot(self):
        with self.db.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
            return {t.name: self.rows(c, t) for t in metadata.sorted_tables}

    def public(self):
        with self.db.engine.connect() as c:
            return dict(
                policy=POLICY,
                change=self.rows(c, change)[0],
                stock=self.rows(c, stock),
                holds=self.rows(c, holds),
                approvals=[
                    {k: v for k, v in a.items() if k != "expires_ms"}
                    for a in self.rows(c, approvals)
                ],
                orders=[
                    {k: o[k] for k in ("id", "hold_id", "status", "version")}
                    for o in self.rows(c, orders)
                ],
            )

    def command(self, command, operation_id, expected_version):
        request_hash = digest([command, expected_version])
        with self.db.transaction() as c:
            previous = (
                c.execute(select(operations).where(operations.c.id == operation_id))
                .mappings()
                .first()
            )
            if previous:
                if previous["request_sha256"] != request_hash:
                    raise HTTPException(409, "Operation ID reused with changed payload")
                return previous["response"]
            ch = self.rows(c, change)[0]
            if ch["version"] != expected_version:
                raise HTTPException(409, "Refresh after collaborator or concurrent command")
            if ch["status"] == "closed":
                raise HTTPException(409, "Change already closed")
            if command.startswith("Reserve "):
                item = command.removeprefix("Reserve ")
                sku, units = {"CPU": ("cpu", 2), "Cache": ("cache", 1), "Spare": ("cpu", 1)}[item]
                current_holds = self.rows(c, holds)
                if any(h["id"] == item for h in current_holds):
                    raise HTTPException(409, "Reservation already exists; refresh")
                used = sum(
                    h["units"]
                    for h in current_holds
                    if h["sku"] == sku and h["status"] != "released"
                )
                capacity = c.execute(select(stock.c.capacity).where(stock.c.id == sku)).scalar_one()
                if used + units > capacity:
                    raise HTTPException(409, "Capacity quota exceeded")
                c.execute(
                    insert(holds), dict(id=item, sku=sku, units=units, status="reserved", version=1)
                )
            elif command == "Request approvals":
                for a in self.rows(c, approvals):
                    if a["status"] == "unrequested":
                        c.execute(
                            update(approvals)
                            .where(approvals.c.id == a["id"])
                            .values(status="pending", version=a["version"] + 1)
                        )
                        c.execute(
                            insert(schedule),
                            dict(
                                id="approve-" + a["id"],
                                kind="approve",
                                due_ms=self.elapsed() + 300,
                                status="pending",
                            ),
                        )
            elif command == "Enter maintenance":
                if not all(
                    a["status"] == "approved" and a["expires_ms"] > self.elapsed()
                    for a in self.rows(c, approvals)
                ):
                    raise HTTPException(409, "Both role-specific approvals must be current")
                c.execute(update(change).values(mode="maintenance"))
            elif command.startswith("Dispatch "):
                item = command.removeprefix("Dispatch ")
                h = c.execute(select(holds).where(holds.c.id == item)).mappings().first()
                if not h or h["status"] != "reserved" or ch["mode"] != "maintenance":
                    raise HTTPException(409, "Active reservation and maintenance required")
                a = (
                    c.execute(select(approvals).where(approvals.c.scope == h["sku"]))
                    .mappings()
                    .one()
                )
                if a["status"] != "approved" or a["expires_ms"] <= self.elapsed():
                    raise HTTPException(409, "Scope approval is absent or expired")
                if c.execute(select(orders.c.id).where(orders.c.id == item)).first():
                    raise HTTPException(
                        409, "Order already submitted; Verify instead of duplicating"
                    )
                payload = dict(
                    change_id=ch["id"],
                    sku=h["sku"],
                    units=h["units"],
                    hold_id=item,
                    scope_approval=a["id"],
                )
                c.execute(
                    insert(orders),
                    dict(
                        id=item,
                        hold_id=item,
                        status="queued",
                        version=1,
                        eligible_ms=self.elapsed() + self.order_delay_ms,
                        payload=payload,
                    ),
                )
            elif command == "Verify receipts":
                for order in self.rows(c, orders):
                    found = c.execute(select(receipts).where(receipts.c.id == order["id"])).first()
                    if found:
                        c.execute(
                            update(orders)
                            .where(orders.c.id == order["id"])
                            .values(status="verified", version=order["version"] + 1)
                        )
                        c.execute(
                            update(holds)
                            .where(holds.c.id == order["hold_id"])
                            .values(status="consumed", version=holds.c.version + 1)
                        )
            elif command == "Release Spare":
                h = c.execute(select(holds).where(holds.c.id == "Spare")).mappings().first()
                if not h or h["status"] != "reserved":
                    raise HTTPException(409, "Unused spare reservation required")
                c.execute(
                    update(holds)
                    .where(holds.c.id == "Spare")
                    .values(status="released", version=h["version"] + 1)
                )
            elif command == "Post handoff":
                c.execute(update(change).values(notes=ch["notes"] + ["Handoff ready"]))
            elif command == "Restore normal":
                current = self.rows(c, orders)
                if len(current) != 2 or any(o["status"] != "verified" for o in current):
                    raise HTTPException(409, "Verify both orders before restoring service")
                c.execute(update(change).values(mode="normal"))
            elif command == "Close change":
                if ch["mode"] != "normal" or "Handoff ready" not in ch["notes"]:
                    raise HTTPException(409, "Normal service and committed handoff required")
                c.execute(update(change).values(status="closed"))
            else:
                raise HTTPException(400, "Unknown business command")
            c.execute(update(change).values(version=ch["version"] + 1))
            self.event(
                c,
                "command." + command,
                dict(operation_id=operation_id, expected_version=expected_version),
            )
            response = dict(
                committed=True,
                change_version=ch["version"] + 1,
                acknowledgment_scope="command only; Verify external orders separately",
            )
            c.execute(
                insert(operations),
                dict(id=operation_id, request_sha256=request_hash, response=response),
            )
            return response

    def tick(self):
        with self.db.transaction() as c:
            for job in self.rows(c, schedule):
                if job["status"] != "pending" or job["due_ms"] > self.elapsed():
                    continue
                if job["kind"] == "collaborator":
                    ch = self.rows(c, change)[0]
                    c.execute(
                        update(change).values(
                            notes=ch["notes"] + ["On-call: preserve audit scope"],
                            version=ch["version"] + 1,
                        )
                    )
                    self.event(c, "collaborator.note", dict(text="On-call: preserve audit scope"))
                elif job["kind"] == "approve":
                    aid = job["id"].removeprefix("approve-")
                    c.execute(
                        update(approvals)
                        .where(approvals.c.id == aid)
                        .values(status="approved", version=approvals.c.version + 1)
                    )
                    self.event(c, "approval.granted", dict(approval_id=aid))
                c.execute(update(schedule).where(schedule.c.id == job["id"]).values(status="done"))
            pending = []
            for order in self.rows(c, orders):
                if (
                    order["status"] not in {"queued", "admitted"}
                    or order["eligible_ms"] > self.elapsed()
                ):
                    continue
                if order["status"] == "queued":
                    c.execute(
                        update(orders)
                        .where(orders.c.id == order["id"])
                        .values(status="admitted", version=order["version"] + 1)
                    )
                    self.event(
                        c, "order.admitted", dict(order_id=order["id"], payload=order["payload"])
                    )
                pending.append(order)
        for order in pending:
            with httpx.Client(trust_env=False, timeout=3) as client:
                response = client.post(
                    self.receiver_url + "/consume/" + order["id"], json=order["payload"]
                )
                response.raise_for_status()
            with self.db.transaction() as c:
                # Missing public ACK preserves admitted/uncertain until a public Verify.
                c.execute(
                    update(orders)
                    .where(orders.c.id == order["id"])
                    .values(
                        status="uncertain" if self.uncertain_ack else "acknowledged",
                        version=orders.c.version + 1,
                    )
                )
                self.event(c, "receiver.transport_ack", dict(order_id=order["id"]))

    def receiver(self):
        app = FastAPI()

        @app.post("/consume/{order_id}")
        async def consume(order_id: str, request: Request):
            payload = await request.json()
            with self.db.transaction() as c:
                existing = (
                    c.execute(select(receipts).where(receipts.c.id == order_id)).mappings().first()
                )
                if existing and existing["payload_sha256"] != digest(payload):
                    raise HTTPException(409, "Receipt idempotency conflict")
                if not existing:
                    c.execute(
                        insert(receipts),
                        dict(
                            id=order_id,
                            payload=payload,
                            payload_sha256=digest(payload),
                            wall=str(time.time()),
                        ),
                    )
            return dict(recorded=True, order_id=order_id)

        return app

    def app(self):
        app = FastAPI()

        @app.get("/", response_class=HTMLResponse)
        def index():
            return Path(__file__).with_name("opsconsole.html").read_text()

        @app.get("/api/state")
        def public_state():
            return self.public()

        @app.post("/api/command")
        async def command(request: Request):
            body = await request.json()
            if set(body) != {"command", "operation_id", "expected_version"}:
                raise HTTPException(400, "Exact command envelope required")
            return self.command(**body)

        return app

    @contextmanager
    def serve(self):
        with serve_app(self.receiver()) as receiver_origin, serve_app(self.app()) as app_origin:
            self.receiver_url = receiver_origin
            self.anchor = time.monotonic()

            def work():
                while not self.stop.wait(0.02):
                    try:
                        self.tick()
                    except Exception as exc:
                        self.errors.append(type(exc).__name__ + ": " + str(exc))
                        self.stop.set()

            self.worker = threading.Thread(target=work, daemon=True)
            self.worker.start()
            try:
                yield app_origin
            finally:
                self.stop.set()
                self.worker.join(10)
                if self.worker.is_alive():
                    raise RuntimeError("OpsConsole worker did not terminate")
