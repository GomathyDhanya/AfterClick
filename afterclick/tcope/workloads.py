"""Independent wall-clock fake services appended to the preserved FlowBoard app.

Private schedule state never enters public(). Receivers commit immutable evidence
via real loopback HTTP; no external network, money, mail or permissions are used.
"""

import json
import random
import socket
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.routing import APIRoute
from sqlalchemy import Column, Float, Integer, MetaData, String, Table, insert, select, text, update
from sqlalchemy.dialects.postgresql import JSONB

from afterclick import domain
from afterclick.api import create_app
from afterclick.infrastructure import schema as core
from afterclick.model_sprint.tasks import TaskSpec
from afterclick.tcope.driver import CoreWorld

metadata = MetaData()
accounts = Table(
    "tc_accounts",
    metadata,
    Column("id", String, primary_key=True),
    Column("units", Integer, nullable=False),
)
runtime = Table(
    "tc_runtime",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("family", String, nullable=False),
    Column("clock_ms", Integer, nullable=False),
    Column("state", JSONB, nullable=False),
)
events = Table(
    "tc_events",
    metadata,
    Column("id", String, primary_key=True),
    Column("kind", String, nullable=False),
    Column("ms", Integer, nullable=False),
    Column("wall", Float, nullable=False),
    Column("action_id", String, nullable=False),
    Column("actor", String, nullable=False),
    Column("payload", JSONB, nullable=False),
)
receipts = Table(
    "tc_receipts",
    metadata,
    Column("id", String, primary_key=True),
    Column("kind", String, nullable=False),
    Column("ms", Integer, nullable=False),
    Column("wall", Float, nullable=False),
    Column("action_id", String, nullable=False),
    Column("payload", JSONB, nullable=False),
)
TABLES = {t.name: t for t in metadata.sorted_tables}


@dataclass(frozen=True)
class WorkloadSpec(TaskSpec):
    family: str
    scenario: str
    schedule: dict
    service_goal: str
    allowed_receipt: bool
    partition: str = "development"

    def private(self):
        return asdict(self)


