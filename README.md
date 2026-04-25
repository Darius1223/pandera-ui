# pandera-ui

> **Swagger for your Pandera schemas.** One command — instant searchable documentation for every dataframe schema in your project.

[![PyPI](https://img.shields.io/pypi/v/pandera-ui)](https://pypi.org/project/pandera-ui/)
[![Python](https://img.shields.io/pypi/pyversions/pandera-ui)](https://pypi.org/project/pandera-ui/)
[![CI](https://github.com/Darius1223/pandera-ui/actions/workflows/ci.yml/badge.svg)](https://github.com/Darius1223/pandera-ui/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/Darius1223/pandera-ui/branch/main/graph/badge.svg)](https://codecov.io/gh/Darius1223/pandera-ui)
[![License: MIT](https://img.shields.io/github/license/Darius1223/pandera-ui)](https://github.com/Darius1223/pandera-ui/blob/main/LICENSE)

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

| Feature | Description |
|---|---|
| **Zero config** | Point at a directory, get a UI. No decorators, no config files. |
| **Two-pass extraction** | Runtime import for accuracy + AST fallback when imports fail (missing deps, DB connections, etc.) |
| **Rich CLI** | Progress spinner and summary table when `rich` is installed |
| **CI-friendly** | `--json` flag exports structured metadata for linting, diffing, or downstream tooling |
| **Fast navigation** | Filter by type, sort by name/file/columns, full-text search |
| **Team-ready** | Dark/light theme, EN/RU/FR/DE localization |

---

## Quick start

```bash
# Install
pip install pandera-ui

# Scan current directory and open the UI
pandera-ui .

# Scan a specific project on a custom port
pandera-ui /path/to/myproject --port 9000

# Pretty terminal output (spinner + summary table)
pip install pandera-ui[rich]
pandera-ui .

# Export JSON for CI / tooling
pandera-ui . --json > schemas.json
```

---

## What you get

**Terminal output** (with `pandera-ui[rich]`):

```
Found 4 schema(s).

 Schema    Type             File                   Columns
 orders    DataFrameSchema  dataframe_schemas.py   5
 products  DataFrameSchema  dataframe_schemas.py   4
 users     DataFrameModel   schema_models.py       4
 events    DataFrameModel   schema_models.py       5
```

**Browser UI:** searchable sidebar, column table with dtypes and checks, AST/runtime badge, dark/light theme.

---

## Installation

```bash
# Core
pip install pandera-ui

# With beautiful terminal output
pip install pandera-ui[rich]
```

With [uv](https://github.com/astral-sh/uv):

```bash
uv add pandera-ui
uv add pandera-ui[rich]   # optional rich UI
```

Requires Python 3.10+.

### Docker

```bash
docker run --rm \
  -v /path/to/myproject:/project:ro \
  -p 8765:8765 \
  ghcr.io/darius-krsk/pandera-ui:latest
```

```bash
PROJECT_PATH=/path/to/myproject docker compose up
```

---

## What gets extracted

| Schema style | Example | Support |
| --- | --- | --- |
| `pa.DataFrameSchema(...)` | `orders = pa.DataFrameSchema(...)` | Full |
| `pa.DataFrameModel` subclass | `class Orders(pa.DataFrameModel)` | Full |
| File with import errors | imports a missing library | AST fallback |

**Per column:** name, dtype, nullable, required, checks (with parameters), title, description.

**Per schema:** name, coerce, title, description, index, source file, variable/class name.

### AST fallback

When a file can't be imported (missing dependency, DB connection at module level, etc.), pandera-ui falls back to static AST analysis — no import side effects, no crashes. Schemas extracted this way get an `AST` badge in the UI.

---

## Python API

```python
from pandera_ui import scan_project

schemas = scan_project("./myproject")
for schema in schemas:
    print(schema.name, [c.name for c in schema.columns])
```

`scan_project` returns a list of `SchemaMetadata` Pydantic models.
See [`pandera_ui/models.py`](pandera_ui/models.py) for the full structure.

---

## CLI reference

```
Usage: pandera-ui [OPTIONS] [PROJECT_PATH]

  Scan PROJECT_PATH for Pandera schemas and serve a documentation UI.

Arguments:
  [PROJECT_PATH]  Project root to scan  [default: .]

Options:
  -p, --port INTEGER  Port for the UI server  [default: 8765]
  --host TEXT         Host to bind  [default: 127.0.0.1]
  --json              Print JSON to stdout, do not start server
  --help              Show this message and exit.
```

---

## Architecture

```
pandera_ui/
  scanner.py            # discovery: walks project, dispatches per file
  _extract_runtime.py   # pass 1: dynamic import + introspection
  _extract_ast.py       # pass 2: static AST parse (fallback)
  models.py             # Pydantic models: SchemaMetadata, ColumnMetadata, CheckMetadata
  server.py             # FastAPI: GET /api/schemas, GET /
  cli.py                # Typer CLI entry point
  _console.py           # optional rich output (spinner, summary table)
frontend/
  index.html            # single-page UI (vanilla JS, no build step)
```

---

## Development

```bash
git clone https://github.com/darius-krsk/pandera-ui
cd pandera-ui
make setup            # uv sync
make setup-ui-tests   # install Playwright browser

make lint             # ruff check
make type             # mypy
make test             # unit tests
make test-cov         # unit tests + coverage report

make test-ui          # Playwright E2E tests (requires Playwright)
make run              # start UI against test fixtures
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for raw commands and PR guidelines.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE) © 2025 Ildar
