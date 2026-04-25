from pathlib import Path
import pandera_ui.server as srv
from pandera_ui.scanner import scan_project

FIXTURES = Path(__file__).parent / "fixtures"


def test_private_var_skipped(tmp_path):
    (tmp_path / "private.py").write_text("""
import pandera.pandas as pa
_hidden = pa.DataFrameSchema(name="hidden", columns={})
""")
    assert scan_project(tmp_path) == []


def test_to_schema_exception_skipped(tmp_path):
    """If to_schema() raises, the schema is silently skipped — scan must not crash."""
    (tmp_path / "bad.py").write_text("""
import pandera.pandas as pa
from pandera.typing.pandas import Series

class BrokenModel(pa.DataFrameModel):
    class Config:
        name = "broken"
""")
    schemas = scan_project(tmp_path)
    assert isinstance(schemas, list)


def test_deduplication(tmp_path):
    """Two names bound to the same DataFrameSchema object → only one schema."""
    (tmp_path / "dup.py").write_text("""
import pandera.pandas as pa
base = pa.DataFrameSchema(name="base", columns={})
alias = base
""")
    schemas = scan_project(tmp_path)
    assert len(schemas) == 1
    assert schemas[0].name == "base"


def test_non_serializable_check_stats(tmp_path):
    """Lambda-based custom checks must not raise during stat serialisation."""
    (tmp_path / "custom.py").write_text("""
import pandera.pandas as pa
schema = pa.DataFrameSchema(
    name="custom",
    columns={"val": pa.Column(int, checks=pa.Check(lambda x: x > 0, name="custom_fn"))}
)
""")
    schemas = scan_project(tmp_path)
    assert len(schemas) == 1


def test_ast_multi_assign_skipped(tmp_path):
    """Tuple-target assignment (a, b = ...) is not extracted by AST fallback."""
    (tmp_path / "multi.py").write_text("""
import nonexistent_dep
import pandera.pandas as pa
a, b = None, pa.DataFrameSchema(name="x", columns={})
""")
    schemas = scan_project(tmp_path)
    assert schemas == []


def test_ast_missing_config(tmp_path):
    """DataFrameModel without Config defaults name to the class name."""
    (tmp_path / "no_config.py").write_text("""
import nonexistent_dep
import pandera.pandas as pa
from pandera.typing.pandas import Series

class NoConfig(pa.DataFrameModel):
    x: Series[int]
""")
    schemas = scan_project(tmp_path)
    assert len(schemas) == 1
    assert schemas[0].name == "NoConfig"
    assert schemas[0].metadata_source == "ast"


def test_ast_empty_columns_dict(tmp_path):
    """DataFrameSchema with empty columns dict produces a schema with no columns."""
    (tmp_path / "empty.py").write_text("""
import nonexistent_dep
import pandera.pandas as pa
empty = pa.DataFrameSchema(name="empty", columns={})
""")
    schemas = scan_project(tmp_path)
    assert len(schemas) == 1
    assert schemas[0].columns == []


def test_module_name_mismatch_no_duplicate():
    """DataFrameModel imported into another module must not be double-counted."""
    schemas = scan_project(FIXTURES)
    user_schemas = [s for s in schemas if s.source_class == "UserSchema"]
    assert len(user_schemas) == 1


def test_server_multiple_load_calls(tmp_path):
    """load_schemas() called twice returns the same count — idempotent."""
    (tmp_path / "s.py").write_text("""
import pandera.pandas as pa
s = pa.DataFrameSchema(name="s", columns={})
""")
    srv.load_schemas(str(tmp_path))
    first = len(srv._schemas)
    srv.load_schemas(str(tmp_path))
    second = len(srv._schemas)
    assert first == second == 1


def test_server_nonexistent_path():
    """Scanning a missing path returns an empty schema list."""
    srv.load_schemas("/tmp/nonexistent_pandera_ui_xyz_999")
    assert srv._schemas == []


def test_ast_column_with_list_checks(tmp_path):
    """Column with a list of checks is extracted correctly via AST."""
    (tmp_path / "list_checks.py").write_text("""
import nonexistent_dep
import pandera.pandas as pa
schema = pa.DataFrameSchema(
    name="checks",
    columns={
        "amount": pa.Column(
            float,
            checks=[pa.Check.greater_than_or_equal_to(0), pa.Check.less_than(1000)],
        )
    },
)
""")
    schemas = scan_project(tmp_path)
    assert len(schemas) == 1
    col = schemas[0].columns[0]
    assert len(col.checks) == 2
    check_names = {c.name for c in col.checks}
    assert "greater_than_or_equal_to" in check_names
    assert "less_than" in check_names


def test_ast_field_isin(tmp_path):
    """DataFrameModel Field with isin list is extracted via AST."""
    (tmp_path / "isin.py").write_text("""
import nonexistent_dep
import pandera.pandas as pa
from pandera.typing.pandas import Series

class StatusSchema(pa.DataFrameModel):
    status: Series[str] = pa.Field(isin=["active", "inactive"])
    class Config:
        name = "status"
""")
    schemas = scan_project(tmp_path)
    assert len(schemas) == 1
    col = schemas[0].columns[0]
    assert col.checks[0].name == "isin"
