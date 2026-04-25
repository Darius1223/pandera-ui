.PHONY: setup setup-ui-tests lint format type test test-ui test-cov run ci

setup:
	uv sync

setup-ui-tests:
	uv run playwright install chromium

lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy pandera_ui/

test:
	uv run pytest tests/ -q --ignore=tests/test_ui.py

test-ui:
	uv run pytest tests/test_ui.py -q

test-cov:
	uv run pytest tests/ -q --tb=short --ignore=tests/test_ui.py --cov=pandera_ui --cov-report=term-missing

run:
	uv run pandera-ui tests/fixtures

ci: lint type test-cov
