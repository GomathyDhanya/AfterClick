from sqlalchemy import delete, select, update

from afterclick import domain
from afterclick.infrastructure import schema as s


def compensate_review(db, action_id):
    """Supported finite primitive: reverse an owned review and its owned readiness.

    No snapshot restoration. No oracle calls. Unknown workflows are rejected before writing.
    The common transaction lock makes field checks, job cancellation, and writes atomic.
    """
    with db.transaction() as c:
        events = [e for e in domain.rows(c, s.effects) if e["action_id"] == action_id]
        roots = [e for e in events if e["kind"] == "task.updated"]
        if len(roots) != 1 or set(roots[0]["after"]) != {"reviewed"}:
            return {"status": "UNSUPPORTED", "reason": "Only one review mutation is supported"}
        owned = [e for e in events if e["kind"] in {"task.updated", "readiness.updated"}]
        completed = c.execute(
            select(s.effects).where(s.effects.c.action_id == f"recovery:{action_id}")
        ).first()
        if completed:
            return {"status": "ALREADY_ATTEMPTED", "reason": "Re-verify current state"}
        # Validate every compensation before any write: an ABA edit is still a conflict.
        for effect in owned:
            current = domain.task(c, effect["resource"])
            for field, value in effect["after"].items():
                if current["owners"].get(field) != action_id or current[field] != value:
                    return {"status": "CONFLICT", "resource": effect["resource"], "field": field}
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
        for notice in c.execute(
            select(s.notifications).where(s.notifications.c.action_id == action_id)
        ).mappings():
            if notice["id"] not in delivered:
                c.execute(
                    delete(s.notifications).where(
                        s.notifications.c.id == notice["id"],
                        s.notifications.c.version == notice["version"],
                    )
                )
                removed.append(notice["id"])
        for effect in reversed(owned):
            current = domain.task(c, effect["resource"])
            values = effect["before"]
            result = c.execute(
                update(s.tasks)
                .where(s.tasks.c.id == current["id"], s.tasks.c.version == current["version"])
                .values(
                    **values,
                    owners={**current["owners"], **{f: f"recovery:{action_id}" for f in values}},
                    version=current["version"] + 1,
                    field_revisions=domain.revised(current, values),
                )
            )
            if result.rowcount != 1:
                raise domain.Conflict("Compensation version changed; transaction rolled back")
            domain.emit(
                c,
                "task.compensated",
                f"recovery:{action_id}",
                "recovery",
                current["id"],
                effect["after"],
                values,
                parents=[effect["id"]],
                publish=True,
            )
        domain.emit(
            c,
            "recovery.attempted",
            f"recovery:{action_id}",
            "recovery",
            roots[0]["resource"],
            after={"cancelled_jobs": cancelled, "removed_notifications": removed},
        )
        return {"status": "APPLIED", "cancelled_jobs": cancelled, "removed_notifications": removed}
