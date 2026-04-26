# Architecture

## Project layout

```
pandera_ui/
  scanner.py            # Entry point: walks project, dispatches per file
  _extract_runtime.py   # Pass 1: dynamic import + introspection
  _extract_ast.py       # Pass 2: static AST parse (fallback)
  models.py             # Pydantic models: SchemaMetadata, ColumnMetadata, …
  server.py             # FastAPI: GET /api/schemas, GET /api/coverage, GET /
  cli.py                # Typer CLI entry point
  _console.py           # Optional rich output (spinner, summary table)
  _export.py            # Markdown and HTML renderers
  _coverage.py          # Documentation coverage calculator
frontend/
  index.html            # Single-page UI (vanilla JS, no build step)
  demo-data.json        # Pre-generated schema data for the live demo
```

---

## Two-pass extraction

Schema discovery is the core of pandera-ui. Each `.py` file is processed in two passes:

```
.py file
   │
   ▼
┌─────────────────────────────┐
│  Pass 1: Runtime import     │  importlib.util.spec_from_file_location
│  • Full accuracy            │  → exec_module()
│  • Handles dynamic schemas  │  → inspect module attributes
│  • May fail (missing deps)  │
└─────────────┬───────────────┘
              │ success → SchemaMetadata (metadata_source="runtime")
              │ failure ↓
┌─────────────────────────────┐
│  Pass 2: AST fallback       │  ast.parse()
│  • No import side effects   │  → walk Call nodes
│  • Static literals only     │  → extract keyword arguments
│  • Always safe              │
└─────────────────────────────┘
              │
              ▼
         SchemaMetadata (metadata_source="ast")
```

### When AST fallback is used

- The file imports a library that isn't installed (e.g., a database connector)
- Module-level code opens a network connection or reads a file
- A circular import prevents loading

AST-extracted schemas get an `AST` badge in the UI so users know the extraction was incomplete.

### What AST can and cannot extract

**Can extract**: string/int/float/bool literals, list/dict literals, simple attribute access (`pa.Column`, `pa.Check.greater_than`).

**Cannot extract**: values computed at runtime — function return values, variable references, f-strings, comprehensions.

---

## Schema detection

A module attribute is recognized as a Pandera schema if it is:

- An instance of `pa.DataFrameSchema`, **or**
- A subclass of `pa.DataFrameModel` (i.e. `issubclass(obj, pa.DataFrameModel) and obj is not pa.DataFrameModel`)

---

## Frontend

The UI is a **single vanilla JS file** — no framework, no build step. It fetches `/api/schemas` on load and renders the schema list client-side.

This keeps the package footprint small: the only runtime dependencies are FastAPI, uvicorn, typer, pydantic, pandera, numpy, and pandas.

---

## Server state

The FastAPI app holds schemas in a module-level `_schemas` list. `load_schemas(path)` rescans the directory and replaces the list. In `--watch` mode, the watchdog handler calls `load_schemas()` on every `.py` file change — the in-memory state is updated atomically (GIL protects the list reassignment), and the next request to `/api/schemas` sees fresh data.

---

## Optional dependencies

| Extra | Packages | What it enables |
|---|---|---|
| `rich` | `rich>=13` | Terminal spinner + summary table |
| `watch` | `watchdog>=3` | `--watch` live-reload flag |
