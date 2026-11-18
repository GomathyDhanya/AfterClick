"""Non-identifying field revisions and project-summary ownership."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"


def upgrade():
    op.add_column("tasks", sa.Column("field_revisions", JSONB, nullable=True))
    # Existing clients cannot prove field histories. A conservative backfill assigns
    # the current record version to every field; fresh reads establish a safe base.
    op.execute("""UPDATE tasks SET field_revisions = jsonb_build_object(
        'title', version, 'description', version, 'reviewed', version, 'ready', version,
        'priority', version, 'assignee', version, 'status', version)""")
    op.alter_column("tasks", "field_revisions", nullable=False)
    op.add_column(
        "projects",
        sa.Column("owners", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column("projects", sa.Column("field_revisions", JSONB, nullable=True))
    op.execute("""UPDATE projects SET field_revisions =
               jsonb_build_object('name', version, 'completed', version)""")
    op.alter_column("projects", "field_revisions", nullable=False)
    op.alter_column("projects", "owners", server_default=None)


def downgrade():
    op.drop_column("projects", "field_revisions")
    op.drop_column("projects", "owners")
    op.drop_column("tasks", "field_revisions")
