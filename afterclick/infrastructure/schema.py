"""Initial schema. Migration 0001 freezes these definitions independently."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

runtime = Table(
    "runtime",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("logical_time", Integer, nullable=False),
    Column("seed", Integer, nullable=False),
    Column("worker_delay", Integer, nullable=False),
    Column("delivery_delay", Integer, nullable=False),
    Column("paused", Boolean, nullable=False),
)
projects = Table(
    "projects",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("completed", Integer, nullable=False),
    Column("version", Integer, nullable=False),
    Column("owners", JSONB, nullable=False),
    Column("field_revisions", JSONB, nullable=False),
)
tasks = Table(
    "tasks",
    metadata,
    Column("id", String, primary_key=True),
    Column("project_id", String, ForeignKey("projects.id"), nullable=False),
    Column("title", String, nullable=False),
    Column("description", Text, nullable=False),
    Column("reviewed", Boolean, nullable=False),
    Column("ready", Boolean, nullable=False),
    Column("priority", String, nullable=False),
    Column("assignee", String, nullable=False),
    Column("status", String, nullable=False),
    Column("version", Integer, nullable=False),
    Column("owners", JSONB, nullable=False),
    Column("field_revisions", JSONB, nullable=False),
)
dependencies = Table(
    "task_dependencies",
    metadata,
    Column("task_id", String, ForeignKey("tasks.id"), primary_key=True),
    Column("prerequisite_id", String, ForeignKey("tasks.id"), primary_key=True),
)
operations = Table(
    "operations",
    metadata,
    Column("id", String, primary_key=True),
    Column("request_hash", String, nullable=False),
    Column("action_id", String, nullable=False),
    Column("response", JSONB, nullable=False),
)
effects = Table(
    "effect_events",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("kind", String, nullable=False),
    Column("action_id", String, nullable=False),
    Column("actor", String, nullable=False),
    Column("resource", String, nullable=False),
    Column("logical_time", Integer, nullable=False),
    Column("parents", JSONB, nullable=False),
    Column("before", JSONB),
    Column("after", JSONB),
    Column("irreversible", Boolean, nullable=False),
)
outbox = Table(
    "outbox_events",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("effect_id", BigInteger, ForeignKey("effect_events.id"), nullable=False, unique=True),
    Column("payload", JSONB, nullable=False),
    Column("published", Boolean, nullable=False),
)
jobs = Table(
    "scheduled_jobs",
    metadata,
    Column("id", String, primary_key=True),
    Column("kind", String, nullable=False),
    Column("action_id", String, nullable=False),
    Column("due", Integer, nullable=False),
    Column("parent_id", String, ForeignKey("scheduled_jobs.id")),
    Column("status", String, nullable=False),
    Column("payload", JSONB, nullable=False),
)
notifications = Table(
    "notifications",
    metadata,
    Column("id", String, primary_key=True),
    Column("action_id", String, nullable=False),
    Column("message", String, nullable=False),
    Column("version", Integer, nullable=False),
)
deliveries = Table(
    "notification_deliveries",
    metadata,
    Column("notification_id", String, ForeignKey("notifications.id"), primary_key=True),
    Column("recipient", String, primary_key=True),
    Column("logical_time", Integer, nullable=False),
    Column("action_id", String, nullable=False),
)
escalations = Table(
    "escalations",
    metadata,
    Column("id", String, primary_key=True),
    Column("task_id", String, nullable=False),
    Column("action_id", String, nullable=False),
    Column("version", Integer, nullable=False),
)
comments = Table(
    "task_comments",
    metadata,
    Column("id", String, primary_key=True),
    Column("task_id", String, ForeignKey("tasks.id")),
    Column("body", Text, nullable=False),
    Column("actor", String, nullable=False),
    Column("version", Integer, nullable=False),
)
sse_receipts = Table(
    "sse_receipts",
    metadata,
    Column("session_id", String, primary_key=True),
    Column("outbox_id", BigInteger, ForeignKey("outbox_events.id"), primary_key=True),
)

TABLES = {table.name: table for table in metadata.sorted_tables}
