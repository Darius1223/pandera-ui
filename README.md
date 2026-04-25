# pandera-ui

**Swagger-like documentation UI for [Pandera](https://pandera.readthedocs.io) dataframe schemas.**

Point it at a Python project and get a searchable, filterable web interface showing every schema — columns, types, validation checks, nullability, and descriptions — in one place.

[![PyPI](https://img.shields.io/pypi/v/pandera-ui)](https://pypi.org/project/pandera-ui/)
[![Python](https://img.shields.io/pypi/pyversions/pandera-ui)](https://pypi.org/project/pandera-ui/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)]()
[![CI](https://github.com/darius-krsk/pandera-ui/actions/workflows/ci.yml/badge.svg)](https://github.com/darius-krsk/pandera-ui/actions)

---

## Demo

```
┌───────────────────────┬──────────────────────────────────────────────────────┐
│  🔍 Search schemas    │  orders                                              │
│  ─────────────────    │  DataFrameSchema · 5 columns · coerce               │
│  ○ orders             │  E-commerce order records                            │
│  ○ products           │  orders.py                                           │
│  ● UserSchema         │                                                      │
│  ○ events             │  COLUMNS                                             │
│                       │  Name        Type     Nullable  Checks               │
│  [All] [Schema] [Model│  order_id    int64    —         greater_than(0)      │
│  Sort: Name A→Z  ▼    │  amount      float64  —         ge(0), lt(1000000)   │
│                       │  status      object   —         isin([pending, …])   │
│  🌙  EN RU FR DE      │  customer_id int64    —         —                    │
└───────────────────────┴──────────────────────────────────────────────────────┘
```

---

## Features

- **Zero config** — run one command, get a UI
- **Two-pass extraction** — runtime import for accuracy, AST fallback for files with missing dependencies
- **Filter & sort** — by schema type (DataFrameSchema / DataFrameModel), metadata source (runtime / AST), column count, or name
- **Search** — across schema names, file paths, and class names
- **Dark / Light theme** — persisted in localStorage
- **Internationalization** — English, Russian, French, German
- **Docker ready** — one-liner to run on any project
- **JSON output** — `--json` flag for CI pipelines and tooling

---

## Installation

```bash
pip install pandera-ui
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add pandera-ui
```

Requires Python 3.10+.

---

## Quick start

```bash
# Scan current directory and open the UI at http://localhost:8765
pandera-ui .

# Scan a specific project
pandera-ui /path/to/myproject --port 9000

# Print JSON instead of starting a server (useful in CI)
pandera-ui . --json
```

---

## Docker

```bash
# Run against any project directory
docker run --rm \
  -v /path/to/myproject:/project:ro \
  -p 8765:8765 \
  ghcr.io/darius-krsk/pandera-ui:latest
```

Or with docker-compose — clone the repo and set `PROJECT_PATH`:

```bash
PROJECT_PATH=/path/to/myproject docker compose up
```

---

## What gets extracted

| Schema style | Example | Support |
|---|---|---|
| `pa.DataFrameSchema(...)` | `orders = pa.DataFrameSchema(...)` | ✅ Full |
| `pa.DataFrameModel` subclass | `class Orders(pa.DataFrameModel)` | ✅ Full |
| File with import errors | imports a missing library | ✅ AST fallback |

**Per column:** name, dtype, nullable, required, checks (with parameters), title, description.

**Per schema:** name, coerce, title, description, index, source file, variable/class name.

### AST fallback

If a file cannot be imported (missing dependency, DB connection at module level, etc.), pandera-ui falls back to static AST analysis — no import, no side effects. Dynamic schemas built from variables or function calls will have incomplete metadata; these are shown with an **AST** badge.

---

## Python API

```python
from pandera_ui import scan_project

schemas = scan_project("./myproject")
for schema in schemas:
    print(schema.name, [c.name for c in schema.columns])
```

`scan_project` returns a list of `SchemaMetadata` Pydantic models. See [`pandera_ui/models.py`](pandera_ui/models.py) for the full shape.

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
  scanner.py   # discovery + extraction (runtime import → AST fallback)
  models.py    # Pydantic models: SchemaMetadata, ColumnMetadata, CheckMetadata
  server.py    # FastAPI: GET /api/schemas, GET /
  cli.py       # Typer CLI entry point
frontend/
  index.html   # single-page UI (vanilla JS, no build step)
```

---

## Development

```bash
git clone https://github.com/darius-krsk/pandera-ui
cd pandera-ui
uv sync
uv run playwright install chromium

# Run all tests
uv run pytest tests/ -q

# Run with coverage
uv run pytest tests/ --cov=pandera_ui --cov-report=term-missing

# Type check
uv run mypy pandera_ui/

# Try the UI on the test fixtures
uv run pandera-ui tests/fixtures
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## License

[MIT](LICENSE)
