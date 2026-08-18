# Contributing to binspect

Thank you for helping improve `binspect`. Statistical correctness and clear public
behavior take priority over adding features.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

Use Python 3.10 or newer in an isolated environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Before opening a pull request, run the same checks as CI:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/pytest --cov -m "not external"
.venv/bin/python -m build
```

## Change guidelines

- Add a regression test for every bug fix and identity tests for statistical claims.
- Keep orchestration in `api.py`, calculations in `core`, and drawing in `viz`.
- Prefer small functions, descriptive names, immutable results, and actionable errors.
- Do not change a public default or output schema without updating the changelog.
- Treat verdicts and intervals honestly: current verdicts are descriptive heuristics,
  and current confidence intervals assume independent observations.

Open an issue before undertaking a large API or statistical-method change so effort
is not spent on a design that may not fit the project.
