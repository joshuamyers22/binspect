.PHONY: sync lint type test build check

sync:
	uv sync --frozen --all-extras

lint:
	uv run ruff check .
	uv run ruff format --check .

type:
	uv run mypy
	uv run lint-imports

test:
	uv run pytest --cov --cov-report=term-missing -m "not external"

build:
	uv build

check: lint type test build
