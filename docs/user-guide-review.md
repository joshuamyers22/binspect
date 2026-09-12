# D1 — executable user guide and API reference

- Owner: Josh Myers; implementer: Codex; maintainer review pending.
- Date / baseline: 2026-09-12 / `e3c9bf2`, stacked on A3 PR #18.
- Task: D1 in [the production plan](../binspect-plan.md).
- Status: implemented and locally verified on `docs/executable-user-guide`;
  maintainer review/integration and hosting/publication pending.

## Contract before iteration

Build a navigable MkDocs user guide with a generated API reference. Execute its
Python examples and the quickstart in CI, and fail builds on invalid local links
and anchors. Cover original/adjusted estimands, reliability weights, missingness,
clusters and limitations, DPI/partitions, grouped support, gap versus R-squared,
Polars/pandas outputs and plot composition. Correct stale installation/version
and release-trigger documentation against actual metadata/workflows.

Keep numerical methods, defaults, optional pandas boundary, ownership and all
inference withdrawals unchanged. Synthetic examples are application journeys,
not coverage assessment. Existing unit/reference/plot tests are the safety net.
Build tooling must not publish or change hosting, read caller data, overwrite
tracked figures, fetch provenance or introduce runtime library I/O. Dependencies
already include MkDocs Material and mkdocstrings; prefer the frozen environment.

Required evidence: executed quickstart/guide examples, strict MkDocs build,
broken-example/link rejection checks, `make check` (workflow/tooling changes),
documentation consistency, built HTML inspection and final diff review. Blocking
High findings: silently skipped/failing examples, invalid support claims, broken
reference/build, numerical regressions or publication without authorization.
Missing guide coverage/navigation is Medium and must be resolved. Maximum four
evidence-changing passes / 90 minutes / local compute only. Stop when checks pass;
at the ceiling record remaining findings and the owner's next action. No test
tolerance changes, reserved assessment seeds, merges or releases.

## Evidence ledger

| Pass | Changed evidence | Check / disposition |
|---|---|---|
| Baseline | No MkDocs config/site or executable documentation gate; docs dependencies already locked | Existing quickstart writes tracked hero.png. D1 will give it an explicit output path and run it in temporary storage. |
| 1 | Twelve-page guide/reference site, source-generated members and executable Markdown runner | Covered all D1 journeys with native Polars defaults and optional pandas/DPI examples. First execution caught a new example incorrectly assuming JSON omitted the x/y name fields; corrected it to assert names rather than raw vectors. No schema change. |
| 2 | Strict site build, deliberate missing page/anchor and failing-example checks | Site builds; temporary broken links/anchors cause nonzero build exit. Six runner regressions cover execution/shared state, temporary outputs, failure traceback/line, malformed fences, non-Python exclusion and indented/longer fences. Generated HTML includes all 36/12/9 public fields/properties/methods for single/grouped/adapter result types. |
| 3 | Full gate, Markdown formatting and repository inclusion | Narrowed existing `site/` ignore to root `/site/` so guide source is tracked. Ruff formats README/A3/new guide blocks; A3 changes are formatting only. `make check` passes every stage through documentation; sandbox DNS blocks final Hatchling resolution. Authorized `uv build` retry builds both distributions successfully. |
| 4 | Final source/doc consistency, navigation/output inspection and diff review | Source edits are docstrings only (Polars projection, signed SD identity, withheld CI and explicit theme example). README examples now have seeded inputs. Contribution/release instructions match extras/version and the actual published-GitHub-release trigger. No publishing workflow or hosting change. |

## Verification results

`uv sync --frozen --all-extras` succeeds without lock changes. Full software stages:
Ruff lint/format, strict mypy (38 source files), four import contracts, **408 unit
tests**, **34 DPI/binsreg integrations**, **40 Statsmodels references**, **94.56%
coverage**, native estimation/export/plotting without pandas, and all three
prespecified development coverage gates pass. Existing uneven-cluster diagnostic
failures remain visible; no seeds/tolerances or numerical methods were changed.

`make docs` executes **28 Python blocks**: 15 across eight guide/start pages,
seven in README, two in the input/export contract and four in the compatibility
guide. The 25,000-row standalone quickstart also executes and produces a nonempty
PNG in temporary storage. MkDocs strictly builds all twelve pages, including three
source-generated API pages. Missing-page/anchor fault injection used copied
temporary docs/config and left the real source untouched. Six runner regressions
are included in the 408 unit tests. Warnings about sparse bins/adjusted inference
remain visible in applicable examples; none are silently suppressed.

The final `make check` command exits at build because sandbox DNS cannot fetch
Hatchling. An authorized `uv build` retry completes the wheel and sdist. This is
an environment-resolution retry, not a waived software/build failure. The gate log
is ignored `.work/d1-check.log`; preliminary docs evidence is `.work/d1-docs.log`.
No other-platform or clean-commit CI result is claimed by this local record.

Environment: macOS arm64, Python 3.12.14, MkDocs 1.6.1, Material 9.7.7,
mkdocstrings 1.0.6 and Python handler 2.0.7, using the unchanged committed lock.
The existing theme prints an upstream informational banner; MkDocs reports no
strict validation warnings in the successful build. External URLs are not fetched
or certified. Source docstring illustrations are generated reference material;
the executable contract is the explicitly authored Python guide/README blocks.

## Implementation pointers

- [MkDocs configuration](../mkdocs.yml) treats invalid local links, anchors and
  navigation as strict failures, and generates API documentation from source.
- [Guide](site/index.md) distinguishes unreleased 0.1.1 checkout behavior from
  proposed 0.2.0 and published 0.1.1; linked repository contracts remain canonical.
- [Runner](../validation/documentation.py) runs one fresh process/temp directory
  per page with Agg rendering and a 60-second timeout, retaining page/line errors.
  [Regressions](../tests/test_documentation.py) check failure behavior.
- [CI](../.github/workflows/ci.yml) adds a pinned-action, read-only documentation
  job; [Makefile](../Makefile) includes it in `make check`. No deploy step exists.
- [Quickstart](../examples/quickstart.py) defaults to `.work/quickstart.png` and
  accepts an explicit `--output`; tracked hero.png is unchanged.

## Review disposition

No unresolved local blocking finding remains. D1 implementation is ready for
maintainer review on top of A3/A2/A1. Hosting, publication authorization and
integration remain open; the site is built locally only. Package version remains
0.1.1; no library runtime behavior, inference contract, dependency lock or release
workflow was changed. No merge, deployment or release was performed.

M2 acceptance, qualified C3 statistical review/final assessment and dependency/
release gates remain open. This guide does not qualify PDF/SVG, accessibility or
pixel baselines; D2 exported-figure verification is the next implementation item.
The broader seeded-gallery work remains D3. Reserved assessment seeds were not run.
