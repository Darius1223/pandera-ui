# pandera-ui

Swagger-like documentation UI for [Pandera](https://pandera.readthedocs.io) dataframe schemas.

Point it at any Python project and instantly browse every discovered schema: columns, dtypes,
validation checks, nullability, titles, and descriptions in one searchable UI. 🚀

[![PyPI](https://img.shields.io/pypi/v/pandera-ui)](https://pypi.org/project/pandera-ui/)
[![Python](https://img.shields.io/pypi/pyversions/pandera-ui)](https://pypi.org/project/pandera-ui/)
[![CI](https://github.com/darius-krsk/pandera-ui/actions/workflows/ci.yml/badge.svg)](https://github.com/darius-krsk/pandera-ui/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/darius-krsk/pandera-ui/branch/main/graph/badge.svg)](https://codecov.io/gh/darius-krsk/pandera-ui)
[![License](https://img.shields.io/github/license/darius-krsk/pandera-ui)](https://github.com/darius-krsk/pandera-ui/blob/main/LICENSE)

## Demo

![Pandera UI screenshot](docs/assets/ui-overview.png)

## Why use it

- Zero config: run one command, get a UI ⚡
- Two-pass extraction: runtime import first, AST fallback when imports fail 🧠
- Fast navigation: filter by type/source, sort by columns/name, full-text search 🔎
- CI-friendly: export JSON with `--json` for tooling and automation 🔁
- Ready for teams: dark/light theme and EN/RU/FR/DE localization 🌍

## Quick start

```bash
# Scan current directory and open the UI at http://localhost:8765
pandera-ui .

# Scan a specific project
pandera-ui /path/to/myproject --port 9000

# Print JSON instead of starting a server
pandera-ui . --json
```

## Installation

```bash
pip install pandera-ui
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add pandera-ui
```

Requires Python 3.10+.

## Docker

```bash
docker run --rm \
  -v /path/to/myproject:/project:ro \
  -p 8765:8765 \
  ghcr.io/darius-krsk/pandera-ui:latest
```

Or with docker-compose:

```bash
PROJECT_PATH=/path/to/myproject docker compose up
```

## What gets extracted

| Schema style | Example | Support |
| --- | --- | --- |
| `pa.DataFrameSchema(...)` | `orders = pa.DataFrameSchema(...)` | Full |
| `pa.DataFrameModel` subclass | `class Orders(pa.DataFrameModel)` | Full |
| File with import errors | imports a missing library | AST fallback |

Per column: name, dtype, nullable, required, checks (with parameters), title, description.

Per schema: name, coerce, title, description, index, source file, variable/class name.

### AST fallback

If a file cannot be imported (missing dependency, DB connection at module level, etc.),
pandera-ui falls back to static AST analysis (no import side effects). Dynamic schemas built from
variables or function calls can be partially resolved and are marked with an `AST` badge.

## Python API

```python
from pandera_ui import scan_project

schemas = scan_project("./myproject")
for schema in schemas:
    print(schema.name, [c.name for c in schema.columns])
```

`scan_project` returns a list of `SchemaMetadata` Pydantic models. See
[`pandera_ui/models.py`](pandera_ui/models.py) for the full structure.

## CLI reference

```text
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

## Architecture

```text
pandera_ui/
  scanner.py   # discovery + extraction (runtime import -> AST fallback)
  models.py    # Pydantic models: SchemaMetadata, ColumnMetadata, CheckMetadata
  server.py    # FastAPI: GET /api/schemas, GET /
  cli.py       # Typer CLI entry point
frontend/
  index.html   # single-page UI (vanilla JS, no build step)
```

## Development

```bash
git clone https://github.com/darius-krsk/pandera-ui
cd pandera-ui
make setup
make setup-ui-tests

# Core checks
make lint
make type
make test

# Coverage run
make test-cov

# Optional browser UI tests (requires Playwright browser install)
make test-ui

# Run UI against fixtures
make run
```

If you prefer raw commands, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
