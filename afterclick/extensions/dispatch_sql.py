"""Real transactional fake receiver and separate receipt observer for the new workload.

Three isolated ac_* schemas, no networking or snapshot restore. Does not import
the finite simulator, its cancellation helper, or its outcome function.
"""

from uuid import uuid4

from sqlalchemy import create_engine, text

from afterclick.extensions.dispatch_oracle import certify
from afterclick.infrastructure.db import DEFAULT_URL


def execute(instance, plan, at=None):
    import os

    engine = create_engine(os.environ.get("DATABASE_URL", DEFAULT_URL))
    schemas = ["ac_obs_" + uuid4().hex for _ in range(3)]
    source, sink, observer = schemas
    age = instance.age if at is None else at
    payload = "RESTRICTED_FIXTURE" if instance.unsafe else "PUBLIC_FIXTURE"
    cancel = None
    if plan == "cancel":
        cancel = age
    elif plan == "verify" and instance.unsafe:
        cancel = age + instance.probe_delay
    elif plan not in {"continue", "verify"}:
        raise ValueError("Unsupported plan")
    try:
        with engine.begin() as c:
            for s in schemas:
                c.execute(text(f'CREATE SCHEMA "{s}"'))
            c.execute(
                text(
                    f'CREATE TABLE "{source}".job (active boolean, payload text, '
                    "independent_note text, cancelled boolean)"
                )
            )
            c.execute(
                text(f"INSERT INTO \"{source}\".job VALUES (true,:p,'initial-note',false)"),
                dict(p=payload),
            )
            c.execute(text(f'CREATE TABLE "{sink}".child (payload text, minted integer)'))
            c.execute(
                text(
                    f'CREATE TABLE "{sink}".copies '
                    "(effect_id text PRIMARY KEY, payload text, time integer)"
                )
            )
            c.execute(
                text(
                    f'CREATE TABLE "{observer}".receipts '
                    "(effect_id text PRIMARY KEY, arrival integer)"
                )
            )
        trace = []
        # Provider and cancellation are actual independent commits; recipient wins ties.
        schedule = [(instance.commit, 0, "consume"), (10, 0, "independent_edit")]
        if instance.mechanism == "pull":
            schedule.append((instance.frontier, 0, "mint_child"))
        if cancel is not None:
            schedule.append((cancel, 1, "cancel"))
        for time, _, kind in sorted(schedule):
            with engine.begin() as c:
                if kind == "independent_edit":
                    c.execute(
                        text(f"UPDATE \"{source}\".job SET independent_note='keep-this-note'")
                    )
                    trace.append(dict(event="independent_edit_commit", time=time))
                elif kind == "cancel":
                    c.execute(text(f'UPDATE "{source}".job SET active=false,cancelled=true'))
                    trace.append(dict(event="source_cancel_commit", time=time))
                elif kind == "mint_child":
                    row = (
                        c.execute(text(f'SELECT active,payload FROM "{source}".job FOR UPDATE'))
                        .mappings()
                        .one()
                    )
                    if row["active"]:
                        c.execute(
                            text(f'INSERT INTO "{sink}".child VALUES (:p,:t)'),
                            dict(p=row["payload"], t=time),
                        )
                        trace.append(dict(event="unrevokable_child_commit", time=time))
                else:
                    row = (
                        c.execute(text(f'SELECT active,payload FROM "{source}".job FOR UPDATE'))
                        .mappings()
                        .one()
                    )
                    permitted = row["active"]
                    if instance.mechanism == "pull":
                        children = (
                            c.execute(text(f'SELECT payload FROM "{sink}".child')).mappings().all()
                        )
                        permitted = bool(children)
                        if children:
                            row = dict(payload=children[0]["payload"])
                    if permitted:
                        c.execute(
                            text(f"INSERT INTO \"{sink}\".copies VALUES ('effect-1',:p,:t)"),
                            dict(p=row["payload"], t=time),
                        )
                        trace.append(
                            dict(event="consumer_commit", time=time, path=instance.mechanism)
                        )
            # Observer writes its own durable record, after provider commit.
        with engine.connect() as c:
            copies = [dict(x) for x in c.execute(text(f'SELECT * FROM "{sink}".copies')).mappings()]
        if copies and not instance.missing_ack:
            for duplicate in range(2 if instance.duplicate_ack else 1):
                with engine.begin() as c:
                    c.execute(
                        text(
                            f"INSERT INTO \"{observer}\".receipts VALUES ('effect-1',:t) "
                            "ON CONFLICT DO NOTHING"
                        ),
                        dict(t=instance.commit + instance.receipt_lag + duplicate),
                    )
        with engine.connect() as c:
            s = dict(c.execute(text(f'SELECT * FROM "{source}".job')).mappings().one())
            receipts = [
                dict(x) for x in c.execute(text(f'SELECT * FROM "{observer}".receipts')).mappings()
            ]
        s["deadline"] = instance.deadline
        certificate = certify(s, dict(copies=copies), receipts)
        return dict(
            source=s,
            initial_state=dict(
                payload=payload,
                active=True,
                independent_note="initial-note",
                copies=[],
                receipts=[],
            ),
            consumer=dict(copies=copies),
            receipts=receipts,
            trace=trace,
            certificate=certificate,
            schemas=schemas,
            provenance="Real PG audit with synthetic schedules; no real-world agent samples",
        )
    finally:
        with engine.begin() as c:
            for s in schemas:
                c.execute(text(f'DROP SCHEMA IF EXISTS "{s}" CASCADE'))
        engine.dispose()
