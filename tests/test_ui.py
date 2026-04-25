"""Playwright end-to-end tests for the pandera-ui frontend."""

import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
from playwright.sync_api import Page, expect

import pandera_ui.server as srv
from pandera_ui.server import app

FIXTURES = Path(__file__).parent / "fixtures"
PORT = 18765


@pytest.fixture(scope="session")
def live_server():
    """Start uvicorn in a daemon thread, yield base URL, then shut down."""
    srv.load_schemas(str(FIXTURES))
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Poll until ready (up to 3 s)
    for _ in range(30):
        try:
            httpx.get(f"http://127.0.0.1:{PORT}/", timeout=1)
            break
        except Exception:
            time.sleep(0.1)

    yield f"http://127.0.0.1:{PORT}"
    server.should_exit = True
    thread.join(timeout=5)


def test_page_loads(page: Page, live_server):
    page.goto(live_server)
    expect(page.locator("#schema-list")).to_be_visible()


def test_schemas_appear_in_sidebar(page: Page, live_server):
    page.goto(live_server)
    expect(page.locator(".schema-item").first).to_be_visible()


def test_schema_count_in_header(page: Page, live_server):
    page.goto(live_server)
    count_text = page.locator("#count").inner_text()
    assert "schema" in count_text.lower() or any(c.isdigit() for c in count_text)


def test_schema_selection_shows_detail(page: Page, live_server):
    page.goto(live_server)
    page.locator(".schema-item").first.click()
    expect(page.locator(".schema-header h2")).to_be_visible()


def test_schema_detail_has_columns_table(page: Page, live_server):
    page.goto(live_server)
    page.locator(".schema-item").first.click()
    expect(page.locator("table")).to_be_visible()


def test_language_switch_to_ru(page: Page, live_server):
    page.goto(live_server)
    page.locator(".schema-item").first.click()
    page.click('[data-lang="ru"]')
    expect(page.locator("th", has_text="Название")).to_be_visible()


def test_language_switch_to_fr(page: Page, live_server):
    page.goto(live_server)
    page.locator(".schema-item").first.click()
    page.click('[data-lang="fr"]')
    expect(page.locator("th", has_text="Nom")).to_be_visible()


def test_language_switch_to_de(page: Page, live_server):
    page.goto(live_server)
    page.locator(".schema-item").first.click()
    page.click('[data-lang="de"]')
    expect(page.locator("th", has_text="Typ")).to_be_visible()


def test_theme_toggle_changes_attribute(page: Page, live_server):
    page.goto(live_server)
    before = page.evaluate("document.documentElement.dataset.theme || 'dark'")
    page.click("#theme-toggle")
    after = page.evaluate("document.documentElement.dataset.theme || 'dark'")
    assert before != after


def test_theme_persists_after_reload(page: Page, live_server):
    page.goto(live_server)
    page.click("#theme-toggle")
    theme_after_toggle = page.evaluate("document.documentElement.dataset.theme || 'dark'")
    page.reload()
    theme_after_reload = page.evaluate("document.documentElement.dataset.theme || 'dark'")
    assert theme_after_toggle == theme_after_reload


def test_type_filter_dataframemodel(page: Page, live_server):
    page.goto(live_server)
    page.click('[data-val="DataFrameModel"]')
    items = page.locator(".schema-item").all()
    assert len(items) > 0
    for item in items:
        expect(item.locator(".dot")).to_have_class("dot model")


def test_type_filter_dataframeschema(page: Page, live_server):
    page.goto(live_server)
    page.click('[data-val="DataFrameSchema"]')
    items = page.locator(".schema-item").all()
    assert len(items) > 0
    for item in items:
        dot = item.locator(".dot")
        # DataFrameSchema items have dot without "model" class
        classes = dot.get_attribute("class")
        assert "model" not in classes


def test_type_filter_all_restores(page: Page, live_server):
    page.goto(live_server)
    total = page.locator(".schema-item").count()
    page.click('[data-val="DataFrameModel"]')
    page.click('[data-val="all"]')
    assert page.locator(".schema-item").count() == total


def test_search_filters_sidebar(page: Page, live_server):
    page.goto(live_server)
    total = page.locator(".schema-item").count()
    page.fill("#search", "orders")
    assert page.locator(".schema-item").count() < total
    assert page.locator(".schema-item").count() >= 1


def test_search_clear_restores(page: Page, live_server):
    page.goto(live_server)
    total = page.locator(".schema-item").count()
    page.fill("#search", "orders")
    page.fill("#search", "")
    assert page.locator(".schema-item").count() == total


def test_sort_name_desc_changes_order(page: Page, live_server):
    page.goto(live_server)
    page.select_option("#sort-select", "name-asc")
    asc = [page.locator(".schema-item").nth(i).inner_text()
           for i in range(page.locator(".schema-item").count())]
    page.select_option("#sort-select", "name-desc")
    desc = [page.locator(".schema-item").nth(i).inner_text()
            for i in range(page.locator(".schema-item").count())]
    # Schemas grouped by file, so A→Z and Z→A are not exact reverses,
    # but the overall set must differ when there are multiple schemas.
    assert set(asc) == set(desc)  # same schemas
    assert asc != desc             # different order


def test_filter_bar_visible(page: Page, live_server):
    page.goto(live_server)
    expect(page.locator("#filter-bar")).to_be_visible()


def test_filter_labels_translate_with_lang(page: Page, live_server):
    page.goto(live_server)
    page.click('[data-lang="ru"]')
    # Russian label for "Type" filter
    expect(page.locator(".filter-label", has_text="Тип")).to_be_visible()
