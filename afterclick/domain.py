"""FlowBoard mutations, transactional outbox, and deterministic durable jobs."""

from sqlalchemy import delete, insert, select, update

from afterclick.infrastructure import schema as s
from afterclick.infrastructure.db import digest


class Conflict(Exception):
    pass


class NotFound(Exception):
    pass


def rows(c, table):
    return [dict(r) for r in c.execute(select(table).order_by(*table.primary_key)).mappings()]


def clock(c):
    return dict(c.execute(select(s.runtime)).mappings().one())


def task(c, task_id):
    row = c.execute(select(s.tasks).where(s.tasks.c.id == task_id)).mappings().first()
    if not row:
        raise NotFound(task_id)
    return dict(row)


def enqueue(c, job_id, kind, action_id, due, payload, parent=None):
    c.execute(
        insert(s.jobs).values(
            id=job_id,
            kind=kind,
            action_id=action_id,
            due=due,
            parent_id=parent,
            payload=payload,
            status="pending",
        )
    )


def emit(
    c,
    kind,
    action_id,
    actor,
    resource,
    before=None,
    after=None,
    parents=None,
    irreversible=False,
    publish=False,
):
    effect_id = c.execute(
        insert(s.effects)
        .values(
            kind=kind,
            action_id=action_id,
            actor=actor,
            resource=resource,
            logical_time=clock(c)["logical_time"],
            before=before,
            after=after,
            parents=parents or [],
            irreversible=irreversible,
        )
        .returning(s.effects.c.id)
    ).scalar_one()
    if publish:
        outbox_id = c.execute(
            insert(s.outbox)
            .values(
                effect_id=effect_id,
                payload={"kind": kind, "resource": resource, "effect_id": effect_id},
                published=False,
            )
            .returning(s.outbox.c.id)
        ).scalar_one()
        enqueue(
            c,
            f"publish:{outbox_id}",
            "publish",
            action_id,
            clock(c)["logical_time"],
            {"outbox_id": outbox_id, "effect_id": effect_id},
        )
    return effect_id


def seed(db, seed=7, worker_delay=100, delivery_delay=100):
    """Initialize an empty world; never reset a user's existing board implicitly."""
    if min(worker_delay, delivery_delay) < 0:
        raise ValueError("Delays must be nonnegative")
    with db.transaction() as c:
        if c.execute(select(s.runtime.c.id)).first():
            return
        c.execute(
            insert(s.runtime).values(
                id=1,
                logical_time=0,
                seed=seed,
                worker_delay=worker_delay,
                delivery_delay=delivery_delay,
                paused=False,
            )
        )
        c.execute(
            insert(s.projects).values(id="release", name="API v2 launch", completed=0, version=1)
        )
        c.execute(
            insert(s.tasks),
            [
                dict(
                    id=tid,
                    project_id="release",
                    title=title,
                    description=description,
                    reviewed=False,
                    ready=False,
                    priority="Normal",
                    assignee="Maya",
                    status="In progress",
                    version=1,
                    owners={},
                )
                for tid, title, description in [
                    (
                        "TASK-42",
                        "Refresh the integration guide",
                        "Document the API v1 integration.",
                    ),
                    (
                        "TASK-43",
                        "Publish the release",
                        "Publish after the integration guide is reviewed.",
                    ),
                ]
            ],
        )
        c.execute(insert(s.dependencies).values(task_id="TASK-43", prerequisite_id="TASK-42"))


