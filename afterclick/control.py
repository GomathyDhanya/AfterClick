"""Separate loopback-only experimental control service; never mounted on FlowBoard."""

import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import update

from afterclick import domain
from afterclick.infrastructure import schema as s
from afterclick.infrastructure.db import Database


class Reset(BaseModel):
    seed: int = 7
    worker_delay: int = Field(default=100, ge=0)
    delivery_delay: int = Field(default=100, ge=0)


class Advance(BaseModel):
    target: int = Field(ge=0)
    release_id: str | None = None


def create_control(db, token):
    if not token or not db.schema.startswith("ac_"):
        raise ValueError("Control plane needs a token and isolated experiment schema")

    def authenticate(authorization: str = Header(default="")):
        if not secrets.compare_digest(authorization, f"Bearer {token}"):
            raise HTTPException(403)

    app = FastAPI(title="AfterClick control", dependencies=[Depends(authenticate)])

    @app.post("/research/reset")
    def reset(body: Reset):
        domain.reset_experiment(db, body.seed, body.worker_delay, body.delivery_delay)
        return {"reset": True}

    @app.post("/research/scheduler/advance")
    @app.post("/research/scheduler/release-event")
    def advance(body: Advance):
        try:
            return {"executed": domain.advance(db, body.target, body.release_id)}
        except (ValueError, domain.Conflict) as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/research/scheduler/pause")
    def pause(paused: bool = True):
        with db.transaction() as c:
            c.execute(update(s.runtime).values(paused=paused))
        return {"paused": paused}

    @app.get("/research/state")
    def state():
        return domain.snapshot(db)

    @app.get("/research/effects")
    def effects():
        return domain.snapshot(db)["effect_events"]

    @app.get("/research/pending-jobs")
    def jobs():
        return [j for j in domain.snapshot(db)["scheduled_jobs"] if j["status"] == "pending"]

    return app


def from_env():
    db = Database(os.environ["EXPERIMENT_SCHEMA"])
    db.migrate()
    domain.seed(db)
    return create_control(db, os.environ["RESEARCH_TOKEN"])
