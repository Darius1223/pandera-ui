# Python API

## `scan_project`

```python
from pandera_ui import scan_project

schemas: list[SchemaMetadata] = scan_project(project_path)
```

Walks `project_path` recursively and returns a list of `SchemaMetadata` objects — one per discovered Pandera schema.

**Parameters**

| Parameter | Type | Description |
|---|---|---|
| `project_path` | `str \| Path` | Root directory to scan |

**Returns** `list[SchemaMetadata]`

**Skipped directories**: `.venv`, `venv`, `__pycache__`, `.git`, `node_modules`, `dist`, `build`.

---

## Models

All models are Pydantic `BaseModel` subclasses and can be serialized with `.model_dump()`.

### `SchemaMetadata`

Top-level schema descriptor.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Schema name (from `name=` kwarg or class name) |
| `var_name` | `str` | Python variable or class name in source |
| `file_path` | `str` | Path relative to the scanned root |
| `source_class` | `str \| None` | Class name if defined via `DataFrameModel` |
| `title` | `str \| None` | Short display title |
| `description` | `str \| None` | Schema documentation |
| `coerce` | `bool` | Whether dtypes are coerced automatically |
| `columns` | `list[ColumnMetadata]` | Column descriptors |
| `index` | `IndexMetadata \| None` | Index descriptor |
| `metadata_source` | `"runtime" \| "ast"` | How the schema was extracted |

### `ColumnMetadata`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Column name |
| `dtype` | `str \| None` | Pandas dtype string, e.g. `"int64"` |
| `nullable` | `bool` | Whether `NaN`/`None` values are allowed |
| `required` | `bool` | Whether the column must be present |
| `checks` | `list[CheckMetadata]` | Validation checks |
| `title` | `str \| None` | Short display label |
| `description` | `str \| None` | Column documentation |

### `CheckMetadata`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Check function name, e.g. `"greater_than"` |
| `statistics` | `dict[str, Any]` | Check parameters, e.g. `{"min_value": 0}` |
| `description` | `str \| None` | Human-readable description |
| `error` | `str \| None` | Custom error message |

### `IndexMetadata`

| Field | Type | Description |
|---|---|---|
| `name` | `str \| None` | Index name |
| `dtype` | `str \| None` | Index dtype |
| `nullable` | `bool` | — |
| `checks` | `list[CheckMetadata]` | — |

### `CoverageReport`

Returned by `GET /api/coverage` and produced by the `--coverage` flag.

| Field | Type | Description |
|---|---|---|
| `schema_count` | `int` | Total schemas |
| `schemas_with_title` | `int` | Schemas with a `title` |
| `schemas_with_description` | `int` | Schemas with a `description` |
| `column_count` | `int` | Total columns across all schemas |
| `columns_with_title` | `int` | Columns with a `title` |
| `columns_with_description` | `int` | Columns with a `description` |
| `schema_title_pct` | `float` | % of schemas with a title |
| `schema_description_pct` | `float` | % of schemas with a description |
| `column_title_pct` | `float` | % of columns with a title |
| `column_description_pct` | `float` | % of columns with a description |

---

## Examples

### Iterate columns and checks

```python
from pandera_ui import scan_project

for schema in scan_project("./myproject"):
    print(f"=== {schema.name} ({schema.file_path}) ===")
    for col in schema.columns:
        checks = ", ".join(c.name for c in col.checks) or "none"
        print(f"  {col.name}: {col.dtype}, nullable={col.nullable}, checks=[{checks}]")
```

### Export to JSON

```python
import json
from pandera_ui import scan_project

schemas = scan_project("./myproject")
with open("schemas.json", "w") as f:
    json.dump([s.model_dump() for s in schemas], f, indent=2, default=str)
```

### Compute coverage programmatically

```python
from pandera_ui import scan_project
from pandera_ui._coverage import compute_coverage, format_coverage

schemas = scan_project("./myproject")
report = compute_coverage(schemas)
print(format_coverage(report))
```

### Export to Markdown

```python
from pandera_ui import scan_project
from pandera_ui._export import to_markdown

schemas = scan_project("./myproject")
print(to_markdown(schemas))
```
