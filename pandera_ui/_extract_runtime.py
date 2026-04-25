"""Runtime-based schema extraction via dynamic module import."""

import importlib.util
import sys
import types
from typing import Optional

import pandera.pandas as pa

from .models import CheckMetadata, ColumnMetadata, IndexMetadata, SchemaMetadata


def load_module(path: object, root: object) -> types.ModuleType | None:
    """Dynamically import *path* as a module; return None on any failure."""
    from pathlib import Path
    path = Path(path)  # type: ignore[arg-type]
    root = Path(root)  # type: ignore[arg-type]

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


def runtime_extract(module: types.ModuleType, relative: object) -> list[SchemaMetadata]:
    """Inspect *module* and return metadata for all Pandera schemas found."""
    from pathlib import Path
    relative = Path(relative)  # type: ignore[arg-type]

    results = []
    seen_schema_ids: set[int] = set()

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
            results.append(_build_meta(var_name, df_schema, str(relative), source_class))

    return results


def _build_meta(
    var_name: str,
    schema: pa.DataFrameSchema,
    file_path: str,
    source_class: Optional[str],
) -> SchemaMetadata:
    columns = [_build_column(n, c) for n, c in schema.columns.items()]

    index_meta: Optional[IndexMetadata] = None
    if schema.index is not None:
        idx = schema.index
        index_meta = IndexMetadata(
            name=getattr(idx, "name", None),
            dtype=str(idx.dtype) if getattr(idx, "dtype", None) else None,
            nullable=getattr(idx, "nullable", False),
            checks=[_build_check(c) for c in getattr(idx, "checks", [])],
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


def _build_column(col_name: str, col: pa.Column) -> ColumnMetadata:
    return ColumnMetadata(
        name=col_name,
        dtype=str(col.dtype) if col.dtype is not None else None,
        nullable=col.nullable,
        required=col.required,
        checks=[_build_check(c) for c in col.checks],
        title=getattr(col, "title", None),
        description=getattr(col, "description", None),
    )


def _build_check(check: pa.Check) -> CheckMetadata:
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
