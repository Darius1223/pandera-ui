# Contributing

## Setup

```bash
git clone https://github.com/darius-krsk/pandera-ui
cd pandera-ui
uv sync
uv run playwright install chromium
```

## Run tests

```bash
uv run pytest tests/ -q
```

## Manual testing

```bash
uv run pandera-ui tests/fixtures
```

Then open http://localhost:8765.

## Pull requests

- One feature or fix per PR
- Add a test for any new extraction behavior
- Run `uv run pytest` and `uv run mypy pandera_ui/` before submitting
