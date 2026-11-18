from concurrent.futures import ThreadPoolExecutor

import pytest

from afterclick import domain
from afterclick.recovery.planner import compensate_review


def test_same_value_write_changes_only_touched_token_and_does_not_expose_owner(client):
    initial = client.get("/api/tasks/TASK-42").json()
    result = client.patch(
        "/api/tasks/TASK-42",
        json={
            "expected_version": 1,
            "operation_id": "same",
            "changes": {"description": initial["description"]},
            "expected_field_revisions": {"description": 1},
        },
    )
    assert result.status_code == 200
    current = result.json()
    assert current["description"] == initial["description"]
    assert current["field_revisions"]["description"] == 2
    assert current["field_revisions"]["priority"] == 1
    assert "owners" not in current and "owners" not in client.get("/api/projects").json()[0]
    rejected = client.patch(
        "/api/tasks/TASK-42",
        json={
            "expected_version": 2,
            "operation_id": "stale-token",
            "changes": {"description": "overwrite"},
            "expected_field_revisions": {"description": 1},
        },
    )
    assert rejected.status_code == 409  # even a fresh record version cannot bypass stale field CAS


@pytest.mark.parametrize("overlap", [True, False])
def test_atomic_field_cas_with_concurrent_writers(db, overlap):
    def write(i):
        field = "description" if i == 0 or overlap else "priority"
        value = f"API v2 {i}" if field == "description" else "High"
        try:
            domain.patch_task(
                db,
                "TASK-42",
                {field: value},
                1,
                f"op{i}",
                f"a{i}",
                expected_field_revisions={field: 1},
            )
            return "committed"
        except domain.Conflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = sorted(pool.map(write, [0, 1]))
    assert results == (["committed", "conflict"] if overlap else ["committed", "committed"])


def test_same_value_aba_and_cas_retry_identity(db):
    initial = domain.snapshot(db)["tasks"][0]
    for version, value in [(1, "temporary"), (2, initial["description"])]:
        domain.patch_task(
            db, "TASK-42", {"description": value}, version, f"human{version}", f"human{version}"
        )
    with pytest.raises(domain.Conflict):
        domain.patch_task(
            db,
            "TASK-42",
            {"description": "draft"},
            1,
            "stale",
            "stale",
            expected_field_revisions={"description": 1},
        )
    args = (db, "TASK-42", {"priority": "High"}, 1, "safe", "safe")
    result = domain.patch_task(*args, expected_field_revisions={"priority": 1})
    assert domain.patch_task(*args, expected_field_revisions={"priority": 1}) == result
    with pytest.raises(domain.Conflict):
        domain.patch_task(*args, expected_field_revisions={"priority": 2})


@pytest.mark.parametrize(
    "tokens",
    [
        {},
        {"priority": 1},
        {"description": True},
        {"description": 1, "priority": 1},
        {"description": 0},
    ],
)
def test_incomplete_or_invalid_tokens_fail_closed(client, tokens):
    response = client.patch(
        "/api/tasks/TASK-42",
        json={
            "expected_version": 1,
            "operation_id": "bad",
            "changes": {"description": "draft"},
            "expected_field_revisions": tokens,
        },
    )
    assert response.status_code == 422
    assert client.get("/api/tasks/TASK-42").json()["version"] == 1


def test_worker_and_recovery_advance_field_tokens(db):
    domain.patch_task(db, "TASK-42", {"reviewed": True}, 1, "review", "review")
    domain.advance(db, 150)
    before = domain.snapshot(db)
    assert before["tasks"][1]["field_revisions"]["ready"] == 2
    assert compensate_review(db, "review")["status"] == "APPLIED"
    after = domain.snapshot(db)
    assert after["tasks"][0]["field_revisions"]["reviewed"] == 3
    assert after["tasks"][1]["field_revisions"]["ready"] == 3


def test_migration_backfills_existing_records_without_rewriting_business_values(db):
    from alembic import command
    from alembic.config import Config

    with db.engine.begin() as c:
        config = Config("alembic.ini")
        config.attributes["connection"] = c
        command.downgrade(config, "0002")
        c.exec_driver_sql("UPDATE tasks SET description = 'Existing legitimate edit', version = 7")
        c.exec_driver_sql("UPDATE projects SET completed = 1, version = 4")
        command.upgrade(config, "head")
    state = domain.snapshot(db)
    assert state["tasks"][0]["description"] == "Existing legitimate edit"
    assert set(state["tasks"][0]["field_revisions"].values()) == {7}
    assert state["projects"][0]["completed"] == 1
    assert state["projects"][0]["field_revisions"] == {"name": 4, "completed": 4}
