import asyncio

import httpx
import pytest
from playwright.async_api import async_playwright, expect

from afterclick import domain

pytestmark = pytest.mark.browser


def test_delayed_ack_stays_pending_after_real_commit(origin, db):
    async def scenario():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            committed = asyncio.Event()
            release = asyncio.Event()

            async def hold(route):
                if route.request.method == "PATCH":
                    response = await route.fetch()
                    assert response.status == 200
                    committed.set()
                    await release.wait()
                    await route.fulfill(response=response)
                else:
                    await route.continue_()

            await page.route("**/api/tasks/TASK-42", hold)
            await page.goto(origin)
            await page.get_by_label("Description", exact=True).fill(
                "API v2 delayed acknowledgement"
            )
            await asyncio.wait_for(committed.wait(), timeout=5)
            await expect(page.get_by_role("status")).to_have_text("Saving")
            assert domain.snapshot(db)["tasks"][0]["version"] == 2
            assert len(domain.snapshot(db)["effect_events"]) == 1
            release.set()
            await expect(page.get_by_role("status")).to_have_text("✓ Committed")
            await browser.close()

    asyncio.run(scenario())


def test_sse_reconnect_resumes_after_confirmed_cursor(origin, db):
    domain.patch_task(db, "TASK-42", {"description": "API v2"}, 1, "one", "one")
    domain.patch_task(db, "TASK-42", {"reviewed": True}, 2, "two", "two")
    domain.advance(db, 0)
    with httpx.stream(
        "GET", origin + "/api/events", headers={"Last-Event-ID": "1"}, timeout=5
    ) as stream:
        assert stream.status_code == 200
        for line in stream.iter_lines():
            if line.startswith("id:"):
                assert line == "id: 2"
                break


def test_late_refresh_cannot_regress_committed_task_version(origin, db):
    async def scenario():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(origin)
            await expect(page.get_by_label("Description", exact=True)).to_be_visible()
            captured, release = asyncio.Event(), asyncio.Event()
            held = False

            async def hold_first(route):
                nonlocal held
                if not held:
                    held = True
                    response = await route.fetch()
                    captured.set()
                    await release.wait()
                    await route.fulfill(
                        response=response, headers={**response.headers, "x-stale-test": "1"}
                    )
                else:
                    await route.continue_()

            await page.route("**/api/projects/release/tasks", hold_first)
            domain.patch_task(db, "TASK-42", {"description": "API v2 older"}, 1, "one", "one")
            domain.advance(db, 0)
            await asyncio.wait_for(captured.wait(), timeout=5)
            domain.patch_task(db, "TASK-42", {"description": "API v2 latest"}, 2, "two", "two")
            domain.advance(db, 0)
            await expect(page.get_by_label("Description", exact=True)).to_have_value(
                "API v2 latest"
            )
            async with page.expect_response(lambda r: r.headers.get("x-stale-test") == "1") as info:
                release.set()
            response = await info.value
            await response.finished()
            # Flush the browser render cycle after the deliberately delayed response.
            await page.evaluate(
                "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
            )
            await expect(page.get_by_text("Version 3", exact=True)).to_be_visible()
            await expect(page.get_by_label("Description", exact=True)).to_have_value(
                "API v2 latest"
            )
            await browser.close()

    asyncio.run(scenario())
