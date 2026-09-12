.PHONY: sync lint type test integration build check

sync:
	uv sync --frozen --all-extras

lint:
	uv run ruff check .
	uv run ruff format --check .

type:
	uv run mypy
	uv run lint-imports

test:
	uv run pytest --cov --cov-report=term-missing -m "not external and not integration"

integration:
	uv run --frozen --extra dev --extra dpi pytest tests/integration -m integration

build:
	uv build

check: lint type test integration build
