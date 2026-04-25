"""Schema discovery and metadata extraction for Pandera schemas.

Two-pass strategy per file:
1. Runtime import — accurate, handles dynamic schemas.
2. AST fallback   — safe static parse when import fails (missing deps, side-effects).
"""

import ast
import importlib.util
import sys
import types
from pathlib import Path
from typing import Optional

import pandera.pandas as pa

from .models import CheckMetadata, ColumnMetadata, IndexMetadata, SchemaMetadata

_SKIP_DIRS = {
    ".venv", "venv", ".env", "__pycache__", ".git",
    "node_modules", ".tox", "dist", "build", "site-packages",
}

# Maps DataFrameModel Field kwargs to (check_name, statistic_key)
_FIELD_CHECK_MAP: dict[str, tuple[str, str]] = {
    "gt": ("greater_than", "min_value"),
    "ge": ("greater_than_or_equal_to", "min_value"),
    "lt": ("less_than", "max_value"),
    "le": ("less_than_or_equal_to", "max_value"),
    "eq": ("equal_to", "value"),
    "ne": ("not_equal_to", "value"),
    "isin": ("isin", "allowed_values"),
    "notin": ("notin", "forbidden_values"),
    "str_matches": ("str_matches", "pattern"),
    "str_contains": ("str_contains", "string"),
    "str_startswith": ("str_startswith", "string"),
    "str_endswith": ("str_endswith", "string"),
}

# Maps Check method names to their primary statistics key
_CHECK_STAT_MAP: dict[str, str] = {
    "greater_than": "min_value",
    "greater_than_or_equal_to": "min_value",
    "less_than": "max_value",
    "less_than_or_equal_to": "max_value",
    "equal_to": "value",
    "not_equal_to": "value",
    "isin": "allowed_values",
    "notin": "forbidden_values",
    "str_matches": "pattern",
    "str_contains": "string",
    "str_startswith": "string",
    "str_endswith": "string",
    "in_range": "min_value",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_project(project_path: str | Path) -> list[SchemaMetadata]:
    """Walk *project_path* and return metadata for every Pandera schema found.

    Each ``.py`` file is first imported at runtime for full accuracy.
    If the import fails (missing dependency, side-effects, etc.) the file is
    re-processed with a static AST parser as a safe fallback.  AST-derived
    schemas are marked ``metadata_source="ast"``.

    Directories named ``.venv``, ``venv``, ``__pycache__``, ``.git``,
    ``node_modules``, ``dist``, and ``build`` are skipped automatically.
    """
    root = Path(project_path).resolve()
    results: list[SchemaMetadata] = []
    seen_ids: set[int] = set()

    for py_file in sorted(root.rglob("*.py")):
        if any(part in _SKIP_DIRS for part in py_file.parts):
            continue

        relative = py_file.relative_to(root)
        schemas = _scan_file(py_file, root, relative)

        for schema in schemas:
            obj_id = id(schema)
            if obj_id not in seen_ids:
                seen_ids.add(obj_id)
                results.append(schema)

    return results


# ---------------------------------------------------------------------------
# File-level dispatch
# ---------------------------------------------------------------------------

def _scan_file(path: Path, root: Path, relative: Path) -> list[SchemaMetadata]:
    """Try runtime import first; fall back to AST on failure."""
    module = _load_module(path, root)
    if module is not None:
        schemas = _runtime_extract(module, relative)
        for s in schemas:
            s.metadata_source = "runtime"
        return schemas

    schemas = _ast_extract(path, relative)
    for s in schemas:
        s.metadata_source = "ast"
    return schemas


# ---------------------------------------------------------------------------
# Runtime extraction
# ---------------------------------------------------------------------------

def _load_module(path: Path, root: Path) -> types.ModuleType | None:
    root_str = str(root)
    added = root_str not in sys.path
    if added:
        sys.path.insert(0, root_str)

    module_name = "_pandera_ui_scan_" + path.stem + "_" + str(abs(hash(str(path))))
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module
    except Exception:
        return None
    finally:
        if added and root_str in sys.path:
            sys.path.remove(root_str)


def _runtime_extract(module: types.ModuleType, relative: Path) -> list[SchemaMetadata]:
    """Inspect a loaded module and return metadata for all Pandera schemas."""
    results = []
    seen_schema_ids: set[int] = set()  # deduplicate aliases (alias = original)

    for var_name, obj in vars(module).items():
        if var_name.startswith("_"):
            continue

        df_schema: Optional[pa.DataFrameSchema] = None
        source_class: Optional[str] = None

        if isinstance(obj, pa.DataFrameSchema):
            df_schema = obj
        elif (
            isinstance(obj, type)
            and issubclass(obj, pa.DataFrameModel)
            and obj is not pa.DataFrameModel
            and obj.__module__ == module.__name__
        ):
            try:
                df_schema = obj.to_schema()
                source_class = obj.__name__
            except Exception:
                continue

        if df_schema is not None:
            sid = id(df_schema)
            if sid in seen_schema_ids:
                continue
            seen_schema_ids.add(sid)
            results.append(_runtime_build_meta(var_name, df_schema, str(relative), source_class))

    return results


def _runtime_build_meta(
    var_name: str,
    schema: pa.DataFrameSchema,
    file_path: str,
    source_class: Optional[str],
) -> SchemaMetadata:
    columns = [_runtime_build_column(n, c) for n, c in schema.columns.items()]

    index_meta: Optional[IndexMetadata] = None
    if schema.index is not None:
        idx = schema.index
        index_meta = IndexMetadata(
            name=getattr(idx, "name", None),
            dtype=str(idx.dtype) if getattr(idx, "dtype", None) else None,
            nullable=getattr(idx, "nullable", False),
            checks=[_runtime_build_check(c) for c in getattr(idx, "checks", [])],
        )

    return SchemaMetadata(
        name=schema.name or source_class or var_name,
        var_name=var_name,
        file_path=file_path,
        source_class=source_class,
        title=getattr(schema, "title", None),
        description=getattr(schema, "description", None),
        coerce=schema.coerce,
        columns=columns,
        index=index_meta,
    )


def _runtime_build_column(col_name: str, col: pa.Column) -> ColumnMetadata:
    return ColumnMetadata(
        name=col_name,
        dtype=str(col.dtype) if col.dtype is not None else None,
        nullable=col.nullable,
        required=col.required,
        checks=[_runtime_build_check(c) for c in col.checks],
        title=getattr(col, "title", None),
        description=getattr(col, "description", None),
    )


def _runtime_build_check(check: pa.Check) -> CheckMetadata:
    stats = check.statistics or {}
    safe = {
        k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v))
        for k, v in stats.items()
    }
    return CheckMetadata(
        name=check.name or "custom",
        statistics=safe,
        description=getattr(check, "description", None),
        error=getattr(check, "error", None),
    )


