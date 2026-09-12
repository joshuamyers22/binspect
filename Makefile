.PHONY: sync lint type test integration reference coverage coverage-expanded build check

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
	uv run --frozen --extra dev --extra dpi pytest tests/integration/test_dpi.py -m integration

reference:
	uv run --frozen --extra dev --extra validation pytest tests/integration/test_inference.py -m integration

coverage:
	uv run --frozen --extra dev --extra validation python validation/coverage.py --phase development

coverage-expanded:
	uv run --frozen --extra dev --extra validation --extra dpi python validation/expanded_coverage.py --phase development --output .work/expanded-coverage-development.json

build:
	uv build

check: lint type test integration reference coverage coverage-expanded build
