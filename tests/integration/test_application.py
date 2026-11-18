from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import select, update

from afterclick import domain
from afterclick.control import create_control
from afterclick.infrastructure import schema as s


def patch(client, changes, version=1, op="edit"):
    return client.patch(
        "/api/tasks/TASK-42",
        json={"changes": changes, "expected_version": version, "operation_id": op},
    )


def test_commit_and_outbox_atomic_and_idempotent(client, db):
    response = patch(client, {"description": "API v2"})
    assert response.status_code == 200
    assert patch(client, {"description": "API v2"}).json() == response.json()
    state = domain.snapshot(db)
    assert len(state["effect_events"]) == len(state["outbox_events"]) == 1
    assert state["outbox_events"][0]["published"] is False
    assert len(state["scheduled_jobs"]) == 2
    assert patch(client, {"description": "different"}).status_code == 409
    assert len(domain.snapshot(db)["effect_events"]) == 1


def test_stale_write_cannot_overwrite_collaborator(client):
    assert patch(client, {"description": "human"}).status_code == 200
    assert patch(client, {"reviewed": True}, op="stale").status_code == 409
    task = client.get("/api/tasks/TASK-42").json()
    assert task["description"] == "human" and not task["reviewed"]
    assert patch(client, {"reviewed": True}, version=2, op="rebase").status_code == 200


def test_concurrent_same_version_has_single_winner(db):
    def write(i):
        try:
            domain.patch_task(db, "TASK-42", {"description": str(i)}, 1, str(i), str(i))
            return "committed"
        except domain.Conflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write, [1, 2])) == ["committed", "conflict"]
    assert len(domain.snapshot(db)["effect_events"]) == 1


def test_concurrent_duplicate_is_exactly_once(db):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: domain.patch_task(db, "TASK-42", {"reviewed": True}, 1, "same", "same"),
                range(2),
            )
        )
    assert results[0] == results[1]
    assert len(domain.snapshot(db)["effect_events"]) == 1


def test_four_workflows_and_idempotent_dispatch(client, db):
    assert (
        patch(
            client, {"reviewed": True, "priority": "Critical", "assignee": "Alex", "status": "Done"}
        ).status_code
        == 200
    )
    domain.advance(db, 100)
    state = domain.snapshot(db)
    assert state["tasks"][1]["ready"]
    assert state["projects"][0]["completed"] == 1
    assert len(state["escalations"]) == 1
    assert len(state["notifications"]) == 3
    assert not state["notification_deliveries"]
    domain.advance(db, 200)
    assert len(domain.snapshot(db)["notification_deliveries"]) == 3
    before = domain.snapshot(db)
    assert domain.advance(db, 200) == []
    assert domain.snapshot(db) == before


def test_rollback_leaves_no_partial_outbox_or_mutation(db):
    before = domain.snapshot(db)
    with pytest.raises(RuntimeError):
        with db.transaction() as c:
            c.execute(update(s.tasks).where(s.tasks.c.id == "TASK-42").values(description="bad"))
            domain.emit(c, "test", "test", "test", "TASK-42", publish=True)
            raise RuntimeError("injected transaction failure")
    assert domain.snapshot(db) == before


def test_public_api_has_no_control_routes_or_owners(client, db):
    assert client.post("/research/reset").status_code == 404
    assert "owners" not in client.get("/api/tasks/TASK-42").json()
    from fastapi.testclient import TestClient

    with TestClient(create_control(db, "test-secret")) as control:
        assert control.get("/research/state").status_code == 403
        assert (
            control.get(
                "/research/state", headers={"Authorization": "Bearer test-secret"}
            ).status_code
            == 200
        )


def test_comments_idempotency_and_receipt_preconditions(client, db):
    payload = {"body": "Looks good", "operation_id": "comment"}
    first = client.post("/api/tasks/TASK-42/comments", json=payload)
    assert first.status_code == 200
    assert client.post("/api/tasks/TASK-42/comments", json=payload).json() == first.json()
    assert client.post("/api/events/1/ack", headers={"X-Session-ID": "browser"}).status_code == 409
    domain.advance(db, 0)
    for _ in range(2):
        assert (
            client.post("/api/events/1/ack", headers={"X-Session-ID": "browser"}).status_code == 200
        )
    with db.engine.connect() as c:
        assert len(c.execute(select(s.sse_receipts)).all()) == 1


def test_database_rejects_history_rewriting(client, db):
    from sqlalchemy.exc import DBAPIError

    patch(client, {"reviewed": True})
    with pytest.raises(DBAPIError, match="append-only"):
        with db.transaction() as c:
            c.execute(update(s.effects).values(irreversible=False))
