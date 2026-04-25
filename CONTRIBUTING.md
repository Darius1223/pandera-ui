# Contributing

## Setup

```bash
git clone https://github.com/darius-krsk/pandera-ui
cd pandera-ui
make setup
make setup-ui-tests
```

## Quality checks

```bash
make lint
make type
make test
```

## UI tests

```bash
make setup-ui-tests
make test-ui
```

## Coverage run

```bash
make test-cov
```

## Manual testing

```bash
make run
```

Then open http://localhost:8765.

## Raw commands (without Makefile)

```bash
uv sync
uv run playwright install chromium
uv run ruff check .
uv run mypy pandera_ui/
uv run pytest tests/ -q --ignore=tests/test_ui.py
uv run pytest tests/test_ui.py -q
uv run pytest tests/ -q --tb=short --ignore=tests/test_ui.py --cov=pandera_ui --cov-report=term-missing
uv run pandera-ui tests/fixtures
```

## Pull requests

- One feature or fix per PR
- Add a test for any new extraction behavior
- Run `make lint`, `make type`, and `make test` before submitting