# ---------------------------------------------------------------------------
# AST extraction (fallback)
# ---------------------------------------------------------------------------

def _ast_extract(path: Path, relative: Path) -> list[SchemaMetadata]:
    """Parse *path* with the AST module and extract schema metadata without importing.

    Only literal values are extracted; dynamic expressions (function calls,
    variable references) are silently skipped.
    """
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    results: list[SchemaMetadata] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _ast_is_df_schema_call(node.value):
                    meta = _ast_build_from_call(target.id, node.value, str(relative))  # type: ignore[arg-type]
                    if meta:
                        results.append(meta)

        elif isinstance(node, ast.ClassDef) and _ast_is_df_model(node):
            meta = _ast_build_from_class(node, str(relative))
            if meta:
                results.append(meta)

    return results


def _ast_is_df_schema_call(node: ast.expr) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "DataFrameSchema"
    if isinstance(func, ast.Name):
        return func.id == "DataFrameSchema"
    return False


def _ast_is_df_model(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Attribute) and base.attr == "DataFrameModel":
            return True
        if isinstance(base, ast.Name) and base.id == "DataFrameModel":
            return True
    return False


def _ast_build_from_call(var_name: str, call: ast.Call, file_path: str) -> Optional[SchemaMetadata]:
    kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}

    name = _ast_str(kwargs.get("name"), var_name) or var_name
    description = _ast_str(kwargs.get("description"))
    coerce = _ast_bool(kwargs.get("coerce"), False)

    columns: list[ColumnMetadata] = []
    if "columns" in kwargs and isinstance(kwargs["columns"], ast.Dict):
        columns = _ast_extract_columns(kwargs["columns"])

    return SchemaMetadata(
        name=name,
        var_name=var_name,
        file_path=file_path,
        description=description,
        coerce=coerce,
        columns=columns,
    )


