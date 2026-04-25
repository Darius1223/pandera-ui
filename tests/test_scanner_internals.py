import ast
from pathlib import Path

import pandera.pandas as pa

from pandera_ui import scanner


def test_load_module_returns_none_when_spec_missing(monkeypatch, tmp_path):
    target = tmp_path / "x.py"
    target.write_text("x = 1")

    def _fake_spec_from_file_location(*args, **kwargs):
        return None

    monkeypatch.setattr(
        scanner.importlib.util,
        "spec_from_file_location",
        _fake_spec_from_file_location,
    )
    assert scanner._load_module(target, tmp_path) is None


def test_runtime_extract_skips_model_when_to_schema_raises():
    module = type("M", (), {"__name__": "m"})()

    class BadModel(pa.DataFrameModel):
        @classmethod
        def to_schema(cls):  # type: ignore[override]
            raise RuntimeError("boom")

    BadModel.__module__ = "m"
    module.BadModel = BadModel

    assert scanner._runtime_extract(module, Path("sample.py")) == []


def test_runtime_build_meta_extracts_index():
    schema_obj = pa.DataFrameSchema(
        columns={"x": pa.Column(int)},
        index=pa.Index(int, checks=pa.Check.greater_than(0), name="idx"),
    )
    meta = scanner._runtime_build_meta("s", schema_obj, "f.py", None)
    assert meta.index is not None
    assert meta.index.name == "idx"
    assert meta.index.checks[0].name == "greater_than"


def test_ast_helper_branches_for_names_and_attributes():
    assert scanner._ast_is_df_schema_call(ast.parse("DataFrameSchema()", mode="eval").body)
    assert scanner._ast_is_df_model(ast.parse("class A(DataFrameModel):\n    pass\n").body[0])  # type: ignore[arg-type]
    assert scanner._ast_is_column_call(ast.parse("Column(int)", mode="eval").body)  # type: ignore[arg-type]
    assert scanner._ast_is_field_call(ast.parse("Field(gt=1)", mode="eval").body)  # type: ignore[arg-type]


def test_ast_extract_columns_skips_non_constant_key():
    dict_node = ast.parse("{x: Column(int)}", mode="eval").body
    assert isinstance(dict_node, ast.Dict)
    assert scanner._ast_extract_columns(dict_node) == []


def test_ast_parse_checks_and_parse_check_edge_cases():
    list_checks = ast.parse("[Check.isin(['a', 'b']), 123]", mode="eval").body
    checks = scanner._ast_parse_checks(list_checks)
    assert len(checks) == 1
    assert checks[0].name == "isin"

    unknown = ast.parse("custom(1)", mode="eval").body
    assert isinstance(unknown, ast.Call)
    assert scanner._ast_parse_check(unknown) is None

    assert scanner._ast_parse_checks(ast.parse("x", mode="eval").body) == []


def test_ast_dtype_and_literal_helpers():
    assert scanner._ast_dtype_node(ast.parse("'int64'", mode="eval").body) == "int64"
    assert scanner._ast_dtype_node(ast.parse("int", mode="eval").body) == "int"
    assert scanner._ast_dtype_node(ast.parse("pa.Int64", mode="eval").body) == "Int64"
    assert scanner._ast_series_dtype(ast.parse("int", mode="eval").body) is None

    assert scanner._ast_str(ast.parse("'v'", mode="eval").body) == "v"
    assert scanner._ast_str(ast.parse("1", mode="eval").body, "d") == "d"
    assert scanner._ast_bool(ast.parse("True", mode="eval").body) is True
    assert scanner._ast_bool(ast.parse("'x'", mode="eval").body, False) is False

