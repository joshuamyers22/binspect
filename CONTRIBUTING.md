# Contributing to binspect

Thank you for helping improve `binspect`. Statistical correctness and clear public
behavior take priority over adding features.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
Repository work follows the [working agreement](AGENTS.md),
[brief](PROJECT_BRIEF.md), and [project plan](binspect-plan.md). Review ownership
and actual GitHub enforcement are recorded in [governance](docs/GOVERNANCE.md).
For security-sensitive changes, update the [threat model](docs/THREAT_MODEL.md).

## Development setup

Use Python 3.10 or newer in an isolated environment. For the exact CI dependency
versions and all documentation examples, use:

```bash
uv sync --frozen --all-extras
make check
```

`make check` runs the complete local quality gate, including DPI integration,
locked Statsmodels references and prespecified development coverage simulations.
For an unlocked editable environment, the equivalent extras are
`python -m pip install -e ".[dev,dpi,validation,docs]"`; that does not reproduce the lock.
It also runs `make native` in an isolated installation without pandas, exercising
Polars input, categorical/weighted/clustered estimation, grouped controls, exports
and plots. Pandas compatibility is tested in the all-extras environment. Native
tabular code must not import pandas; convert only at the optional boundary.

Run `make dependencies DEPENDENCY_PROFILE=lower-pandas DEPENDENCY_PYTHON=3.10`
for an isolated dependency check. See the [profile matrix](docs/site/guide/dependencies.md)
for minimal/DPI/locked/floor/current configurations and Python scope. These jobs
require index access and run separately from `make check`; output records contain
the actual installed versions and source/configuration hashes.

Run `make benchmark` separately for the sequential 10k/100k/1M workload grid.
It needs permission to read child-process RSS and enforces a 2 GiB/120-second
trial ceiling. Read [measurement boundaries and limits](docs/site/guide/performance.md)
and [P1 evidence](docs/performance-review.md) before making performance claims.
Numeric budget proposals require explicit maintainer baseline/runner acceptance;
`validation/performance_check.py --budget ...` refuses pending or incompatible
evidence. Shared CI runs numerical/allocation/guard regressions, not an unaccepted
timing gate. Never regenerate or relax a budget solely to erase a regression.

Before opening a pull request, run the same checks as CI:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/pytest --cov -m "not external and not integration"
.venv/bin/pytest tests/integration -m integration
.venv/bin/python validation/coverage.py --phase development
.venv/bin/python validation/expanded_coverage.py --phase development
.venv/bin/python validation/binsreg_coverage.py --phase development
make docs
make figures
.venv/bin/python -m build
```

The unit suite does not need binsreg. The `dpi-integration` CI job installs the
committed lockfile on Python 3.12 and runs real-library tests without skips or
`continue-on-error`. It is part of the required project quality gate; configuring
GitHub branch protection to enforce it is tracked separately by G1/R1. Neither
test suite makes runtime network calls.
`make integration` also checks the locked binsreg inference contract: control
uncertainty, higher-degree function intervals and small-cluster fallbacks. See
the [reference review](docs/binsreg-reference-review.md) for the estimand differences.

`make reference` and `make coverage` run the separate `inference-validation` CI
gate using the explicit validation extra. Follow the
[analysis plan](docs/STATISTICAL_ANALYSIS_PLAN.md) before altering methods, scenarios,
seeds or tolerances. Development coverage is a regression gate for its stated
sanity cases; diagnostic failures must remain visible and do not establish broader
method validity. Locked assessment requires a committed plan/protocol and a clean
checkout, with its evidence retained for qualified review.
The [protocol amendment](docs/adjusted-inference-boundary-review.md) preserves
the failed adjusted formula as a low-level development diagnostic and checks that
the public API withholds its uncertainty. Current reports use schema version 2
with an explicit scope for each scenario. The original plan and locked report are
unchanged. The CLI refuses consumed v1 assessment seeds; reproduce the historical
assessment at clean `c19c2a8`. New assessment requires a reviewed new protocol.

`make coverage-expanded` adds the
[prespecified nonflat/DPI and few-cluster grid](docs/EXPANDED_COVERAGE_PLAN.md)
to `make check` and the same CI job. It requires both validation and DPI extras,
writes `.work/expanded-coverage-development.json`, and retains diagnostic coverage
failures while requiring every replicate to complete. The harness permits only
development seeds; qualified review and a separate locked assessment remain open.
See the [results and limitations](docs/expanded-coverage-review.md).

`make coverage-binsreg` tests the separate optional function-inference adapter,
following its [committed protocol](docs/BINSREG_ADAPTER_PLAN.md). It requires
zero invalid runs and checks iid DPI coverage against a prespecified band;
clustered coverage remains diagnostic. Reports include actual method/status
histograms in `.work/binsreg-coverage-development.json`. `make integration` checks
adjusted, weighted, clustered, filtered and categorical inputs against direct
binsreg, including degree-0 few-cluster fallback. Assessment seeds remain reserved.

## Change guidelines

Run `make supply-chain` for the separate online advisory/license/history/artifact
gate. It uses isolated locked tooling and fails on unavailable evidence or
unapproved findings. See [scope and pending license reviews](docs/SUPPLY_CHAIN.md).
Dependency updates must regenerate `uv.lock` and rerun `make check`, affected P2
profiles and this audit; CI rejects stale locks and retains numerical drift gates.

The [user guide](docs/site/index.md) and generated API reference build from
`mkdocs.yml`. `make docs` executes every plain `python`/`py` fenced block in the
site, README and input/compatibility contracts, in page order with one fresh process
and temporary working directory per page. Keep examples self-contained on each
page and use synthetic data; do not add a silent skip marker. It also runs the
standalone quickstart with an explicit temporary image path and builds MkDocs
strictly, including local links, anchors and navigation. External links are not
fetched. Docstring illustrations in generated reference pages are not part of the
executable-guide suite. The dedicated CI `documentation` job runs the same target.

Preview with `uv run --frozen --all-extras mkdocs serve`. Generated `site/` output
is ignored. This build does not configure hosting or publish a site; maintainer
publication approval and configured hosting remain separate requirements.

`make figures` compares four reviewed PNG candidates using the renderer/font
manifest in [tests/baseline](tests/baseline/README.md); `make check` includes it.
Use CPython 3.12 and the frozen lock for this qualification gate. The dedicated CI
job pins Python 3.12.14 on macos-15; the normal unit matrix runs portable PNG/PDF/SVG
structure, text, geometry and state tests (pypdf is development-only). Renderer
mismatches and image differences fail; baseline replacement requires an explicit
command, visual diff inspection and maintainer review. Do not relax thresholds.
Generate disposable color/background review sheets with
`uv run --frozen --all-extras python validation/figure_accessibility.py`.

- Add a regression test for every bug fix and identity tests for statistical claims.
- Keep orchestration in `api.py`, calculations in `core`, and drawing in `viz`.
- Prefer small functions, descriptive names, immutable results, and actionable errors.
- Do not change a public default or output schema without updating the changelog.
- Follow the proposed [compatibility policy](docs/COMPATIBILITY.md): update the
  [API inventory](docs/API_INVENTORY.md), supported option matrix and executable
  migration examples when a public contract changes. Assign the release by actual
  compatibility impact; policy acceptance and publishing require maintainer review.
- Treat verdicts and intervals honestly: current verdicts are descriptive heuristics.
  Ordinary intervals use independence assumptions; clustered intervals depend on
  the supplied cluster structure. Broader inference validation remains open in C3.

Open an issue before undertaking a large API or statistical-method change so effort
is not spent on a design that may not fit the project.
