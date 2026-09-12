# Contributing to binspect

Thank you for helping improve `binspect`. Statistical correctness and clear public
behavior take priority over adding features.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
Repository work follows the [working agreement](AGENTS.md),
[brief](PROJECT_BRIEF.md), and [project plan](binspect-plan.md). Review ownership
and actual GitHub enforcement are recorded in [governance](docs/GOVERNANCE.md).
For security-sensitive changes, update the [threat model](docs/THREAT_MODEL.md).

## Development setup

Use Python 3.10 or newer in an isolated environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev,dpi,validation]"
```

For the exact CI dependency versions, use `uv sync --frozen --all-extras`.
`make check` runs the complete local quality gate, including DPI integration,
locked Statsmodels references and prespecified development coverage simulations.

Before opening a pull request, run the same checks as CI:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/pytest --cov -m "not external and not integration"
.venv/bin/pytest tests/integration -m integration
.venv/bin/python validation/coverage.py --phase development
.venv/bin/python -m build
```

The unit suite does not need binsreg. The `dpi-integration` CI job installs the
committed lockfile on Python 3.12 and runs real-library tests without skips or
`continue-on-error`. It is part of the required project quality gate; configuring
GitHub branch protection to enforce it is tracked separately by G1/R1. Neither
test suite makes runtime network calls.

`make reference` and `make coverage` run the separate `inference-validation` CI
gate using the explicit validation extra. Follow the
[analysis plan](docs/STATISTICAL_ANALYSIS_PLAN.md) before altering methods, scenarios,
seeds or tolerances. Development coverage is a regression gate for its stated
sanity cases; diagnostic failures must remain visible and do not establish broader
method validity. Locked assessment requires a committed plan/protocol and a clean
checkout, with its evidence retained for qualified review.

## Change guidelines

- Add a regression test for every bug fix and identity tests for statistical claims.
- Keep orchestration in `api.py`, calculations in `core`, and drawing in `viz`.
- Prefer small functions, descriptive names, immutable results, and actionable errors.
- Do not change a public default or output schema without updating the changelog.
- Treat verdicts and intervals honestly: current verdicts are descriptive heuristics.
  Ordinary intervals use independence assumptions; clustered intervals depend on
  the supplied cluster structure. Broader inference validation remains open in C3.

Open an issue before undertaking a large API or statistical-method change so effort
is not spent on a design that may not fit the project.
