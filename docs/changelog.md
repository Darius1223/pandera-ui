# Changelog

All notable changes to pandera-ui are documented here.

## [0.3.0] — 2026-04-26

### Added
- `--export markdown` / `--export html` — generate schema docs without starting a server; embeds into README, Sphinx, or MkDocs
- `--coverage` flag — print documentation coverage (% of schemas and columns with `title`/`description`); also available as `GET /api/coverage` for CI quality gates
- `--watch` / `-w` flag — auto-reload schemas on `.py` file changes using `watchdog` (install via `pandera-ui[watch]`)
- `CoverageReport` Pydantic model in `pandera_ui.models`
- `pandera_ui._export` module with `to_markdown()` and `to_html()` functions
- `pandera_ui._coverage` module with `compute_coverage()` and `format_coverage()` functions
- `watch` optional extra: `pip install pandera-ui[watch]`
- MkDocs documentation site

## [0.2.0] — 2026-04-25

### Added
- `rich` optional extra: `pip install pandera-ui[rich]` enables spinner and summary table in CLI
- `examples/quickstart.py` — standalone Python API demo

### Changed
- `scanner.py` split into `_extract_runtime.py` and `_extract_ast.py` for clarity
- `_FIELD_CHECK_MAP` and `_CHECK_STAT_MAP` unified — stat map is now derived, removing duplication
- Renamed internal `_cli` → `cli_app` in `cli.py`

### Fixed
- CI: `id-token: write` permission moved to dedicated `upload-coverage` job (was granted to all matrix runners)
- CI: `setup-uv` updated from `v4` → `v5`

## [0.1.0] — 2025

### Added
- Two-pass schema extraction: runtime import first, static AST fallback when imports fail
- FastAPI server serving a single-page vanilla JS UI
- Supports `pa.DataFrameSchema` and `pa.DataFrameModel` subclasses
- Per-column metadata: name, dtype, nullable, required, checks with parameters, title, description
- Per-schema metadata: name, coerce, title, description, index, source file, variable/class name
- CLI (`pandera-ui`) with `--json` mode for CI/tooling integration
- Python API: `scan_project()` returns a list of Pydantic `SchemaMetadata` models
- 4 UI languages: EN, RU, FR, DE
- Dark / light theme with localStorage persistence
- Filter by schema type, sort by name / file / columns, full-text search
- Docker image and docker-compose support