@contextmanager
def server(app):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    engine = uvicorn.Server(uvicorn.Config(app, log_level="error", timeout_graceful_shutdown=2))
    thread = threading.Thread(target=engine.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    end = time.monotonic() + 15
    try:
        while not engine.started:
            if not thread.is_alive() or time.monotonic() >= end:
                raise RuntimeError("Local service startup failed")
            threading.Event().wait(0.01)
        yield f"http://127.0.0.1:{sock.getsockname()[1]}"
    finally:
        if hasattr(app.state, "stop_streams"):
            app.state.stop_streams.set()
        engine.should_exit = True
        thread.join(5)
        sock.close()
        if thread.is_alive():
            raise RuntimeError("Local service failed shutdown")


class WorkloadWorld(CoreWorld):
    from afterclick.tcope.gateway import ServiceGateway as gateway_type

    def __init__(self, spec):
        super().__init__(spec)
        self.offset = 0
        self.anchor = None
        self.mock_stop = threading.Event()
        self.mock_thread = None
        self.receiver_url = None
        self.worker_errors = []

    def initialize(self, checkpoint=None):
        self.browser_payload = checkpoint.get("browser_payload") if checkpoint else None
        self.db.migrate()
        with self.db.transaction() as c:
            metadata.create_all(c)
            c.execute(
                text("""CREATE FUNCTION tc_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Immutable fake observer evidence'; END; $$""")
            )
            for table in ["tc_events", "tc_receipts"]:
                c.execute(
                    text(
                        f"CREATE TRIGGER immutable_history BEFORE UPDATE OR DELETE ON {table} "
                        "FOR EACH ROW EXECUTE FUNCTION tc_immutable()"
                    )
                )
        super().initialize(checkpoint)
        with self.db.transaction() as c:
            if checkpoint:
                for table in metadata.sorted_tables:
                    values = checkpoint["world"][table.name]
                    if values:
                        c.execute(insert(table), values)
            else:
                q = self.spec.schedule
                rng = random.Random(self.spec.seed)
                frontier = q.get(
                    "deadline_ms", rng.choice(q.get("deadline_distribution_ms", [8000]))
                )
                state = dict(
                    nonce=uuid4().hex,
                    deadline=frontier,
                    read_due=q.get("read_ms", frontier + q.get("read_delay_ms", 2000)),
                    ack_lag=q.get(
                        "ack_lag_ms", rng.choice(q.get("ack_lag_distribution_ms", [1000]))
                    ),
                    missing_ack=q.get("missing_ack", False),
                    ack_at=None,
                    verified=False,
                    verify_receipts=[],
                    verify_resolved=False,
                    verified_ms=None,
                    permission=q.get("permission_initial", True),
                    ticket=False,
                    ticket_checked=False,
                    canceled=False,
                    staged=False,
                    pending=q.get("pending", False),
                    inflight=False,
                    done=False,
                    outcome_known=False,
                    collaborator_done=False,
                    action_id="environment-initial",
                    source_actor="controlled_environment",
                    dispatches=0,
                )
                c.execute(
                    insert(runtime).values(id=1, family=self.spec.family, clock_ms=0, state=state)
                )
                c.execute(insert(accounts).values(id="synthetic-resource", units=3))
        if checkpoint:
            self.frozen_initial = self.snapshot()
            self.offset = self.frozen_initial["tc_runtime"][0]["clock_ms"]
        self.allowed_actors.add("controlled-collaborator")

    def snapshot(self):
        with self.db.engine.connect() as c:
            c.exec_driver_sql("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            return {
                name: domain.rows(c, table) for name, table in {**core.TABLES, **TABLES}.items()
            }

    def elapsed(self):
        return self.offset + (int((time.monotonic() - self.anchor) * 1000) if self.anchor else 0)

    def _event(self, c, kind, state, ms, payload=None):
        c.execute(
            insert(events).values(
                id=uuid4().hex,
                kind=kind,
                ms=ms,
                wall=time.time(),
                action_id=state["action_id"],
                actor=state["source_actor"],
                payload=payload or {},
            )
        )

    def public(self):
        with self.db.engine.connect() as c:
            row = c.execute(select(runtime)).mappings().one()
            s = row["state"]
            ms = row["clock_ms"]
            ack_available = s["ack_at"] is not None and ms >= s["ack_at"] and not s["missing_ack"]
            found = [
                r
                for r in domain.rows(c, receipts)
                if ack_available or r["id"] in s.get("verify_receipts", [])
            ]
        # This allowlist is the ONLY mock-service observation source. No true due
        # times, tickets, hidden dispatches, receipt labels or oracle fields cross it.
        resolved = (s["outcome_known"] and ack_available) or s.get("verify_resolved", False)
        return dict(
            service=row["family"],
            age_ms=ms,
            permission="granted" if s["permission"] else "revoked",
            preparation="staged" if s["staged"] else "not staged",
            cancellation="requested" if s["canceled"] else "not requested",
            acknowledgment="verified"
            if s["verified"]
            else "received"
            if resolved
            else "pending or uncertain",
            request_resolved=resolved,
            observed_receipts=len(found),
            verification_age_ms=ms - s["verified_ms"] if s["verified_ms"] is not None else None,
            note="All effects are fake. Committed task fields do not certify service effects. "
            "Cancellation may be too late for a past effect; use Verify. "
            "Revoking access cannot recall a ticket already issued.",
            available_actions=self.buttons(),
        )

    def buttons(self):
        if self.spec.family == "publication":
            return [
                "Stage notice",
                "Send notice",
                "Cancel notice",
                "Verify notice",
                "Wait for update",
            ]
        if self.spec.family == "access":
            return ["Grant access", "Revoke access", "Verify access", "Wait for update"]
        if self.spec.family == "resource":
            return [
                "Authorize resource",
                "Capture resource",
                "Cancel resource",
                "Verify resource",
                "Retry resource",
                "Wait for update",
            ]
        return ["Wait for update"]

    def receiver(self):
        app = FastAPI()

        @app.post("/observe")
        async def observe(request: Request):
            payload = await request.json()
            if set(payload) != {"id", "kind", "action_id", "payload"}:
                raise ValueError("Strict receiver payload")
            with self.db.transaction() as c:
                previous = (
                    c.execute(select(receipts).where(receipts.c.id == payload["id"]))
                    .mappings()
                    .first()
                )
                if not previous:
                    if payload["kind"] == "resource.consumed":
                        account = c.execute(select(accounts)).mappings().one()
                        if account["units"] < 1:
                            raise ValueError("Synthetic resource exhausted")
                        c.execute(update(accounts).values(units=account["units"] - 1))
                    c.execute(
                        insert(receipts).values(**payload, ms=self.elapsed(), wall=time.time())
                    )
            return {"receipt_id": payload["id"], "observed": True}

        return app

    def action(self, name, action_id, actor, nonce):
        if name not in self.buttons():
            raise ValueError("Unknown visible service action")
        with self.db.transaction() as c:
            row = c.execute(select(runtime)).mappings().one()
            s = dict(row["state"])
            ms = self.elapsed()
            if name.startswith("Verify"):
                s["verified"] = True
                s["verify_receipts"] = [r["id"] for r in domain.rows(c, receipts)]
                s["verify_resolved"] = s["outcome_known"]
                s["verified_ms"] = ms
            elif name == "Stage notice":
                s["staged"] = True
            elif name in {"Send notice", "Capture resource", "Retry resource"}:
                if name != "Retry resource":
                    s["nonce"] = nonce
                # Reusing the same operation is idempotent at the independent receiver.
                s.update(
                    pending=True,
                    canceled=False,
                    inflight=False,
                    done=False,
                    outcome_known=False,
                    verified=False,
                    ack_at=None,
                    deadline=ms + self.spec.schedule.get("action_delay_ms", 1000),
                    action_id=action_id,
                    source_actor=actor,
                )
            elif name.startswith("Cancel"):
                s["canceled"] = True
                if not s["inflight"]:
                    s["outcome_known"] = True
                    s["pending"] = False
                    s["ack_at"] = ms
            elif name == "Grant access":
                s["permission"] = True
            elif name == "Revoke access":
                s["permission"] = False
            elif name == "Authorize resource":
                s["staged"] = True
            self._event(
                c,
                "command." + name.lower().replace(" ", "_"),
                {**s, "action_id": action_id, "source_actor": actor},
                ms,
            )
            c.execute(update(runtime).values(clock_ms=ms, state=s))
        return self.public()

    def step(self, target=None):
        if target is not None and self.anchor is None:
            self.offset = target
        dispatch = None
        collaborate = False
        with self.db.transaction() as c:
            row = c.execute(select(runtime)).mappings().one()
            s = dict(row["state"])
            ms = target if target is not None else self.elapsed()
            family = row["family"]
            if (
                family == "access"
                and s["pending"]
                and not s["ticket_checked"]
                and ms >= s["deadline"]
            ):
                s["ticket_checked"] = True
                s["ticket"] = s["permission"]
                self._event(
                    c, "access.ticket_snapshot", s, ms, {"granted_at_snapshot": s["permission"]}
                )
                if not s["ticket"]:
                    s["done"] = True
                    s["pending"] = False
                    s["outcome_known"] = True
                    s["ack_at"] = ms + s["ack_lag"]
            due = (family == "access" and s["ticket"] and ms >= s["read_due"]) or (
                family in {"publication", "resource"}
                and s["pending"]
                and not s["canceled"]
                and ms >= s["deadline"]
            )
            if due and not s["inflight"] and not s["done"]:
                s["inflight"] = True
                s["dispatches"] += 1
                kind = {
                    "publication": "notice.delivered",
                    "access": "external.read",
                    "resource": "resource.consumed",
                }[family]
                dispatch = dict(
                    id=s["nonce"], kind=kind, action_id=s["action_id"], payload={"synthetic": True}
                )
                self._event(c, "dispatch.issued", s, ms, dispatch)
            if (
                family == "collaboration"
                and not s["collaborator_done"]
                and ms >= self.spec.schedule.get("edit_ms", 200)
            ):
                s["collaborator_done"] = True
                collaborate = True
            c.execute(update(runtime).values(clock_ms=ms, state=s))
        if collaborate:
            changes = self.spec.schedule["collaborator_changes"]
            with self.db.engine.connect() as c:
                current = domain.task(c, "TASK-42")
            domain.patch_task(
                self.db,
                "TASK-42",
                changes,
                current["version"],
                "collab-" + self.spec.case_id,
                "collab-" + self.spec.case_id,
                "controlled-collaborator",
            )
        if dispatch:
            with httpx.Client(timeout=2, trust_env=False) as client:
                response = client.post(self.receiver_url + "/observe", json=dispatch)
                response.raise_for_status()
            with self.db.transaction() as c:
                row = c.execute(select(runtime)).mappings().one()
                s = dict(row["state"])
                s.update(done=True, pending=False, outcome_known=True, ack_at=ms + s["ack_lag"])
                self._event(c, "observer.acknowledged", s, ms, response.json())
                c.execute(update(runtime).values(state=s))

    @contextmanager
    def serve(self):
        with server(self.receiver()) as receiver_url:
            self.receiver_url = receiver_url
            app = create_app(
                self.db, auto_tick=self.frozen_initial is None, static_dir="apps/flowboard-web/dist"
            )
            html = (
                Path("apps/flowboard-web/dist/index.html")
                .read_text()
                .replace("</body>", '<script src="/tcope-panel.js"></script></body>')
            )

            if self.browser_payload:
                payload = json.dumps(self.browser_payload).replace("<", "\\u003c")
                html = html.replace(
                    '<script src="/tcope-panel.js">',
                    "<script>window.tcBootstrap="
                    + payload
                    + ';</script><script src="/tcope-panel.js">',
                )

            async def index():
                return HTMLResponse(html)

            async def script():
                return Response(
                    Path(__file__).with_name("panel.js").read_text(),
                    media_type="application/javascript",
                )

            async def state():
                return self.public()

            async def action(request: Request):
                data = await request.json()
                if set(data) != {"name", "nonce"}:
                    raise ValueError("Strict public action")
                return self.action(
                    data["name"],
                    request.headers.get("x-action-id", "unknown"),
                    request.headers.get("x-actor", "browser"),
                    data["nonce"],
                )

            routes = [
                APIRoute("/", index),
                APIRoute("/tcope-panel.js", script),
                APIRoute("/api/tcope/state", state),
                APIRoute("/api/tcope/action", action, methods=["POST"]),
            ]
            app.router.routes[0:0] = routes

            @app.middleware("http")
            async def audit_commit(request, call_next):
                response = await call_next(request)
                if response.status_code < 300 and (
                    request.method == "PATCH"
                    or (request.method == "POST" and "/comments" in request.url.path)
                ):
                    with self.db.transaction() as c:
                        row = c.execute(select(runtime)).mappings().one()
                        stamp = dict(
                            row["state"],
                            action_id=request.headers.get("x-action-id", "unknown"),
                            source_actor=request.headers.get("x-actor", "browser"),
                        )
                        self._event(
                            c,
                            "core.commit_ack",
                            stamp,
                            self.elapsed(),
                            dict(
                                path=request.url.path,
                                operation_id=request.headers.get("x-tcope-operation-id"),
                            ),
                        )
                return response

            try:
                with server(app) as origin:
                    yield origin
                    threading.Event().wait(1.0)
            finally:
                self.mock_stop.set()
                if self.mock_thread:
                    self.mock_thread.join(5)
                self.ticker_stop.set()
                if self.ticker:
                    self.ticker.join(5)

    def start(self):
        super().start()
        self.anchor = time.monotonic()

        def tick():
            while not self.mock_stop.wait(0.02):
                try:
                    self.step()
                except Exception as exc:
                    self.worker_errors.append(type(exc).__name__ + ": " + str(exc))
                    self.mock_stop.set()

        self.mock_thread = threading.Thread(target=tick, daemon=True)
        self.mock_thread.start()

    def finish(self):
        super().finish()
        # Explicit finite observation suffix after live worker stopped, never a
        # recovery operation. New dispatches still go to an isolated HTTP receiver.
        # Receiver is closed at this point: all live requests must have resolved;
        # pending future effects remain censored instead of fabricating receipts.

    def evaluate(self, initial, final, actor):
        from afterclick.tcope.workload_oracle import evaluate_workload

        return evaluate_workload(
            self.spec, initial, final, actor, self.allowed_actors, self.worker_errors
        )

    def browser_checkpoint(self, page, observation):
        public = json.loads(page.locator("#service-state").inner_text())
        public["available_actions"] = [
            c["name"] for c in observation["controls"] if c["name"] in self.buttons()
        ]
        return dict(
            public_state=public, last_nonce=page.evaluate("window.tcClientCheckpoint.last_nonce")
        )

    def browser_resume(self, page):
        page.evaluate("window.tcHold=false")

    def browser_pause(self, page):
        page.evaluate("window.tcHold=true")

    def browser_ready(self, page):
        from playwright.sync_api import expect

        expect(page.locator("#service-state")).to_contain_text('"service"')
