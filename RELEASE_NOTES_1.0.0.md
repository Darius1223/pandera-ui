## pandera-ui 1.0.0

Stable 1.0 release of pandera-ui: a Swagger-like UI and documentation toolkit for Pandera schemas.

### Highlights

- Introduced a searchable browser UI for `DataFrameSchema` and `DataFrameModel`.
- Implemented two-pass schema extraction (runtime import + AST fallback).
- Added CLI export modes: `--json`, `--export markdown`, and `--export html`.
- Added documentation coverage reporting via `--coverage` and API endpoint support.
- Added watch mode (`--watch`) for live schema refresh.
- Shipped MkDocs documentation and GitHub Pages publishing workflow.
- Hardened project quality gates with linting, type checks, tests, and packaging checks.

### Upgrade notes

- No migration steps are required for first-time users.
- Install with:
  - `pip install pandera-ui`
  - or `uv add pandera-ui`
