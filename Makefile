.PHONY: format lint type-check check test

format:
	uv run ruff format cooltrader/

lint:
	uv run ruff check cooltrader/

type-check:
	uv run mypy cooltrader/

check: lint type-check

test:
	uv run pytest tests/

test-all:
	uv run pytest tests/ -m "not integration"
	uv run pytest tests/ -m "integration"