def snapshot(db):
    with db.engine.begin() as c:
        # Consistent MVCC snapshot across all tables, including pending work.
        c.exec_driver_sql("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        return {name: rows(c, table) for name, table in s.TABLES.items()}


def patch_task(db, task_id, changes, expected_version, operation_id, action_id, actor="agent"):
    request_hash = digest([task_id, changes, expected_version, actor, action_id])
    with db.transaction() as c:
        previous = (
            c.execute(select(s.operations).where(s.operations.c.id == operation_id))
            .mappings()
            .first()
        )
        if previous:
            if previous["request_hash"] != request_hash:
                raise Conflict("Operation ID was reused for a different request")
            return previous["response"]
        before = task(c, task_id)
        if before["version"] != expected_version:
            raise Conflict(f"Expected v{expected_version}; current v{before['version']}")
        owners = {**before["owners"], **{k: action_id for k in changes}}
        after = (
            c.execute(
                update(s.tasks)
                .where(s.tasks.c.id == task_id, s.tasks.c.version == expected_version)
                .values(**changes, owners=owners, version=expected_version + 1)
                .returning(s.tasks)
            )
            .mappings()
            .one_or_none()
        )
        if after is None:
            raise Conflict("Concurrent update")
        after = dict(after)
        effect_id = emit(
            c,
            "task.updated",
            action_id,
            actor,
            task_id,
            {k: before[k] for k in changes},
            {k: after[k] for k in changes},
            publish=True,
        )
        now = clock(c)
        enqueue(
            c,
            f"workflow:{operation_id}",
            "workflow",
            action_id,
            now["logical_time"] + now["worker_delay"],
            {"task_id": task_id, "changes": changes, "effect_id": effect_id},
        )
        c.execute(
            insert(s.operations).values(
                id=operation_id, request_hash=request_hash, action_id=action_id, response=after
            )
        )
        return after


def add_comment(db, task_id, body, operation_id, actor):
    request_hash = digest(["comment", task_id, body, actor])
    with db.transaction() as c:
        task(c, task_id)
        previous = (
            c.execute(select(s.operations).where(s.operations.c.id == operation_id))
            .mappings()
            .first()
        )
        if previous:
            if previous["request_hash"] != request_hash:
                raise Conflict("Operation ID reused")
            return previous["response"]
        result = dict(id=operation_id, task_id=task_id, body=body, actor=actor, version=1)
        c.execute(insert(s.comments).values(**result))
        emit(c, "comment.created", operation_id, actor, task_id, after=result, publish=True)
        c.execute(
            insert(s.operations).values(
                id=operation_id, request_hash=request_hash, action_id=operation_id, response=result
            )
        )
        return result


def notify(c, job, message, suffix=""):
    notification_id = f"notification:{job['id']}{suffix}"
    c.execute(
        insert(s.notifications).values(
            id=notification_id, action_id=job["action_id"], message=message, version=1
        )
    )
    effect_id = emit(
        c,
        "notification.created",
        job["action_id"],
        "worker",
        notification_id,
        after={"message": message},
        parents=[job["payload"]["effect_id"]],
    )
    now = clock(c)
    enqueue(
        c,
        f"deliver:{job['id']}{suffix}",
        "deliver",
        job["action_id"],
        now["logical_time"] + now["delivery_delay"],
        {"notification_id": notification_id, "effect_id": effect_id},
        parent=job["id"],
    )


def execute_job(c, job):
    payload, action_id = job["payload"], job["action_id"]
    if job["kind"] == "publish":
        c.execute(
            update(s.outbox).where(s.outbox.c.id == payload["outbox_id"]).values(published=True)
        )
        emit(
            c,
            "outbox.published",
            action_id,
            "dispatcher",
            str(payload["outbox_id"]),
            parents=[payload["effect_id"]],
        )
    elif job["kind"] == "deliver":
        notification = (
            c.execute(
                select(s.notifications).where(s.notifications.c.id == payload["notification_id"])
            )
            .mappings()
            .one()
        )
        # This durable inbox belongs to a scripted collaborator. Receipt is irreversible
        # in this fixture's explicit contract; transport to a real human is not claimed.
        c.execute(
            insert(s.deliveries).values(
                notification_id=notification["id"],
                recipient="release-observer",
                logical_time=clock(c)["logical_time"],
                action_id=action_id,
            )
        )
        emit(
            c,
            "notification.delivered",
            action_id,
            "release-observer",
            notification["id"],
            after={"message": notification["message"]},
            parents=[payload["effect_id"]],
            irreversible=True,
            publish=True,
        )
    elif job["kind"] == "workflow":
        changes = payload["changes"]
        current = task(c, payload["task_id"])
        if "reviewed" in changes or "status" in changes:
            for dependency in c.execute(
                select(s.dependencies).where(s.dependencies.c.prerequisite_id == current["id"])
            ).mappings():
                dependent = task(c, dependency["task_id"])
                prerequisites = (
                    c.execute(
                        select(s.dependencies.c.prerequisite_id).where(
                            s.dependencies.c.task_id == dependent["id"]
                        )
                    )
                    .scalars()
                    .all()
                )
                ready = all(
                    (t := task(c, p))["reviewed"] or t["status"] == "Done" for p in prerequisites
                )
                if ready != dependent["ready"]:
                    c.execute(
                        update(s.tasks)
                        .where(
                            s.tasks.c.id == dependent["id"],
                            s.tasks.c.version == dependent["version"],
                        )
                        .values(
                            ready=ready,
                            version=dependent["version"] + 1,
                            owners={**dependent["owners"], "ready": action_id},
                        )
                    )
                    emit(
                        c,
                        "readiness.updated",
                        action_id,
                        "worker",
                        dependent["id"],
                        {"ready": dependent["ready"]},
                        {"ready": ready},
                        parents=[payload["effect_id"]],
                        publish=True,
                    )
                    if ready:
                        notify(c, job, f"{dependent['id']} is ready for release")
        if changes.get("priority") == "Critical":
            c.execute(
                insert(s.escalations).values(
                    id=f"escalation:{job['id']}",
                    task_id=current["id"],
                    action_id=action_id,
                    version=1,
                )
            )
            emit(
                c,
                "escalation.created",
                action_id,
                "worker",
                current["id"],
                after={"priority": "Critical"},
                parents=[payload["effect_id"]],
            )
            # A job can create several notices, each needs its own idempotency key.
            notify(c, job, f"{current['id']} has critical priority", ":escalation")
        if "assignee" in changes:
            notify(c, job, f"{current['id']} assigned to {changes['assignee']}", ":assignment")
        if "status" in changes:
            project = (
                c.execute(select(s.projects).where(s.projects.c.id == current["project_id"]))
                .mappings()
                .one()
            )
            completed = sum(
                t["status"] == "Done" for t in rows(c, s.tasks) if t["project_id"] == project["id"]
            )
            if completed != project["completed"]:
                c.execute(
                    update(s.projects)
                    .where(
                        s.projects.c.id == project["id"], s.projects.c.version == project["version"]
                    )
                    .values(completed=completed, version=project["version"] + 1)
                )
                emit(
                    c,
                    "summary.updated",
                    action_id,
                    "worker",
                    project["id"],
                    {"completed": project["completed"]},
                    {"completed": completed},
                    parents=[payload["effect_id"]],
                    publish=True,
                )
    else:
        raise ValueError(f"Unsupported job kind: {job['kind']}")


def advance(db, target, release_id=None, max_jobs=1000):
    """Run committed, dependency-ready work in (due, seeded tie-break) order."""
    with db.transaction() as c:
        state = clock(c)
        if target < state["logical_time"]:
            raise ValueError("Logical time cannot move backwards")
        if state["paused"] and not release_id:
            raise Conflict("Dispatcher paused; release an eligible event explicitly")
        executed = []
        while True:
            all_jobs = rows(c, s.jobs)
            done = {j["id"] for j in all_jobs if j["status"] == "done"}
            eligible = [
                j
                for j in all_jobs
                if j["status"] == "pending"
                and j["due"] <= target
                and (j["parent_id"] is None or j["parent_id"] in done)
                and (release_id is None or j["id"] == release_id)
            ]
            # Monotone publication prevents Last-Event-ID reconnects from skipping a
            # lower-ID event that would otherwise be published after a higher-ID event.
            pending_publications = [
                j["payload"]["outbox_id"]
                for j in all_jobs
                if j["kind"] == "publish" and j["status"] == "pending"
            ]
            if pending_publications:
                first_publication = min(pending_publications)
                eligible = [
                    j
                    for j in eligible
                    if j["kind"] != "publish" or j["payload"]["outbox_id"] == first_publication
                ]
            if not eligible:
                if release_id and not executed:
                    raise Conflict(
                        "Event is missing, complete, too early, or has an unmet prerequisite"
                    )
                break
            if len(executed) >= max_jobs:
                raise Conflict("Event budget exceeded; entire advancement rolled back")
            eligible.sort(key=lambda j: (j["due"], digest([state["seed"], j["id"]])))
            job = eligible[0]
            due = max(clock(c)["logical_time"], job["due"])
            c.execute(update(s.runtime).values(logical_time=due))
            execute_job(c, job)
            c.execute(update(s.jobs).where(s.jobs.c.id == job["id"]).values(status="done"))
            executed.append(job["id"])
            if release_id:
                break
        c.execute(update(s.runtime).values(logical_time=target))
        return executed


def reset_experiment(db, seed_value=7, worker_delay=100, delivery_delay=100):
    if not db.schema.startswith("ac_"):
        raise ValueError("Reset is restricted to isolated experiment schemas")
    with db.transaction() as c:
        c.exec_driver_sql("SET LOCAL afterclick.fixture_reset = 'on'")
        for table in reversed(s.metadata.sorted_tables):
            c.execute(delete(table))
        # Replay requires deterministic sequence identities as well as business rows.
        for table in (s.effects, s.outbox):
            c.exec_driver_sql(f'ALTER SEQUENCE "{table.name}_id_seq" RESTART WITH 1')
    seed(db, seed_value, worker_delay, delivery_delay)
