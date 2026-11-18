"""Finite conditional compensation witnesses for three fixed application workflows.

This is not a counterfactual oracle or an optimizer. The independent evaluation modules
consume resulting snapshots and never trust the status returned here.
"""

from sqlalchemy import delete, select, update

from afterclick import domain
from afterclick.infrastructure import schema as s

FIELD_TABLES = {
    "task.updated": s.tasks,
    "readiness.updated": s.tasks,
    "summary.updated": s.projects,
}


def compensate_owned_workflow(db, action_id):
    with db.transaction() as c:
        events = [e for e in domain.rows(c, s.effects) if e["action_id"] == action_id]
        roots = [e for e in events if e["kind"] == "task.updated"]
        if len(roots) != 1 or set(roots[0]["after"]) not in (
            {"reviewed"},
            {"priority"},
            {"status"},
        ):
            return {"status": "UNSUPPORTED"}
        if c.execute(
            select(s.effects.c.id).where(s.effects.c.action_id == f"recovery:{action_id}")
        ).first():
            return {"status": "ALREADY_ATTEMPTED"}
        field_effects = [e for e in events if e["kind"] in FIELD_TABLES]
        plan = []
        for effect in reversed(field_effects):
            table = FIELD_TABLES[effect["kind"]]
            current = dict(
                c.execute(select(table).where(table.c.id == effect["resource"])).mappings().one()
            )
            for field, expected in effect["after"].items():
                if current["owners"].get(field) != action_id or current[field] != expected:
                    return {"status": "CONFLICT", "resource": current["id"], "field": field}
            plan.append((effect, table, current))
        cancelled = (
            c.execute(
                update(s.jobs)
                .where(s.jobs.c.action_id == action_id, s.jobs.c.status == "pending")
                .values(status="cancelled")
                .returning(s.jobs.c.id)
            )
            .scalars()
            .all()
        )
        delivered = set(c.execute(select(s.deliveries.c.notification_id)).scalars())
        removed = []
        for table in (s.notifications, s.escalations):
            for record in c.execute(select(table).where(table.c.action_id == action_id)).mappings():
                if table is s.notifications and record["id"] in delivered:
                    continue
                result = c.execute(
                    delete(table).where(
                        table.c.id == record["id"],
                        table.c.version == record["version"],
                        table.c.action_id == action_id,
                    )
                )
                if result.rowcount != 1:
                    raise domain.Conflict("Derived record changed; transaction rolled back")
                removed.append({"table": table.name, "id": record["id"]})
        for effect, table, current in plan:
            restored = effect["before"]
            predicates = [table.c.id == current["id"], table.c.version == current["version"]]
            predicates.extend(
                table.c.field_revisions[f].as_integer() == current["field_revisions"][f]
                for f in restored
            )
            result = c.execute(
                update(table)
                .where(*predicates)
                .values(
                    **restored,
                    version=current["version"] + 1,
                    field_revisions=domain.revised(current, restored),
                    owners={**current["owners"], **{f: f"recovery:{action_id}" for f in restored}},
                )
            )
            if result.rowcount != 1:
                raise domain.Conflict("Field revision changed; transaction rolled back")
            domain.emit(
                c,
                "task.compensated" if table is s.tasks else "project.compensated",
                f"recovery:{action_id}",
                "recovery",
                current["id"],
                effect["after"],
                restored,
                parents=[effect["id"]],
                publish=True,
            )
        domain.emit(
            c,
            "recovery.attempted",
            f"recovery:{action_id}",
            "recovery",
            roots[0]["resource"],
            after={"cancelled_jobs": cancelled, "removed_records": removed},
        )
        return {"status": "APPLIED", "cancelled_jobs": cancelled, "removed_records": removed}
