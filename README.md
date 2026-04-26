<div align="center">

# pandera-ui

**Swagger for your Pandera schemas.**  
One command — instant searchable documentation for every dataframe schema in your project.

[![PyPI](https://img.shields.io/pypi/v/pandera-ui?color=blue)](https://pypi.org/project/pandera-ui/)
[![Python](https://img.shields.io/pypi/pyversions/pandera-ui)](https://pypi.org/project/pandera-ui/)
[![CI](https://github.com/Darius1223/pandera-ui/actions/workflows/ci.yml/badge.svg)](https://github.com/Darius1223/pandera-ui/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/Darius1223/pandera-ui/branch/main/graph/badge.svg)](https://codecov.io/gh/Darius1223/pandera-ui)
[![License: MIT](https://img.shields.io/github/license/Darius1223/pandera-ui)](LICENSE)

[**Documentation**](https://darius1223.github.io/pandera-ui/) · [**Live Demo**](https://darius1223.github.io/pandera-ui/demo/) · [**PyPI**](https://pypi.org/project/pandera-ui/) · [**Changelog**](CHANGELOG.md)

</div>

---

## The problem

You have 30 Pandera schemas spread across a data project. New team members ask: *"Which columns does `OrdersSchema` have? Is `amount` nullable? What checks run on `user_id`?"*

The answer is buried in code. There's no docs page, no searchable index — just `grep` and hope.

## The solution

```bash
pip install pandera-ui
pandera-ui /path/to/myproject
```

pandera-ui scans your project, discovers every `DataFrameSchema` and `DataFrameModel`, and opens a **Swagger-like UI** at `http://localhost:8765`.

![pandera-ui screenshot](docs/assets/ui-overview.png)

---

## Features

| | Feature | Description |
|---|---|---|
| ⚡ | **Zero config** | Point at a directory, get a UI. No decorators, no config files. |
| 🔍 | **Two-pass extraction** | Runtime import for accuracy + AST fallback when imports fail (missing deps, DB connections, etc.) |
| 👁 | **Live reload** | `--watch` reloads schemas automatically when `.py` files change |
| 📄 | **Export** | `--export markdown` / `--export html` — static docs for README or Sphinx |
| 📊 | **Coverage** | `--coverage` shows what % of schemas and columns are documented |
| 🔧 | **CI-friendly** | `--json` exports structured metadata; `/api/coverage` for quality gates |
| 🎨 | **Rich CLI** | Progress spinner and summary table when `rich` is installed |
| 🌍 | **Team-ready** | Dark/light theme, EN/RU/FR/DE localization, full-text search |

---

## Quick start

```bash
# Install
pip install pandera-ui

# Scan current directory and open the UI
pandera-ui .

# Scan a specific project on a custom port
pandera-ui /path/to/myproject --port 9000
```

**Terminal output** (with `pandera-ui[rich]`):

```
Found 4 schema(s).

 Schema    Type             File                   Columns
 orders    DataFrameSchema  dataframe_schemas.py   5
 products  DataFrameSchema  dataframe_schemas.py   4
 users     DataFrameModel   schema_models.py       4
 events    DataFrameModel   schema_models.py       5

UI ready at http://127.0.0.1:8765
```

Open `http://localhost:8765` in the browser — searchable sidebar, column table with dtypes and checks, AST/runtime badge, dark/light theme.

---

## Installation

```bash
pip install pandera-ui            # core
pip install pandera-ui[rich]      # + spinner and summary table
pip install pandera-ui[watch]     # + --watch live-reload
pip install pandera-ui[rich,watch]  # everything
```

With [uv](https://github.com/astral-sh/uv):

```bash
uv add pandera-ui
uv add pandera-ui[rich,watch]
```

Requires **Python 3.10+**.

### Docker

```bash
docker run --rm \
  -v /path/to/myproject:/project:ro \
  -p 8765:8765 \
  ghcr.io/darius-krsk/pandera-ui:latest
```

---

## All CLI options

```bash
# Export schema docs (no server started)
pandera-ui . --export markdown > schemas.md
pandera-ui . --export html    > schemas.html

# Check documentation coverage
pandera-ui . --coverage

# Live reload on .py changes
pip install pandera-ui[watch]
pandera-ui . --watch

# Export raw JSON for CI / tooling
pandera-ui . --json > schemas.json
```

**Full CLI reference:**

```
Usage: pandera-ui [OPTIONS] [PROJECT_PATH]

Arguments:
  [PROJECT_PATH]  Project root to scan  [default: .]

Options:
  -p, --port INTEGER           Port for the UI server  [default: 8765]
  --host TEXT                  Host to bind  [default: 127.0.0.1]
  --json                       Print JSON to stdout, no server
  --export [markdown|html]     Export docs to stdout, no server
  --coverage                   Print coverage stats and exit
  -w, --watch                  Auto-reload schemas on .py changes
  --help                       Show this message and exit.
```

---

## What gets extracted

| Schema style | Example | Support |
|---|---|---|
| `pa.DataFrameSchema(...)` | `orders = pa.DataFrameSchema(...)` | Full |
| `pa.DataFrameModel` subclass | `class Orders(pa.DataFrameModel)` | Full |
| File with import errors | imports a missing library | AST fallback |

**Per column:** name, dtype, nullable, required, checks (with parameters), title, description.

**Per schema:** name, coerce, title, description, index, source file, variable/class name.

---

## Python API

```python
from pandera_ui import scan_project

schemas = scan_project("./myproject")
for schema in schemas:
    print(schema.name, [c.name for c in schema.columns])
```

`scan_project` returns a list of `SchemaMetadata` Pydantic models — serialize with `.model_dump()`.

```python
# Compute coverage programmatically
from pandera_ui._coverage import compute_coverage, format_coverage
report = compute_coverage(schemas)
print(format_coverage(report))

# Export to Markdown
from pandera_ui._export import to_markdown
print(to_markdown(schemas))
```

---

## Architecture

```
pandera_ui/
  scanner.py            # discovery: walks project, dispatches per file
  _extract_runtime.py   # pass 1: dynamic import + introspection
  _extract_ast.py       # pass 2: static AST parse (fallback)
  models.py             # Pydantic models: SchemaMetadata, ColumnMetadata …
  server.py             # FastAPI: GET /api/schemas, GET /api/coverage, GET /
  cli.py                # Typer CLI entry point
  _export.py            # Markdown and HTML renderers
  _coverage.py          # Documentation coverage calculator
  _console.py           # optional rich output (spinner, summary table)
frontend/
  index.html            # single-page UI (vanilla JS, no build step)
```

---

## Development

```bash
git clone https://github.com/Darius1223/pandera-ui
cd pandera-ui
uv sync

make lint        # ruff check
make type        # mypy
make test        # unit tests
make test-cov    # unit tests + coverage report
make run         # start UI against test fixtures
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for PR guidelines.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE) © 2025 Ildar
