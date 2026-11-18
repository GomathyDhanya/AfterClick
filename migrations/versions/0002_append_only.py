"""Protect historical effect and delivery rows from ordinary mutation."""

from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    op.execute("""
        CREATE FUNCTION reject_history_mutation() RETURNS trigger AS $$
        BEGIN
            IF current_setting('afterclick.fixture_reset', true) = 'on' THEN
                RETURN OLD;
            END IF;
            RAISE EXCEPTION 'Historical evidence is append-only';
        END;
        $$ LANGUAGE plpgsql
    """)
    for table in ("effect_events", "notification_deliveries"):
        op.execute(f"""CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON {table}
                       FOR EACH ROW EXECUTE FUNCTION reject_history_mutation()""")


def downgrade():
    for table in ("effect_events", "notification_deliveries"):
        op.execute(f"DROP TRIGGER append_only ON {table}")
    op.execute("DROP FUNCTION reject_history_mutation()")
