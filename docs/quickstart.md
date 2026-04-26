# Quick Start

## 1. Install

```bash
pip install pandera-ui
```

## 2. Start the UI

Point pandera-ui at your project root:

```bash
pandera-ui /path/to/myproject
```

Open `http://localhost:8765` — you'll see a searchable list of all discovered schemas.

```
Found 4 schema(s).

 Schema    Type             File                   Columns
 orders    DataFrameSchema  dataframe_schemas.py   5
 products  DataFrameSchema  dataframe_schemas.py   4
 users     DataFrameModel   schema_models.py       4
 events    DataFrameModel   schema_models.py       5

UI ready at http://127.0.0.1:8765
```

!!! tip "Better terminal output"
    Install `pandera-ui[rich]` for a spinner and formatted table instead of plain text.

## 3. Browse schemas

- **Sidebar** — click any schema to open its detail card.
- **Search bar** — filter schemas by name, file, or column.
- **Type filter** — show only `DataFrameSchema` or `DataFrameModel`.
- **Sort** — by name, file path, or column count.
- **Theme toggle** — dark / light. EN / RU / FR / DE localization.

## 4. Export docs (no server)

Generate static docs from the command line:

```bash
# Markdown — embed in README or Sphinx
pandera-ui . --export markdown > schemas.md

# Standalone HTML
pandera-ui . --export html > schemas.html
```

## 5. Check documentation coverage

See how well your schemas are documented:

```bash
pandera-ui . --coverage
```

```
Documentation Coverage
======================
Schemas : 4
  title       : 0/4 (0.0%)
  description : 2/4 (50.0%)
Columns : 18
  title       : 0/18 (0.0%)
  description : 9/18 (50.0%)
```

Use in CI to gate on a minimum coverage threshold:

```bash
# fail the build if column description coverage < 80 %
pandera-ui . --json | python -c "
import json, sys
schemas = json.load(sys.stdin)
cols = [c for s in schemas for c in s['columns']]
pct = sum(1 for c in cols if c.get('description')) / len(cols) * 100
print(f'Column coverage: {pct:.1f}%')
sys.exit(0 if pct >= 80 else 1)
"
```

## 6. Live reload during development

```bash
pip install pandera-ui[watch]
pandera-ui . --watch
```

The server reloads schemas automatically whenever any `.py` file changes — no restart needed.

## 7. Python API

```python
from pandera_ui import scan_project

schemas = scan_project("./myproject")
for schema in schemas:
    print(schema.name, [c.name for c in schema.columns])
```

`scan_project` returns a list of `SchemaMetadata` Pydantic models. See [Python API](python-api.md) for the full reference.
