# Review of PRs #16–#23

Date: 2026-09-12 (maintainer timezone). Reviewer/implementer: Codex, under the
user's explicit instruction to review, fix and merge open PRs. This is an agent
code review, not independent statistical or maintainer policy acceptance.

## Review contract

Baseline main: `25bf68c`; original stack tip: `54b197d`. Objective: inspect the
A1–P2 stack, correct supported defects and CI blockers, and merge passing PRs in
dependency order. Separate worktrees preserve the ongoing P3 working tree.

Invariants: owned results; positional Polars/pandas parity; strict, deterministic
exports; unchanged covariance conventions and numerical tolerances; unchanged
baseline PNGs and RMS limit; no release or policy acceptance claim. Existing
mutation, input/export, cluster/reference, documentation and rendering tests are
the safety net. Supported correctness, integrity or security defects and failed
applicable checks block merge. Bound: four evidence-changing passes per finding,
90 minutes; unresolved failures are reported without weakening gates.

## Findings and corrections

| Finding | Evidence | Disposition |
|---|---|---|
| High: declared integer categories lose identity during float conversion | Categories `2**53` and `2**53 + 1` produced an all-one dummy column instead of alternating zero/one; this can silently change adjustment | [Fix 609167c](https://github.com/joshuamyers22/binspect/commit/609167c) preserves declared category values. Two new weighted/unweighted regressions check exact design/metadata, slope against a full NumPy least-squares design, and the shared binsreg preparation boundary. |
| CI blocker: compatibility examples fail formatting | All eight PR #18 platform jobs failed Ruff formatting; #19 already contained the correction | [Fix 3d5ce17](https://github.com/joshuamyers22/binspect/commit/3d5ce17) carries that formatting back to #18. |
| CI blocker: figure runner cannot install requested Python patch | PR #20–#23 figure jobs failed before tests: setup-python could not find 3.12.14 for macOS arm64 | [Fix 378317c](https://github.com/joshuamyers22/binspect/commit/378317c) selects an available CPython 3.12 patch, matching the manifest's existing minor-version guard. Locked rendering packages, FreeType, font hashes, PNG bytes and RMS limit remain unchanged. Current setup instructions are corrected too. |

The fixes were carried forward using ordinary merge commits; no force push or
baseline regeneration. One changelog conflict retained both the categorical fix
and the DPI dependency-floor correction. No existing PR review comments were
present when checked. Code review covered ownership/copying, preparation and
category design, grouped/sample export identity, occupied-cluster CR1 arithmetic,
optional dependencies, workload guards, documentation execution and figure gates.
Local visual inspection included the audit baseline and grouped-controls gallery.

## Verification

- Original stack: `uv sync --frozen --all-extras` and `make check` passed with
  458 unit tests, 74 integration/reference tests and 94.65% coverage.
- Corrected implementation at `621abdf`: the same full gate passed with **460 unit
  tests**, **34 binsreg/DPI integrations**, **40 Statsmodels references**, and
  **94.65% coverage**. Ruff, strict mypy, all four import contracts, native use
  without pandas, all three development coverage protocols, 38 documentation
  blocks plus quickstart, strict MkDocs and wheel/sdist builds passed.
- All four baseline comparisons produced RMS **0.0**, with the existing 0.5/255
  ceiling. Local review used CPython 3.12.11 on macOS arm64 and the committed lock.
- Focused categorical tests: 35 Polars-contract tests passed at the corrected A2
  branch. Existing prespecified numerical tolerances were retained.
- Later changes to renderer instructions and this status record are documentation
  only; formatting/link/example checks apply. CI results on each final PR head
  are linked by the PR records below and checked before merge, not inferred from
  local tests or from an older head. Historical cancelled runs do not substitute
  for the final completed run.

[Ownership #16](https://github.com/joshuamyers22/binspect/pull/16),
[Polars/exports #17](https://github.com/joshuamyers22/binspect/pull/17),
[compatibility #18](https://github.com/joshuamyers22/binspect/pull/18),
[user guide #19](https://github.com/joshuamyers22/binspect/pull/19),
[figure exports #20](https://github.com/joshuamyers22/binspect/pull/20),
[gallery #21](https://github.com/joshuamyers22/binspect/pull/21),
[performance #22](https://github.com/joshuamyers22/binspect/pull/22),
[dependencies #23](https://github.com/joshuamyers22/binspect/pull/23).

The [plan](../binspect-plan.md) retains the outstanding qualification gates:
C3 independent statistical assessment, policy decisions, broader figure
qualification, accepted performance budgets/runner, P3 supply-chain work and
release readiness. The review does not run reserved assessment seeds, accept
performance budgets, publish a package/site or change remote security controls.