def _ast_build_from_class(node: ast.ClassDef, file_path: str) -> Optional[SchemaMetadata]:
    name = node.name
    description: Optional[str] = None
    coerce = False

    for item in node.body:
        if isinstance(item, ast.ClassDef) and item.name == "Config":
            for stmt in item.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        if target.id == "name":
                            name = _ast_str(stmt.value, name) or name
                        elif target.id == "description":
                            description = _ast_str(stmt.value)
                        elif target.id == "coerce":
                            coerce = _ast_bool(stmt.value, False)

    columns: list[ColumnMetadata] = []
    for item in node.body:
        if not isinstance(item, ast.AnnAssign) or not isinstance(item.target, ast.Name):
            continue
        col_name = item.target.id
        if col_name.startswith("_"):
            continue

        dtype = _ast_series_dtype(item.annotation)
        nullable = False
        col_description: Optional[str] = None
        col_title: Optional[str] = None
        checks: list[CheckMetadata] = []

        if item.value and isinstance(item.value, ast.Call) and _ast_is_field_call(item.value):
            fkw = {kw.arg: kw.value for kw in item.value.keywords if kw.arg}
            nullable = _ast_bool(fkw.get("nullable"), False)
            col_description = _ast_str(fkw.get("description"))
            col_title = _ast_str(fkw.get("title"))
            checks = _ast_field_checks(fkw)

        columns.append(ColumnMetadata(
            name=col_name,
            dtype=dtype,
            nullable=nullable,
            checks=checks,
            description=col_description,
            title=col_title,
        ))

    return SchemaMetadata(
        name=name,
        var_name=node.name,
        file_path=file_path,
        source_class=node.name,
        description=description,
        coerce=coerce,
        columns=columns,
    )


def _ast_extract_columns(dict_node: ast.Dict) -> list[ColumnMetadata]:
    columns = []
    for key, value in zip(dict_node.keys, dict_node.values):
        if not isinstance(key, ast.Constant):
            continue
        col_name = str(key.value)

        dtype: Optional[str] = None
        nullable = False
        required = True
        description: Optional[str] = None
        title: Optional[str] = None
        checks: list[CheckMetadata] = []

        if isinstance(value, ast.Call) and _ast_is_column_call(value):
            if value.args:
                dtype = _ast_dtype_node(value.args[0])
            ckw = {kw.arg: kw.value for kw in value.keywords if kw.arg}
            nullable = _ast_bool(ckw.get("nullable"), False)
            required = _ast_bool(ckw.get("required"), True)
            description = _ast_str(ckw.get("description"))
            title = _ast_str(ckw.get("title"))
            if "checks" in ckw:
                checks = _ast_parse_checks(ckw["checks"])

        columns.append(ColumnMetadata(
            name=col_name, dtype=dtype, nullable=nullable, required=required,
            checks=checks, description=description, title=title,
        ))
    return columns


def _ast_is_column_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "Column"
    if isinstance(func, ast.Name):
        return func.id == "Column"
    return False


def _ast_is_field_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "Field"
    if isinstance(func, ast.Name):
        return func.id == "Field"
    return False


def _ast_parse_checks(node: ast.expr) -> list[CheckMetadata]:
    if isinstance(node, ast.Call):
        c = _ast_parse_check(node)
        return [c] if c else []
    if isinstance(node, ast.List):
        return [c for elt in node.elts
                if isinstance(elt, ast.Call)
                for c in [_ast_parse_check(elt)] if c]
    return []


def _ast_parse_check(call: ast.Call) -> Optional[CheckMetadata]:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    check_name = func.attr
    stats: dict = {}
    if call.args and isinstance(call.args[0], ast.Constant):
        param = _CHECK_STAT_MAP.get(check_name, "value")
        stats = {param: call.args[0].value}
    elif call.args and isinstance(call.args[0], ast.List):
        param = _CHECK_STAT_MAP.get(check_name, "value")
        vals = [e.value for e in call.args[0].elts if isinstance(e, ast.Constant)]
        stats = {param: str(vals)}
    return CheckMetadata(name=check_name, statistics=stats)


def _ast_field_checks(field_kwargs: dict[str, ast.expr]) -> list[CheckMetadata]:
    checks = []
    for key, (check_name, param_name) in _FIELD_CHECK_MAP.items():
        if key not in field_kwargs:
            continue
        val_node = field_kwargs[key]
        if isinstance(val_node, ast.Constant):
            checks.append(CheckMetadata(name=check_name, statistics={param_name: val_node.value}))
        elif isinstance(val_node, ast.List):
            vals = [e.value for e in val_node.elts if isinstance(e, ast.Constant)]
            checks.append(CheckMetadata(name=check_name, statistics={param_name: str(vals)}))
    return checks


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _ast_dtype_node(node: ast.expr) -> Optional[str]:
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _ast_series_dtype(annotation: ast.expr) -> Optional[str]:
    """Extract dtype from ``Series[dtype]`` type annotation."""
    if isinstance(annotation, ast.Subscript):
        return _ast_dtype_node(annotation.slice)
    return None


def _ast_str(node: Optional[ast.expr], default: Optional[str] = None) -> Optional[str]:
    if node is None:
        return default
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return default


def _ast_bool(node: Optional[ast.expr], default: bool = False) -> bool:
    if node is None:
        return default
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return default
