from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import pandera_ui.server as srv
from pandera_ui.server import app

FIXTURES = Path(__file__).parent / "fixtures"
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_server():
    srv._schemas = []
    yield
    srv._schemas = []


def test_schemas_empty():
    assert client.get("/api/schemas").json() == []


def test_schemas_status_code():
    assert client.get("/api/schemas").status_code == 200


def test_schemas_after_load():
    srv.load_schemas(str(FIXTURES))
    data = client.get("/api/schemas").json()
    assert len(data) > 0
    names = {s["name"] for s in data}
    assert "orders" in names
    assert "users" in names


def test_schema_structure():
    srv.load_schemas(str(FIXTURES))
    s = client.get("/api/schemas").json()[0]
    for key in ("name", "var_name", "file_path", "columns", "metadata_source", "coerce"):
        assert key in s


def test_schema_column_structure():
    srv.load_schemas(str(FIXTURES))
    schemas = client.get("/api/schemas").json()
    orders = next(s for s in schemas if s["name"] == "orders")
    col = orders["columns"][0]
    for key in ("name", "dtype", "nullable", "required", "checks"):
        assert key in col


def test_metadata_source_values():
    srv.load_schemas(str(FIXTURES))
    data = client.get("/api/schemas").json()
    for s in data:
        assert s["metadata_source"] in ("runtime", "ast")


def test_index_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_index_contains_key_elements():
    body = client.get("/").text
    for element_id in ("lang-selector", "schema-list", "filter-bar", "theme-toggle", "sort-select"):
        assert element_id in body, f"missing element: #{element_id}"


def test_index_contains_all_languages():
    body = client.get("/").text
    for lang in ("en", "ru", "fr", "de"):
        assert f'data-lang="{lang}"' in body


def test_index_translations_present():
    body = client.get("/").text
    for phrase in ("Поиск схем", "Filtrer les", "Schemata filtern"):
        assert phrase in body, f"missing translation: {phrase!r}"


def test_index_pandera_ui_title():
    assert "Pandera UI" in client.get("/").text
