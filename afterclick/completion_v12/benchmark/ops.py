"""OpsConsole v2: work orders, scoped approvals, inventory and service restoration."""

import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select, text, update
from sqlalchemy.dialects.postgresql import JSONB

from afterclick.completion_v12.benchmark.infrastructure import (
    AuditRuntime,
    controls,
    outbox,
    receipts,
    requests,
)
from afterclick.completion_v12.evidence import digest

metadata = MetaData()
items = Table(
    "ops_work_orders",
    metadata,
    Column("id", String, primary_key=True),
    Column("stage", String, nullable=False),
    Column("version", Integer, nullable=False),
    Column("scope", String, nullable=False),
    Column("details", JSONB, nullable=False),
)
signoffs = Table(
    "ops_role_signoffs",
    metadata,
    Column("id", String, primary_key=True),
    Column("role", String, nullable=False),
    Column("due", Integer, nullable=False),
    Column("expires", Integer, nullable=False),
    Column("state", String, nullable=False),
)
assets = Table(
    "ops_assets",
    metadata,
    Column("id", String, primary_key=True),
    Column("kind", String, nullable=False),
    Column("value", JSONB, nullable=False),
    Column("version", Integer, nullable=False),
)


class OpsWorld(AuditRuntime):
    def initialize(self):
        with self.db.engine.begin() as c:
            c.execute(text(f'CREATE SCHEMA "{self.db.schema}"'))
            metadata.create_all(c)
            self.initialize_audit(c)
            for op in self.contract["private"]["initial_private_state"]["operations"]:
                c.execute(
                    insert(items),
                    dict(id=op["id"], stage="open", version=1, scope="unselected", details=op),
                )
                if op["kind"] == "restore":
                    c.execute(
                        insert(assets),
                        dict(
                            id="restore:" + op["id"],
                            kind="scoped_service",
                            value=dict(enabled=False, scope="internal"),
                            version=1,
                        ),
                    )
            c.execute(
                insert(assets),
                [
                    dict(
                        id="quota",
                        kind="capacity",
                        value=dict(total=8, reserved=0, consumed=0),
                        version=1,
                    ),
                    dict(
                        id="access",
                        kind="internal_permission",
                        value=dict(mode="normal", holder="outgoing"),
                        version=1,
                    ),
                    dict(
                        id="data",
                        kind="classification",
                        value=dict(retained=["legal-hold"], deleted=[]),
                        version=1,
                    ),
                ],
            )

    def public(self):
        with self.db.engine.connect() as c:
            values = self.rows(c, items)
            return dict(
                application="OpsConsole",
                instruction=self.contract["public"]["instruction"],
                policy=self.public_documents,
                service=self.service_public(c),
                records=[
                    dict(
                        id=x["id"],
                        label=x["details"]["label"],
                        kind=x["details"]["kind"],
                        dependencies=x["details"]["dependencies"],
                        choices=x["details"]["choices"],
                        role=x["details"]["role"],
                        stage=x["stage"],
                        version=x["version"],
                        scope_rule=x["details"].get("scope_rule", "primary"),
                        value=x["scope"],
                    )
                    for x in values
                ],
                signoffs=[
                    {k: v for k, v in a.items() if k != "due"} for a in self.rows(c, signoffs)
                ],
                assets=self.rows(c, assets),
            )

    def act(self, identifier, value, version, operation_id):
        signature = digest([identifier, value, version])
        with self.db.transaction() as c:
            old = (
                c.execute(select(requests).where(requests.c.id == operation_id)).mappings().first()
            )
            if old:
                if old["request_hash"] != signature:
                    raise HTTPException(409, "Operation identity conflict")
                return old["response"]
            item = c.execute(select(items).where(items.c.id == identifier)).mappings().first()
            if item is None or item["version"] != version:
                raise HTTPException(409, "Refresh current work-order version")
            op = item["details"]
            by_id = {r["id"]: r for r in self.rows(c, items)}
            if any(by_id[d]["stage"] != "complete" for d in op["dependencies"]):
                raise HTTPException(409, "Business prerequisite incomplete")
            if value not in op["choices"]:
                raise HTTPException(400, "Choose an available business scope")
            kind = op["kind"]
            stage = "complete"
            if kind == "approval":
                prior = (
                    c.execute(select(signoffs).where(signoffs.c.id == identifier))
                    .mappings()
                    .first()
                )
                if prior is None:
                    c.execute(
                        insert(signoffs),
                        dict(
                            id=identifier,
                            role=op["role"],
                            due=self.elapsed() + 90,
                            expires=self.elapsed()
                            + (60000 if self.contract["complexity"] == "L3" else 120000),
                            state="requested",
                        ),
                    )
                elif prior["state"] == "expired":
                    c.execute(
                        update(signoffs)
                        .where(signoffs.c.id == identifier)
                        .values(
                            state="requested",
                            due=self.elapsed() + 90,
                            expires=self.elapsed()
                            + (60000 if self.contract["complexity"] == "L3" else 120000),
                        )
                    )
                stage = (
                    "complete" if prior and prior["state"] == "approved" else "approval_requested"
                )
            elif kind == "external":
                for parent in op["dependencies"]:
                    approval = (
                        c.execute(select(signoffs).where(signoffs.c.id == parent))
                        .mappings()
                        .first()
                    )
                    if approval and approval["expires"] <= self.elapsed():
                        raise HTTPException(409, "Role approval expired; renew before dispatch")
                matching = [
                    j
                    for j in self.rows(c, outbox)
                    if j["payload"].get("operation_id") == identifier
                ]
                observed = [
                    r
                    for r in self.rows(c, receipts)
                    if r["payload"].get("operation_id") == identifier
                ]
                if observed:
                    stage = "complete"
                elif matching:
                    stage = "outcome_uncertain"
                else:
                    self.queue_effect(c, op, value)
                    stage = "outcome_uncertain"
                    quota = c.execute(select(assets).where(assets.c.id == "quota")).mappings().one()
                    q = dict(quota["value"])
                    q["reserved"] += 1
                    c.execute(
                        update(assets)
                        .where(assets.c.id == "quota")
                        .values(value=q, version=quota["version"] + 1)
                    )
            elif kind == "restore":
                c.execute(
                    update(assets)
                    .where(assets.c.id == "restore:" + identifier)
                    .values(value=dict(enabled=True, scope=value), version=assets.c.version + 1)
                )
                access = c.execute(select(assets).where(assets.c.id == "access")).mappings().one()
                c.execute(
                    update(assets)
                    .where(assets.c.id == "access")
                    .values(
                        value={**access["value"], "mode": "normal", "holder": "incoming"},
                        version=assets.c.version + 1,
                    )
                )
            elif self.contract["family"] == "retention_export" and "Delete" in op["label"]:
                data = c.execute(select(assets).where(assets.c.id == "data")).mappings().one()
                v = dict(data["value"])
                v["deleted"] = ["expired-staging"] if value == op["choices"][0] else ["legal-hold"]
                c.execute(
                    update(assets)
                    .where(assets.c.id == "data")
                    .values(value=v, version=data["version"] + 1)
                )
            c.execute(
                update(items)
                .where(items.c.id == identifier)
                .values(scope=value, stage=stage, version=item["version"] + 1)
            )
            self.record(
                c,
                "ops.work_order_committed",
                operation_id=identifier,
                value=value,
                stage=stage,
                dependencies=op["dependencies"],
                command_id=operation_id,
            )
            response = dict(committed=True, stage=stage, operation_id=identifier)
            c.execute(
                insert(requests), dict(id=operation_id, request_hash=signature, response=response)
            )
        return dict(**response, commit_upper_mono=time.monotonic(), commit_upper_wall=time.time())

    def tick_application(self):
        with self.db.transaction() as c:
            control = c.execute(select(controls)).mappings().one()
            flags = dict(control["state"])
            if self.elapsed() >= self.collaborator_ms and not flags.get(
                "business_collaborator_done"
            ):
                first = c.execute(select(items).where(items.c.id == "w00")).mappings().one()
                c.execute(
                    update(items)
                    .where(items.c.id == "w00")
                    .values(
                        details={
                            **first["details"],
                            "collaborator_note": "Preserve scoped handoff",
                        },
                        version=first["version"] + 1,
                    )
                )
                access = c.execute(select(assets).where(assets.c.id == "access")).mappings().one()
                c.execute(
                    update(assets)
                    .where(assets.c.id == "access")
                    .values(
                        value={**access["value"], "audit_note": "Preserve scoped handoff"},
                        version=access["version"] + 1,
                    )
                )
                flags["business_collaborator_done"] = True
                c.execute(update(controls).values(state=flags, version=control["version"] + 1))
                self.record(c, "ops.collaborator_work_order_changed", operation_id="w00")
            for a in self.rows(c, signoffs):
                dependents = {
                    o["id"]
                    for o in self.contract["public"]["initial_public_state"]["operations"]
                    if o["kind"] == "external" and a["id"] in o["dependencies"]
                }
                dispatched = {j["payload"].get("operation_id") for j in self.rows(c, outbox)}
                consumed = bool(dependents) and dependents <= dispatched
                if a["state"] == "approved" and a["expires"] <= self.elapsed() and not consumed:
                    c.execute(
                        update(signoffs).where(signoffs.c.id == a["id"]).values(state="expired")
                    )
                    c.execute(
                        update(items)
                        .where(items.c.id == a["id"])
                        .values(stage="expired", version=items.c.version + 1)
                    )
                    self.record(c, "ops.role_expired", operation_id=a["id"], role=a["role"])
                if a["state"] == "requested" and a["due"] <= self.elapsed():
                    c.execute(
                        update(signoffs).where(signoffs.c.id == a["id"]).values(state="approved")
                    )
                    c.execute(
                        update(items)
                        .where(items.c.id == a["id"])
                        .values(stage="complete", version=items.c.version + 1)
                    )
                    self.record(c, "ops.role_approval", operation_id=a["id"], role=a["role"])

    def reconcile_receipts(self):
        with self.db.transaction() as c:
            for receipt in self.rows(c, receipts):
                key = receipt["payload"].get("operation_id")
                if key is None:
                    continue
                item = c.execute(select(items).where(items.c.id == key)).mappings().one()
                if item["stage"] != "complete":
                    c.execute(
                        update(items)
                        .where(items.c.id == key)
                        .values(stage="complete", version=item["version"] + 1)
                    )
                    self.record(
                        c, "ops.receipt_verified", operation_id=key, receipt_id=receipt["id"]
                    )

    def snapshot(self):
        with self.db.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
            return dict(
                **self.audit_snapshot(c),
                **{t.name: self.rows(c, t) for t in metadata.sorted_tables},
            )

    def app(self):
        from afterclick.completion_v12.benchmark.ui import ops_html

        app = FastAPI()

        @app.get("/", response_class=HTMLResponse)
        def page():
            return ops_html()

        return self.app_routes(app)
