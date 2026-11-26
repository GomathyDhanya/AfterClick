"""FlowBoard v2 extension: real versioned tasks, dependency edges and approval comments.

No OpsConsole business tables, mutation code or approval engine are imported.
"""

import time
from contextlib import contextmanager

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, insert, select, update

from afterclick.api import create_app
from afterclick.completion_v12.benchmark import domain_v12 as domain
from afterclick.completion_v12.benchmark.infrastructure import (
    AuditRuntime,
    controls,
    outbox,
    receipts,
    requests,
)
from afterclick.completion_v12.evidence import digest
from afterclick.infrastructure import schema as core

flow_metadata = MetaData()
grants = Table(
    "flow_capability_grants",
    flow_metadata,
    Column("id", String, primary_key=True),
    Column("principal", String, nullable=False),
    Column("capability", String, nullable=False),
    Column("active", Boolean, nullable=False),
    Column("revision", Integer, nullable=False),
)


class TransactionBoundDatabase:
    """Reuse existing domain operations within an already locked SQL transaction."""

    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def transaction(self):
        yield self.connection


class FlowWorld(AuditRuntime):
    def initialize(self):
        self.db.migrate()
        domain.seed(self.db)
        with self.db.transaction() as c:
            self.initialize_audit(c)
            flow_metadata.create_all(c)
            operations = self.contract["private"]["initial_private_state"]["operations"]
            for op in operations:
                if op["kind"] == "restore":
                    c.execute(
                        insert(grants),
                        dict(
                            id=op["id"],
                            principal="incoming-internal",
                            capability=op["label"],
                            active=False,
                            revision=1,
                        ),
                    )
                c.execute(
                    insert(core.tasks),
                    dict(
                        id=op["id"],
                        project_id="release",
                        title=op["label"],
                        description="unselected",
                        reviewed=False,
                        ready=not op["dependencies"],
                        priority="Normal",
                        assignee="Maya",
                        status="Backlog",
                        version=1,
                        owners={},
                        field_revisions={k: 1 for k in domain.TASK_FIELDS},
                    ),
                )
            for op in operations:
                for parent in op["dependencies"]:
                    c.execute(
                        insert(core.dependencies), dict(task_id=op["id"], prerequisite_id=parent)
                    )

    def public(self):
        with self.db.engine.connect() as c:
            by_id = {t["id"]: t for t in domain.rows(c, core.tasks)}
            ops = self.contract["public"]["initial_public_state"]["operations"]
            return dict(
                application="FlowBoard",
                instruction=self.contract["public"]["instruction"],
                policy=self.public_documents,
                service=self.service_public(c),
                capability_grants=self.rows(c, grants),
                records=[
                    dict(
                        id=o["id"],
                        label=o["label"],
                        kind=o["kind"],
                        dependencies=o["dependencies"],
                        choices=o["choices"],
                        role=o["role"],
                        scope_rule=o.get("scope_rule", "primary"),
                        stage="complete"
                        if by_id[o["id"]]["status"] == "Done"
                        else by_id[o["id"]]["status"],
                        value=by_id[o["id"]]["description"],
                        version=by_id[o["id"]]["version"],
                    )
                    for o in ops
                ],
            )

    def act(self, identifier, value, version, operation_id):
        signature = digest([identifier, value, version])
        by_op = {o["id"]: o for o in self.contract["public"]["initial_public_state"]["operations"]}
        if identifier not in by_op:
            raise HTTPException(400, "Unknown board task")
        op = by_op[identifier]
        with self.db.transaction() as c:
            previous = (
                c.execute(select(requests).where(requests.c.id == operation_id)).mappings().first()
            )
            if previous:
                if previous["request_hash"] != signature:
                    raise HTTPException(409, "Operation identity conflict")
                return previous["response"]
            task = domain.task(c, identifier)
            if task["version"] != version:
                raise HTTPException(409, "Refresh current board field revisions")
            if any(domain.task(c, d)["status"] != "Done" for d in op["dependencies"]):
                raise HTTPException(409, "Dependent board tasks incomplete")
            if value not in op["choices"]:
                raise HTTPException(400, "Choose a visible business scope")
            status = "Done"
            if op["kind"] == "restore":
                c.execute(
                    update(grants)
                    .where(grants.c.id == identifier)
                    .values(
                        active=True,
                        principal="incoming-internal" if value == op["choices"][0] else value,
                        revision=grants.c.revision + 1,
                    )
                )
            if op["kind"] == "approval":
                status = "In progress"
            elif op["kind"] == "external":
                from afterclick.completion_v12.benchmark.infrastructure import events

                for parent in op["dependencies"]:
                    granted = [
                        e
                        for e in self.rows(c, events)
                        if e["kind"] == "flow.role_approval"
                        and e["payload"].get("operation_id") == parent
                    ]
                    if (
                        granted
                        and max(granted, key=lambda e: e["wall"])["payload"]["expires_ms"]
                        <= self.elapsed()
                    ):
                        raise HTTPException(409, "Role approval expired; renew before dispatch")
                known = [
                    r
                    for r in self.rows(c, receipts)
                    if r["payload"].get("operation_id") == identifier
                ]
                queued = [
                    j
                    for j in self.rows(c, outbox)
                    if j["payload"].get("operation_id") == identifier
                ]
                if not known:
                    status = "In progress"
                    if not queued:
                        self.queue_effect(c, op, value)
            domain.patch_task(
                TransactionBoundDatabase(c),
                identifier,
                dict(description=value, status=status),
                task["version"],
                operation_id,
                operation_id,
                "v12-browser",
            )
            if op["kind"] == "approval":
                self.record(
                    c,
                    "flow.approval_requested",
                    operation_id=identifier,
                    role=op["role"],
                    due_ms=self.elapsed() + 120,
                )
            self.record(
                c,
                "flow.task_committed",
                operation_id=identifier,
                value=value,
                stage=status,
                dependencies=op["dependencies"],
                command_id=operation_id,
            )
            response = dict(committed=True, operation_id=identifier, stage=status)
            c.execute(
                insert(requests), dict(id=operation_id, request_hash=signature, response=response)
            )
        return dict(**response, commit_upper_mono=time.monotonic(), commit_upper_wall=time.time())

    def tick_application(self):
        from afterclick.completion_v12.benchmark.infrastructure import events

        domain.advance(self.db, self.elapsed())
        with self.db.transaction() as c:
            control = c.execute(select(controls)).mappings().one()
            flags = dict(control["state"])
            if self.elapsed() >= self.collaborator_ms and not flags.get(
                "business_collaborator_done"
            ):
                first = domain.task(c, "w00")
                domain.patch_task(
                    TransactionBoundDatabase(c),
                    "w00",
                    dict(assignee="Jordan"),
                    first["version"],
                    "collaborator-handoff",
                    "collaborator-handoff",
                    "controlled-collaborator",
                )
                flags["business_collaborator_done"] = True
                c.execute(update(controls).values(state=flags, version=control["version"] + 1))
                self.record(c, "flow.collaborator_task_changed", operation_id="w00")
            completed_requests = {
                r["payload"].get("request_id")
                for r in self.rows(c, events)
                if r["kind"] == "flow.role_approval"
            }
            latest = {}
            expired = {
                e["payload"].get("request_id")
                for e in self.rows(c, events)
                if e["kind"] == "flow.role_expired"
            }
            for event in self.rows(c, events):
                if event["kind"] == "flow.role_approval":
                    key = event["payload"]["operation_id"]
                    if key not in latest or event["wall"] > latest[key]["wall"]:
                        latest[key] = event
            for key, event in latest.items():
                dependents = {
                    o["id"]
                    for o in self.contract["public"]["initial_public_state"]["operations"]
                    if o["kind"] == "external" and key in o["dependencies"]
                }
                dispatched = {j["payload"].get("operation_id") for j in self.rows(c, outbox)}
                consumed = bool(dependents) and dependents <= dispatched
                if (
                    event["payload"]["expires_ms"] <= self.elapsed()
                    and event["payload"]["request_id"] not in expired
                    and not consumed
                ):
                    task = domain.task(c, key)
                    if task["status"] == "Done":
                        identifier = "expire:" + event["id"]
                        domain.patch_task(
                            TransactionBoundDatabase(c),
                            key,
                            dict(status="Backlog"),
                            task["version"],
                            identifier,
                            identifier,
                            "controlled-approver",
                        )
                    self.record(
                        c,
                        "flow.role_expired",
                        operation_id=key,
                        request_id=event["payload"]["request_id"],
                    )
            for event in self.rows(c, events):
                if (
                    event["kind"] != "flow.approval_requested"
                    or event["payload"]["due_ms"] > self.elapsed()
                    or event["id"] in completed_requests
                ):
                    continue
                key = event["payload"]["operation_id"]
                task = domain.task(c, key)
                if task["status"] == "Done":
                    continue
                comment_id = "approval-" + event["id"]
                bound = TransactionBoundDatabase(c)
                domain.add_comment(
                    bound,
                    key,
                    event["payload"]["role"] + " approved scope",
                    comment_id,
                    "controlled-approver",
                )
                domain.patch_task(
                    bound,
                    key,
                    dict(status="Done"),
                    task["version"],
                    comment_id + ":complete",
                    comment_id,
                    "controlled-approver",
                )
                self.record(
                    c,
                    "flow.role_approval",
                    operation_id=key,
                    role=event["payload"]["role"],
                    request_id=event["id"],
                    expires_ms=self.elapsed()
                    + (60000 if self.contract["complexity"] == "L3" else 120000),
                )

    def reconcile_receipts(self):
        with self.db.transaction() as c:
            for receipt in self.rows(c, receipts):
                key = receipt["payload"].get("operation_id")
                if key is None:
                    continue
                task = domain.task(c, key)
                if task["status"] != "Done":
                    identifier = "verify:" + receipt["id"]
                    domain.patch_task(
                        TransactionBoundDatabase(c),
                        key,
                        dict(status="Done"),
                        task["version"],
                        identifier,
                        identifier,
                        "v12-browser-verification",
                    )
                    self.record(
                        c, "flow.receipt_verified", operation_id=key, receipt_id=receipt["id"]
                    )

    def snapshot(self):
        with self.db.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
            return dict(
                **self.audit_snapshot(c),
                flow_capability_grants=self.rows(c, grants),
                **{t.name: domain.rows(c, t) for t in core.metadata.sorted_tables},
            )

    def app(self):
        from afterclick.completion_v12.benchmark.ui import flow_html

        app = create_app(self.db, auto_tick=False, static_dir="apps/flowboard-web/dist")
        original_routes = list(app.router.routes)
        app.router.routes.clear()

        @app.get("/workflow", response_class=HTMLResponse)
        def workflow():
            return flow_html()

        self.app_routes(app)
        app.router.routes.extend(original_routes)
        return app
