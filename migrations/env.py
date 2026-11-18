from alembic import context

from afterclick.infrastructure.schema import metadata

connection = context.config.attributes.get("connection")
if connection is None:
    from afterclick.infrastructure.db import Database

    db = Database()
    with db.engine.begin() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
else:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()
