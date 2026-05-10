"""Static AST extraction fallback for files that cannot be imported.

Only literal values are extracted; dynamic expressions (function calls,
variable references) are silently skipped.
"""

import ast
from typing import Optional

from .models import CheckMetadata, ColumnMetadata, SchemaMetadata

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

# Derived from _FIELD_CHECK_MAP plus extras not expressible as Field kwargs
_CHECK_STAT_MAP: dict[str, str] = {
    check_name: stat_key for check_name, stat_key in _FIELD_CHECK_MAP.values()
} | {"in_range": "min_value"}


def ast_extract(path: object, relative: object) -> list[SchemaMetadata]:
    """Parse *path* with the AST module and extract schema metadata without importing."""
    from pathlib import Path
    path = Path(path)  # type: ignore[arg-type]
    relative = Path(relative)  # type: ignore[arg-type]

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    model_names = _collect_model_names(tree)
    results: list[SchemaMetadata] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _is_df_schema_call(node.value):
                    meta = _build_from_call(target.id, node.value, str(relative))  # type: ignore[arg-type]
                    if meta:
                        results.append(meta)

        elif isinstance(node, ast.ClassDef) and node.name in model_names:
            meta = _build_from_class(node, str(relative))
            if meta:
                results.append(meta)

    return results


# ---------------------------------------------------------------------------
# Node recognisers
# ---------------------------------------------------------------------------

def _is_df_schema_call(node: ast.expr) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "DataFrameSchema"
    if isinstance(func, ast.Name):
        return func.id == "DataFrameSchema"
    return False


def _collect_model_names(tree: ast.Module) -> set[str]:
    """Return all class names in *tree* that transitively inherit from DataFrameModel."""
    local_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}

    # Seed with DataFrameModel plus any imported name used as a base class.
    # This handles project-local base classes (e.g. BaseDataFrameModel) defined
    # in other files — we can't know at AST time whether they're pandera models,
    # so we optimistically include them and let _build_from_class do the filtering.
    external_bases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                name: Optional[str] = None
                if isinstance(base, ast.Attribute):
                    name = base.attr
                elif isinstance(base, ast.Name):
                    name = base.id
                if name and name not in local_names:
                    external_bases.add(name)

    known: set[str] = {"DataFrameModel"} | external_bases
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name not in known:
                for base in node.bases:
                    base_name: Optional[str] = None
                    if isinstance(base, ast.Attribute):
                        base_name = base.attr
                    elif isinstance(base, ast.Name):
                        base_name = base.id
                    if base_name in known:
                        known.add(node.name)
                        changed = True
    known.discard("DataFrameModel")
    known -= external_bases  # only return locally-defined class names
    return known


# ---------------------------------------------------------------------------
# Schema builders
# ---------------------------------------------------------------------------

def _build_from_call(var_name: str, call: ast.Call, file_path: str) -> Optional[SchemaMetadata]:
    kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}

    name = _str(kwargs.get("name"), var_name) or var_name
    description = _str(kwargs.get("description"))
    coerce = _bool(kwargs.get("coerce"), False)

    columns: list[ColumnMetadata] = []
    if "columns" in kwargs and isinstance(kwargs["columns"], ast.Dict):
        columns = _extract_columns(kwargs["columns"])

    return SchemaMetadata(
        name=name,
        var_name=var_name,
        file_path=file_path,
        description=description,
        coerce=coerce,
        columns=columns,
    )


def _build_from_class(node: ast.ClassDef, file_path: str) -> Optional[SchemaMetadata]:
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
                            name = _str(stmt.value, name) or name
                        elif target.id == "description":
                            description = _str(stmt.value)
                        elif target.id == "coerce":
                            coerce = _bool(stmt.value, False)

    columns: list[ColumnMetadata] = []
    for item in node.body:
        if not isinstance(item, ast.AnnAssign) or not isinstance(item.target, ast.Name):
            continue
        col_name = item.target.id
        if col_name.startswith("_"):
            continue

        dtype = _series_dtype(item.annotation)
        nullable = False
        col_description: Optional[str] = None
        col_title: Optional[str] = None
        checks: list[CheckMetadata] = []

        if item.value and isinstance(item.value, ast.Call) and _is_field_call(item.value):
            fkw = {kw.arg: kw.value for kw in item.value.keywords if kw.arg}
            nullable = _bool(fkw.get("nullable"), False)
            col_description = _str(fkw.get("description"))
            col_title = _str(fkw.get("title"))
            checks = _field_checks(fkw)

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


# ---------------------------------------------------------------------------
# Column helpers
# ---------------------------------------------------------------------------

def _extract_columns(dict_node: ast.Dict) -> list[ColumnMetadata]:
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

        if isinstance(value, ast.Call) and _is_column_call(value):
            if value.args:
                dtype = _dtype_node(value.args[0])
            ckw = {kw.arg: kw.value for kw in value.keywords if kw.arg}
            nullable = _bool(ckw.get("nullable"), False)
            required = _bool(ckw.get("required"), True)
            description = _str(ckw.get("description"))
            title = _str(ckw.get("title"))
            if "checks" in ckw:
                checks = _parse_checks(ckw["checks"])

        columns.append(ColumnMetadata(
            name=col_name, dtype=dtype, nullable=nullable, required=required,
            checks=checks, description=description, title=title,
        ))
    return columns


def _is_column_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "Column"
    if isinstance(func, ast.Name):
        return func.id == "Column"
    return False


def _is_field_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "Field"
    if isinstance(func, ast.Name):
        return func.id == "Field"
    return False


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------

def _parse_checks(node: ast.expr) -> list[CheckMetadata]:
    if isinstance(node, ast.Call):
        c = _parse_check(node)
        return [c] if c else []
    if isinstance(node, ast.List):
        return [c for elt in node.elts
                if isinstance(elt, ast.Call)
                for c in [_parse_check(elt)] if c]
    return []


def _parse_check(call: ast.Call) -> Optional[CheckMetadata]:
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


def _field_checks(field_kwargs: dict[str, ast.expr]) -> list[CheckMetadata]:
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
# Primitive extractors
# ---------------------------------------------------------------------------

def _dtype_node(node: ast.expr) -> Optional[str]:
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _series_dtype(annotation: ast.expr) -> Optional[str]:
    """Extract dtype from ``Series[dtype]`` type annotation."""
    if isinstance(annotation, ast.Subscript):
        return _dtype_node(annotation.slice)
    return None


def _str(node: Optional[ast.expr], default: Optional[str] = None) -> Optional[str]:
    if node is None:
        return default
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return default


def _bool(node: Optional[ast.expr], default: bool = False) -> bool:
    if node is None:
        return default
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return default
