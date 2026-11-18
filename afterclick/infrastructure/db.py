import hashlib
import json
import os
import re
from contextlib import contextmanager

from sqlalchemy import create_engine, text

DEFAULT_URL = "postgresql+psycopg://afterclick:afterclick_local@127.0.0.1:55432/afterclick"


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class Database:
    def __init__(self, schema="flowboard", url=None):
        if not re.fullmatch(r"(?:flowboard|ac_[a-z0-9_]+)", schema):
            raise ValueError("Unsafe experiment schema")
        self.schema = schema
        self.url = url or os.environ.get("DATABASE_URL", DEFAULT_URL)
        self.engine = create_engine(
            self.url, pool_pre_ping=True, connect_args={"options": f"-csearch_path={schema}"}
        )

    def migrate(self):
        from alembic import command
        from alembic.config import Config

        with self.engine.begin() as c:
            c.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'))
            cfg = Config("alembic.ini")
            cfg.attributes["connection"] = c
            command.upgrade(cfg, "head")

    @contextmanager
    def transaction(self):
        # One writer at a time per experimental world. Versions still reject stale clients.
        # Scheduler and recovery share this lock, so cancellation cannot race job execution.
        with self.engine.begin() as c:
            c.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:schema))"), {"schema": self.schema}
            )
            yield c

    def drop_experiment(self):
        if not self.schema.startswith("ac_"):
            raise ValueError("Only isolated experiment schemas can be dropped")
        with self.engine.begin() as c:
            c.execute(text(f'DROP SCHEMA "{self.schema}" CASCADE'))
        self.engine.dispose()
