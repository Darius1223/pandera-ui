from pathlib import Path

from pandera_ui.scanner import scan_project

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Runtime extraction
# ---------------------------------------------------------------------------

def test_finds_dataframe_schemas():
    schemas = scan_project(FIXTURES_DIR)
    names = {s.name for s in schemas}
    assert "orders" in names
    assert "products" in names


def test_finds_schema_models():
    schemas = scan_project(FIXTURES_DIR)
    names = {s.name for s in schemas}
    assert "users" in names
    assert "events" in names


def test_schema_model_has_source_class():
    schemas = scan_project(FIXTURES_DIR)
    users = next(s for s in schemas if s.name == "users")
    assert users.source_class == "UserSchema"


def test_column_metadata_extracted():
    schemas = scan_project(FIXTURES_DIR)
    orders = next(s for s in schemas if s.name == "orders")

    col_names = {c.name for c in orders.columns}
    assert col_names == {"order_id", "customer_id", "amount", "status", "created_at"}

    amount = next(c for c in orders.columns if c.name == "amount")
    assert amount.description == "Order total in USD"
    assert len(amount.checks) == 2


def test_checks_have_statistics():
    schemas = scan_project(FIXTURES_DIR)
    orders = next(s for s in schemas if s.name == "orders")
    order_id = next(c for c in orders.columns if c.name == "order_id")
    assert order_id.checks[0].name == "greater_than"
    assert order_id.checks[0].statistics.get("min_value") == 0


def test_coerce_flag():
    schemas = scan_project(FIXTURES_DIR)
    orders = next(s for s in schemas if s.name == "orders")
    assert orders.coerce is True


def test_runtime_source_label():
    schemas = scan_project(FIXTURES_DIR)
    for s in schemas:
        assert s.metadata_source == "runtime"


def test_empty_directory(tmp_path):
    assert scan_project(tmp_path) == []


def test_file_with_no_schemas(tmp_path):
    (tmp_path / "utils.py").write_text("def add(a, b): return a + b")
    assert scan_project(tmp_path) == []


# ---------------------------------------------------------------------------
# AST fallback
# ---------------------------------------------------------------------------

def test_ast_fallback_dataframe_schema(tmp_path):
    """Files that fail to import are still parsed via AST."""
    (tmp_path / "broken.py").write_text("""
import nonexistent_library_xyz

import pandera.pandas as pa

user_events = pa.DataFrameSchema(
    name="user_events",
    description="Events log",
    columns={
        "event_id": pa.Column(int, checks=pa.Check.greater_than(0), description="PK"),
        "name": pa.Column(str, description="Event name"),
    },
    coerce=True,
)
""")
    schemas = scan_project(tmp_path)
    assert len(schemas) == 1
    s = schemas[0]
    assert s.name == "user_events"
    assert s.description == "Events log"
    assert s.coerce is True
    assert s.metadata_source == "ast"

    col_names = {c.name for c in s.columns}
    assert col_names == {"event_id", "name"}

    event_id = next(c for c in s.columns if c.name == "event_id")
    assert event_id.dtype == "int"
    assert event_id.description == "PK"
    assert event_id.checks[0].name == "greater_than"
    assert event_id.checks[0].statistics["min_value"] == 0


def test_ast_fallback_dataframe_model(tmp_path):
    """DataFrameModel subclass in an unimportable file is found via AST."""
    (tmp_path / "broken_model.py").write_text("""
import nonexistent_xyz

import pandera.pandas as pa
from pandera.typing.pandas import Series


class ProductSchema(pa.DataFrameModel):
    sku: Series[str] = pa.Field(description="Product SKU")
    price: Series[float] = pa.Field(ge=0.0)

    class Config:
        name = "products_ast"
        description = "Product catalog"
        coerce = True
""")
    schemas = scan_project(tmp_path)
    assert len(schemas) == 1
    s = schemas[0]
    assert s.name == "products_ast"
    assert s.description == "Product catalog"
    assert s.coerce is True
    assert s.source_class == "ProductSchema"
    assert s.metadata_source == "ast"

    col_names = {c.name for c in s.columns}
    assert col_names == {"sku", "price"}

    price = next(c for c in s.columns if c.name == "price")
    assert price.dtype == "float"
    assert price.checks[0].name == "greater_than_or_equal_to"
    assert price.checks[0].statistics["min_value"] == 0.0

    sku = next(c for c in s.columns if c.name == "sku")
    assert sku.description == "Product SKU"


def test_ast_fallback_syntax_error_skipped(tmp_path):
    """Files with syntax errors are silently skipped."""
    (tmp_path / "broken_syntax.py").write_text("def oops(:\n    pass")
    assert scan_project(tmp_path) == []


def test_skips_venv(tmp_path):
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "schema.py").write_text("""
import pandera.pandas as pa
hidden = pa.DataFrameSchema(name="hidden", columns={})
""")
    assert scan_project(tmp_path) == []
