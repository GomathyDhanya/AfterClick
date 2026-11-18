from datetime import datetime, timezone

import pytest
from playwright.sync_api import expect

from afterclick import domain
from afterclick.agent.gateway import Action, Gateway

pytestmark = pytest.mark.browser


def open_page(browser, origin):
    context = browser.new_context()
    page = context.new_page()
    instant = datetime(2026, 1, 1, tzinfo=timezone.utc)
    page.clock.install(time=instant)
    page.clock.pause_at(instant)
    page.goto(origin)
    expect(page.get_by_label("Description", exact=True)).to_be_visible()
    expect(page.get_by_text("Live updates", exact=True)).to_be_visible()
    return context, page


def save(page):
    page.clock.fast_forward(600)
    expect(page.get_by_role("status")).to_have_text("✓ Committed")


def test_debounce_and_two_session_sse(browser, origin, db):
    context, first = open_page(browser, origin)
    other, second = open_page(browser, origin)
    first.get_by_label("Description", exact=True).fill("Document API v2.")
    first.clock.fast_forward(599)
    assert domain.snapshot(db)["tasks"][0]["version"] == 1
    first.clock.fast_forward(1)
    expect(first.get_by_role("status")).to_have_text("✓ Committed")
    domain.advance(db, 0)
    expect(second.get_by_label("Description", exact=True)).to_have_value("Document API v2.")
    # Browser ack is a barrier for confirmed receipt, separate from server publication.
    expect(second.get_by_text("Version 2", exact=True)).to_be_visible()
    first.screenshot(path="artifacts/flowboard-desktop.png", full_page=True)
    first.set_viewport_size({"width": 390, "height": 844})
    first.screenshot(path="artifacts/flowboard-mobile.png", full_page=True)
    context.close()
    other.close()


def test_lost_ack_retry_does_not_duplicate_mutation(browser, origin, db):
    context, page = open_page(browser, origin)
    dropped = []

    def drop_once(route):
        if route.request.method == "PATCH" and not dropped:
            response = route.fetch()
            assert response.status == 200  # backend committed, but browser sees failed response
            dropped.append(True)
            route.abort("failed")
        else:
            route.continue_()

    page.route("**/api/tasks/TASK-42", drop_once)
    page.get_by_label("Description", exact=True).fill("API v2 after lost acknowledgement")
    page.clock.fast_forward(600)
    expect(page.get_by_role("status")).to_have_text("Failed")
    assert domain.snapshot(db)["tasks"][0]["version"] == 2
    page.get_by_role("button", name="Retry save").click()
    expect(page.get_by_role("status")).to_have_text("✓ Committed")
    assert domain.snapshot(db)["tasks"][0]["version"] == 2
    assert len(domain.snapshot(db)["effect_events"]) == 1
    context.close()


@pytest.mark.parametrize("overlap", [False, True])
def test_concurrent_edits_rebase_or_conflict(browser, origin, db, overlap):
    context, first = open_page(browser, origin)
    other, second = open_page(browser, origin)
    first.get_by_label("Description", exact=True).fill("API v2 from first")
    if overlap:
        second.get_by_label("Description", exact=True).fill("Human independent draft")
    else:
        second.get_by_label("Priority", exact=True).select_option("High")
    save(first)
    second.clock.fast_forward(600)
    if overlap:
        expect(second.get_by_role("status")).to_have_text("Conflict")
        expect(second.get_by_label("Description", exact=True)).to_have_value(
            "Human independent draft"
        )
        assert domain.snapshot(db)["tasks"][0]["description"] == "API v2 from first"
    else:
        expect(second.get_by_role("status")).to_have_text("✓ Committed")
        state = domain.snapshot(db)["tasks"][0]
        assert state["description"] == "API v2 from first" and state["priority"] == "High"
    context.close()
    other.close()


def test_gateway_records_browser_actions_and_commit_provenance(browser, origin, db):
    context = browser.new_context()
    page = context.new_page()
    gateway = Gateway(page, origin)
    gateway.act(Action("navigate", "/"))
    gateway.act(Action("fill", "Description", "API v2 from the scripted agent"))
    gateway.act(Action("wait", "✓ Committed"))
    effects = domain.snapshot(db)["effect_events"]
    assert len(effects) == 1
    assert effects[0]["action_id"] == "a0002"
    assert all(h["feedback"]["status"] == "completed" for h in gateway.history)
    context.close()
