.PHONY: sync lint type test native integration reference coverage coverage-expanded coverage-binsreg docs figures benchmark dependencies build check

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
	uv run --frozen --extra dev --extra dpi pytest tests/integration/test_dpi.py tests/integration/test_binsreg_contract.py tests/integration/test_binsreg_adapter.py -m integration

native:
	uv run --isolated --frozen --no-dev python validation/native_smoke.py

reference:
	uv run --frozen --extra dev --extra validation pytest tests/integration/test_inference.py -m integration

coverage:
	uv run --frozen --extra dev --extra validation python validation/coverage.py --phase development

coverage-expanded:
	uv run --frozen --extra dev --extra validation --extra dpi python validation/expanded_coverage.py --phase development --output .work/expanded-coverage-development.json

coverage-binsreg:
	uv run --frozen --extra dev --extra validation --extra dpi python validation/binsreg_coverage.py --phase development --output .work/binsreg-coverage-development.json

build:
	uv build

docs:
	uv run --frozen --all-extras python validation/documentation.py
	uv run --frozen --all-extras mkdocs build --strict

figures:
	uv run --frozen --all-extras python validation/figures.py

# Run separately on the recorded host; shared CI is not an accepted timing runner.
benchmark:
	uv run --frozen --all-extras python validation/performance.py

# Fresh resolution needs network access; CI runs each configuration separately.
DEPENDENCY_PROFILE ?= minimal
DEPENDENCY_PYTHON ?= 3.12
dependencies:
	uv run --frozen --all-extras python validation/dependencies.py --profile $(DEPENDENCY_PROFILE) --python $(DEPENDENCY_PYTHON) --output .work/dependencies/$(DEPENDENCY_PROFILE)-$(DEPENDENCY_PYTHON).json

check: lint type test native integration reference coverage coverage-expanded coverage-binsreg docs figures build
