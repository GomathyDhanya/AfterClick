import pytest
from sqlalchemy import update

from afterclick import domain
from afterclick.infrastructure import schema as s


def test_pause_release_and_prerequisites(db):
    domain.patch_task(db, "TASK-42", {"reviewed": True}, 1, "review", "review")
    with db.transaction() as c:
        c.execute(update(s.runtime).values(paused=True))
    with pytest.raises(domain.Conflict):
        domain.advance(db, 100)
    with pytest.raises(domain.Conflict):
        domain.advance(db, 99, "workflow:review")
    domain.advance(db, 100, "workflow:review")
    with pytest.raises(domain.Conflict):
        domain.advance(db, 199, "deliver:workflow:review")
    domain.advance(db, 200, "deliver:workflow:review")
    with pytest.raises(domain.Conflict):
        domain.advance(db, 200, "deliver:workflow:review")
    with pytest.raises(ValueError):
        domain.advance(db, 0)


def test_reset_reproduces_seeded_queue_and_effects(db):
    def run():
        domain.patch_task(db, "TASK-42", {"reviewed": True}, 1, "r", "r")
        domain.advance(db, 250)
        return domain.snapshot(db)

    first = run()
    domain.reset_experiment(db)
    assert run() == first


def test_failed_dependency_never_runs(db):
    with db.transaction() as c:
        domain.enqueue(c, "parent", "workflow", "a", 100, {})
        domain.enqueue(c, "child", "deliver", "a", 0, {}, parent="parent")
        c.execute(update(s.jobs).where(s.jobs.c.id == "parent").values(status="cancelled"))
    assert domain.advance(db, 500) == []
    assert all(j["status"] != "done" for j in domain.snapshot(db)["scheduled_jobs"])


def test_outbox_publication_cannot_skip_earlier_cursor(db):
    domain.patch_task(db, "TASK-42", {"description": "API v2"}, 1, "d", "d")
    domain.patch_task(db, "TASK-42", {"reviewed": True}, 2, "r", "r")
    with pytest.raises(domain.Conflict):
        domain.advance(db, 0, "publish:2")
    domain.advance(db, 0, "publish:1")
    domain.advance(db, 0, "publish:2")
    assert all(e["published"] for e in domain.snapshot(db)["outbox_events"])
