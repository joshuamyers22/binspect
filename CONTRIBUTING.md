# Contributing to binspect

Thank you for helping improve `binspect`. Statistical correctness and clear public
behavior take priority over adding features.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

Use Python 3.10 or newer in an isolated environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev,dpi]"
```

For the exact CI dependency versions, use `uv sync --frozen --all-extras`.
`make check` runs the complete local quality gate, including DPI integration.

Before opening a pull request, run the same checks as CI:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/pytest --cov -m "not external and not integration"
.venv/bin/pytest tests/integration -m integration
.venv/bin/python -m build
```

The unit suite does not need binsreg. The `dpi-integration` CI job installs the
committed lockfile on Python 3.12 and runs real-library tests without skips or
`continue-on-error`. It is part of the required project quality gate; configuring
GitHub branch protection to enforce it is tracked separately by G1/R1. Neither
test suite makes runtime network calls.

## Change guidelines

- Add a regression test for every bug fix and identity tests for statistical claims.
- Keep orchestration in `api.py`, calculations in `core`, and drawing in `viz`.
- Prefer small functions, descriptive names, immutable results, and actionable errors.
- Do not change a public default or output schema without updating the changelog.
- Treat verdicts and intervals honestly: current verdicts are descriptive heuristics,
  and current confidence intervals assume independent observations.

Open an issue before undertaking a large API or statistical-method change so effort
is not spent on a design that may not fit the project.
