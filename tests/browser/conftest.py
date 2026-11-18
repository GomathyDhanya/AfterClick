import pytest
from playwright.sync_api import sync_playwright

from afterclick.replay.server import serve


@pytest.fixture
def origin(db):
    with serve(db) as origin:
        yield origin


@pytest.fixture
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()
