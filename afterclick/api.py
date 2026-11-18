import asyncio
import json
import os
import threading
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from afterclick import domain
from afterclick.infrastructure import schema as s
from afterclick.infrastructure.db import Database


class Changes(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str | None = Field(default=None, max_length=10000)
    reviewed: bool | None = None
    priority: Literal["Normal", "High", "Critical"] | None = None
    assignee: Literal["Maya", "Alex", "Jordan"] | None = None
    status: Literal["Backlog", "In progress", "Done"] | None = None


class Patch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1)
    operation_id: str = Field(min_length=1, max_length=128)
    changes: Changes


class Comment(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    operation_id: str = Field(min_length=1, max_length=128)


def public_task(value):
    return {k: v for k, v in value.items() if k != "owners"}


def create_app(db=None, auto_tick=False, static_dir=None):
    db = db or Database()

    async def tick():
        while True:
            await asyncio.sleep(0.1)

            def step():
                with db.engine.connect() as c:
                    now = domain.clock(c)
                if not now["paused"]:
                    domain.advance(db, now["logical_time"] + 100)

            await asyncio.to_thread(step)

    @asynccontextmanager
    async def lifespan(app):
        await asyncio.to_thread(db.migrate)
        await asyncio.to_thread(domain.seed, db)
        worker = asyncio.create_task(tick()) if auto_tick else None
        yield
        if worker:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker

    app = FastAPI(title="FlowBoard", lifespan=lifespan)
    app.state.db = db
    app.state.stop_streams = threading.Event()

    @app.exception_handler(domain.Conflict)
    async def conflict_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(domain.NotFound)
    async def missing_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.get("/api/health")
    def health():
        with db.engine.connect() as c:
            c.execute(select(s.runtime.c.id)).one()
        return {"status": "ok"}

    @app.get("/api/projects")
    def projects():
        with db.engine.connect() as c:
            return domain.rows(c, s.projects)

    @app.get("/api/projects/{project_id}/tasks")
    def tasks(project_id: str):
        with db.engine.connect() as c:
            return [
                public_task(r) for r in domain.rows(c, s.tasks) if r["project_id"] == project_id
            ]

    @app.get("/api/tasks/{task_id}")
    def get_task(task_id: str):
        with db.engine.connect() as c:
            return public_task(domain.task(c, task_id))

    @app.patch("/api/tasks/{task_id}")
    def patch(
        task_id: str,
        body: Patch,
        x_action_id: str | None = Header(default=None),
        x_actor: str = Header(default="browser"),
    ):
        changes = body.changes.model_dump(exclude_unset=True)
        if not changes or any(v is None for v in changes.values()):
            raise HTTPException(422, "Supply at least one non-null change")
        return public_task(
            domain.patch_task(
                db,
                task_id,
                changes,
                body.expected_version,
                body.operation_id,
                x_action_id or body.operation_id,
                x_actor,
            )
        )

    @app.get("/api/tasks/{task_id}/activity")
    def activity(task_id: str):
        with db.engine.connect() as c:
            return [
                dict(id=r["id"], kind=r["kind"], actor=r["actor"], after=r["after"])
                for r in domain.rows(c, s.effects)
                if r["resource"] == task_id
            ]

    @app.get("/api/tasks/{task_id}/comments")
    def comments(task_id: str):
        with db.engine.connect() as c:
            return [r for r in domain.rows(c, s.comments) if r["task_id"] == task_id]

    @app.post("/api/tasks/{task_id}/comments")
    def comment(task_id: str, body: Comment, x_actor: str = Header(default="browser")):
        return domain.add_comment(db, task_id, body.body, body.operation_id, x_actor)

    @app.get("/api/notifications")
    def notifications():
        with db.engine.connect() as c:
            delivered = {r["notification_id"] for r in domain.rows(c, s.deliveries)}
            return [
                {**r, "delivered": r["id"] in delivered} for r in domain.rows(c, s.notifications)
            ]

    @app.post("/api/events/{event_id}/ack")
    def ack(event_id: int, session_id: str = Header(alias="X-Session-ID", max_length=128)):
        with db.transaction() as c:
            event = c.execute(
                select(s.outbox).where(s.outbox.c.id == event_id, s.outbox.c.published.is_(True))
            ).first()
            if event is None:
                raise HTTPException(409, "Cannot acknowledge an unpublished event")
            c.execute(
                pg_insert(s.sse_receipts)
                .values(session_id=session_id, outbox_id=event_id)
                .on_conflict_do_nothing()
            )
        return {"received": event_id}

    @app.get("/api/events")
    async def events(request: Request, last_event_id: str = Header(default="0")):
        try:
            cursor = int(last_event_id)
        except ValueError as exc:
            raise HTTPException(400, "Invalid event cursor") from exc

        def fetch(after):
            with db.engine.connect() as c:
                return [
                    dict(r)
                    for r in c.execute(
                        select(s.outbox)
                        .where(s.outbox.c.published.is_(True), s.outbox.c.id > after)
                        .order_by(s.outbox.c.id)
                    ).mappings()
                ]

        async def stream():
            nonlocal cursor
            yield ": connected\n\n"
            while not app.state.stop_streams.is_set() and not await request.is_disconnected():
                batch = await asyncio.to_thread(fetch, cursor)
                for event in batch:
                    cursor = event["id"]
                    yield f"id: {cursor}\ndata: {json.dumps(event['payload'])}\n\n"
                await asyncio.sleep(0.05)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if static_dir and Path(static_dir).is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")
    return app


app = create_app(
    auto_tick=os.environ.get("AUTO_TICK", "false") == "true",
    static_dir=os.environ.get("STATIC_DIR"),
)
