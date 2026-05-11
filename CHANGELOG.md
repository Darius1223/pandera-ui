# Changelog

All notable changes to pandera-ui are documented here.

## [1.2.2] — 2026-05-11

### Fixed
- Corrected PyPI metadata: `Homepage` now points to the docs site (`darius1223.github.io/pandera-ui`), `Repository` now points to the correct GitHub account (`Darius1223/pandera-ui`). Previously both fields referenced a wrong URL.

## [1.2.1] — 2026-05-10

### Fixed
- Runtime import now succeeds for files that use absolute intra-project imports (e.g. `from ibp.calculations.models.base import ...`). Previously only the scan root was added to `sys.path`; now all parent package directories up to the first non-package ancestor are added automatically. This eliminates the "⚠ Import failed" warning for the vast majority of files in nested-package projects.

## [1.2.0] — 2026-05-10

### Fixed
- AST extractor now discovers subclasses of project-local base models (e.g. `class MyModel(BaseDataFrameModel)` where `BaseDataFrameModel` lives in another file). Previously only direct `DataFrameModel` inheritance was detected in AST mode, yielding 0 schemas for all such files.
- Files importing Airflow, Django, Flask, or Celery are now scanned with AST-only mode instead of triggering runtime import. This eliminates SQLAlchemy/metastore errors that were printed to stderr whenever Airflow DAG or config files were present in the project.

### Changed
- Default `--workers` increased from 1 to 4; `scan_project()` default matches. Scanning a large project is now ~4× faster out of the box without any flag required.

## [1.1.0] — 2026-05-10

### Added
- `--version` flag — print installed version and exit
- `--verbose` / `-v` flag — print per-file scan progress to stderr (method used, schema count)
- `--workers N` flag — parallel file scanning via thread pool; useful for large projects
- `--no-import` flag — AST-only mode, skips dynamic import for faster and side-effect-free scanning

### Fixed
- AST extractor now finds transitive `DataFrameModel` subclasses (`class Child(MyBase)` when `class MyBase(pa.DataFrameModel)` is defined in the same file)

### Docs
- `docs/cli-reference.md` updated with all new flags and examples

## [1.0.4] — 2026-05-10

### CI / Dev
- Added `nox` compat matrix: tests 6 combinations of pandera (0.27.1, 0.31.x) × pandas (2.1.4, 2.2.3, 2.3.3) on every push
- CI `compat` job now delegates to `nox -s compat` instead of hand-rolled pip steps
- `nox>=2024.10` added to dev dependencies
- Removed `test_matrix.sh` (superseded by nox)

## [1.0.3] — 2026-05-10

### Fixed
- Relaxed `pandera` lower bound to `>=0.27.1` (actual minimum where `pandera.pandas` and `DataFrameModel.to_schema()` work correctly with NumPy 2.x)
- Relaxed `pandas` lower bound to `>=2.1.4` (pandas 2.1.x / 2.2.x / 2.3.x all supported)
- Removed explicit `numpy` pin — transitive dependency, version resolved by pandera/pandas

## [0.3.0] — 2026-04-26

### Added
- `--export markdown` / `--export html` — generate schema docs without starting a server; embeds into README, Sphinx, or MkDocs
- `--coverage` flag — print documentation coverage (% of schemas and columns with `title`/`description`); also available as `GET /api/coverage` for CI quality gates
- `--watch` / `-w` flag — auto-reload schemas on `.py` file changes using `watchdog` (install via `pandera-ui[watch]`)
- `CoverageReport` Pydantic model in `pandera_ui.models`
- `pandera_ui._export` module with `to_markdown()` and `to_html()` functions
- `pandera_ui._coverage` module with `compute_coverage()` and `format_coverage()` functions
- `watch` optional extra: `pip install pandera-ui[watch]`
- MkDocs documentation site at [darius1223.github.io/pandera-ui](https://darius1223.github.io/pandera-ui/)

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
