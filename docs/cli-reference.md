# CLI Reference

## Synopsis

```
pandera-ui [OPTIONS] [PROJECT_PATH]
```

`PROJECT_PATH` defaults to `.` (current directory).

---

## Options

### `--port` / `-p`

Port for the UI server. Default: `8765`.

```bash
pandera-ui . --port 9000
pandera-ui . -p 9000
```

---

### `--host`

Host address to bind. Default: `127.0.0.1`.

```bash
# Expose to the local network
pandera-ui . --host 0.0.0.0
```

---

### `--json`

Print all discovered schemas as a JSON array to stdout, then exit. No server is started.

```bash
pandera-ui . --json
pandera-ui . --json > schemas.json
```

Output shape:

```json
[
  {
    "name": "orders",
    "var_name": "orders_schema",
    "file_path": "data/schemas.py",
    "source_class": null,
    "title": null,
    "description": "E-commerce order records",
    "coerce": true,
    "columns": [...],
    "index": null,
    "metadata_source": "runtime"
  }
]
```

---

### `--export`

Export schema documentation to stdout and exit. No server is started.

Supported formats: `markdown`, `html`.

```bash
# Markdown — paste into README, Sphinx, or MkDocs
pandera-ui . --export markdown > schemas.md

# Standalone HTML file
pandera-ui . --export html > schemas.html
```

The Markdown output produces a GFM table per schema with columns, types, nullability, and descriptions. The HTML output is a self-contained file with inline CSS.

---

### `--coverage`

Print documentation coverage statistics and exit. No server is started.

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

The same data is also available as a JSON endpoint when the server is running: `GET /api/coverage`.

---

### `--watch` / `-w`

Start the UI server and automatically reload schemas when any `.py` file in the project changes.

```bash
pip install pandera-ui[watch]   # requires watchdog
pandera-ui . --watch
pandera-ui . -w
```

Useful during schema development — edit a schema, save, and the UI reflects the change within seconds without restarting the server.

---

### `--version`

Print the installed version and exit.

```bash
pandera-ui --version
# pandera-ui 1.0.4
```

---

### `--verbose` / `-v`

Print per-file scan progress to stderr. Shows which extraction method was used
(`runtime`, `ast`, or `ast[fallback]`) and how many schemas were found in each file.

```bash
pandera-ui . --verbose
pandera-ui . -v
```

Example output:

```
  runtime            data/orders.py  (1 schema(s))
  ast[fallback]      data/broken.py  (0 schema(s))
  runtime            models/users.py  (2 schema(s))
```

---

### `--workers`

Number of parallel threads used during scanning. Default: `1`.

Useful for large projects with many Python files where import time dominates.

```bash
pandera-ui . --workers 4
```

---

### `--no-import`

Skip dynamic import entirely and use the AST extractor for every file. Faster and
side-effect-free, but less accurate — dynamic schema construction and runtime checks
are not evaluated.

```bash
pandera-ui . --no-import
```

All schemas discovered this way will have `"metadata_source": "ast"` in the JSON output.

---

### `--help`

Show the help message and exit.

```bash
pandera-ui --help
```

---

## API endpoints

When the server is running, the following JSON endpoints are available:

| Endpoint | Description |
|---|---|
| `GET /api/schemas` | All discovered schemas |
| `GET /api/coverage` | Documentation coverage statistics |
| `GET /` | The browser UI |

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Error (invalid `--export` format, `watchdog` not installed, etc.) |
