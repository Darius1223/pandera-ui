import ast
from pathlib import Path

import pandera.pandas as pa

from pandera_ui import _extract_ast as ast_mod
from pandera_ui import _extract_runtime as rt_mod


def test_load_module_returns_none_when_spec_missing(monkeypatch, tmp_path):
    target = tmp_path / "x.py"
    target.write_text("x = 1")

    def _fake_spec_from_file_location(*args, **kwargs):
        return None

    monkeypatch.setattr(
        rt_mod.importlib.util,
        "spec_from_file_location",
        _fake_spec_from_file_location,
    )
    assert rt_mod.load_module(target, tmp_path) is None


def test_runtime_extract_skips_model_when_to_schema_raises():
    module = type("M", (), {"__name__": "m"})()

    class BadModel(pa.DataFrameModel):
        @classmethod
        def to_schema(cls):  # type: ignore[override]
            raise RuntimeError("boom")

    BadModel.__module__ = "m"
    module.BadModel = BadModel

    assert rt_mod.runtime_extract(module, Path("sample.py")) == []


def test_runtime_build_meta_extracts_index():
    schema_obj = pa.DataFrameSchema(
        columns={"x": pa.Column(int)},
        index=pa.Index(int, checks=pa.Check.greater_than(0), name="idx"),
    )
    meta = rt_mod._build_meta("s", schema_obj, "f.py", None)
    assert meta.index is not None
    assert meta.index.name == "idx"
    assert meta.index.checks[0].name == "greater_than"


def test_ast_helper_branches_for_names_and_attributes():
    assert ast_mod._is_df_schema_call(ast.parse("DataFrameSchema()", mode="eval").body)
    assert ast_mod._is_df_model(ast.parse("class A(DataFrameModel):\n    pass\n").body[0])  # type: ignore[arg-type]
    assert ast_mod._is_column_call(ast.parse("Column(int)", mode="eval").body)  # type: ignore[arg-type]
    assert ast_mod._is_field_call(ast.parse("Field(gt=1)", mode="eval").body)  # type: ignore[arg-type]


def test_ast_extract_columns_skips_non_constant_key():
    dict_node = ast.parse("{x: Column(int)}", mode="eval").body
    assert isinstance(dict_node, ast.Dict)
    assert ast_mod._extract_columns(dict_node) == []


def test_ast_parse_checks_and_parse_check_edge_cases():
    list_checks = ast.parse("[Check.isin(['a', 'b']), 123]", mode="eval").body
    checks = ast_mod._parse_checks(list_checks)
    assert len(checks) == 1
    assert checks[0].name == "isin"

    unknown = ast.parse("custom(1)", mode="eval").body
    assert isinstance(unknown, ast.Call)
    assert ast_mod._parse_check(unknown) is None

    assert ast_mod._parse_checks(ast.parse("x", mode="eval").body) == []


def test_ast_dtype_and_literal_helpers():
    assert ast_mod._dtype_node(ast.parse("'int64'", mode="eval").body) == "int64"
    assert ast_mod._dtype_node(ast.parse("int", mode="eval").body) == "int"
    assert ast_mod._dtype_node(ast.parse("pa.Int64", mode="eval").body) == "Int64"
    assert ast_mod._series_dtype(ast.parse("int", mode="eval").body) is None

    assert ast_mod._str(ast.parse("'v'", mode="eval").body) == "v"
    assert ast_mod._str(ast.parse("1", mode="eval").body, "d") == "d"
    assert ast_mod._bool(ast.parse("True", mode="eval").body) is True
    assert ast_mod._bool(ast.parse("'x'", mode="eval").body, False) is False
