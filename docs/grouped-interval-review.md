# C2: grouped coordinates and interval identity

- Date: 2026-09-12; baseline `0fb4770` (stacked after PR #8).
- Implementer: Codex; accountable reviewer: Josh Myers.
- Status: locally verified, ready for maintainer review; no statistical or policy
  acceptance implied.

## Bounded verification contract

Objective: prevent unsupported shared adjusted coordinates and preserve the identity
and true bounds of occupied intervals across grouped results and exports.
Scope: the C2 rejection path explicitly authorized in the plan; interval metadata,
table/JSON consistency, group-labelled estimation errors and regression evidence.
No new adjusted estimand, covariance convention, dependency or remote policy.

Invariants: retain existing observation assignments and numerical estimates; keep
compact indices inside estimation and legacy compressed edges available; tables
must identify the original occupied intervals without stretching across empty ones.
Shared bins must use the same complete partition for pooled and group results.
Unadjusted and independently adjusted group fits remain supported.

Blocking failures: incorrect interval joins/bounds, changed fit meaning, silent
unsupported combinations, lost error cause, or failing required checks. Safety net:
the AR4 shifted-control reproduction, independent interval-membership calculations,
and direct per-group estimation comparisons. Use synthetic data only.

Ceiling: three evidence-changing review passes and 90 minutes, local tests/builds
and existing GitHub CI; no publication or resource-exhaustion experiments. Stop
when the rubric passes; otherwise report unresolved findings and next owner/action.
Run focused regressions before the fix, then `make check` and documentation checks.
Acceptance remains maintainer review; C3 independently validates inference.

## Coordinate and export contract

Controls are fitted separately in the pooled sample and each group, with each
sample restoring its own weighted x/y means. These coordinates are not common.
Reject `controls` with `common_bins=True` before fitting, and explain
`common_bins=False` as the supported alternative. Widening pooled edges would not
establish a common adjusted estimand. A future shared-adjustment design remains a
separate reviewed decision; this change does not invent one.

The full partition retains empty intervals. Estimation still uses only occupied
bins with compact indices. Table `bin` values identify intervals in the full
partition and may contain gaps; table bounds are those original intervals.
For shared bins, an ID has the same bounds in every group and the pooled result.
For independent bins, IDs are local to each partition and cannot be joined across
groups as matching x ranges. JSON records both the full partition/occupied IDs and
legacy compressed edges, plus the corrected table rows. Existing no-gap results
keep their IDs and bounds.

## Evidence and disposition

| Pass | Evidence | Result / correction |
|---|---|---|
| 1: reproduce | Added shifted-control and independently calculated interval-membership regressions against `0fb4770`. | 9 failures / 3 passes: generic adjusted-range error, absent full partition/IDs, missing group context on invalid weights. |
| 2: implement | Added the guard, full partition/occupied IDs, table/JSON projection, exception context and compatibility tests. | 86 focused tests passed. The first focused plotting run selected a macOS GUI backend and aborted; the comparison test module now explicitly selects Agg, as the existing plotting suite does. |
| 3: verify | Full gate and documentation checks; expanded DPI-option tests to both grouped partition modes. | The new coordinate guard intentionally precedes DPI validation when both are invalid; tests retain the DPI-specific guard check for independent groups and verify no backend call in either case. Final results below. |

The independently calculated regression uses original interval inequalities,
weighted sample means and a full-design least-squares coefficient reference.
It covers quantile, equal-width and custom partitions; disjoint support; empty
outer/interior intervals; edge ties; missing y/group rows; and retained/dropped
zero weights. Separate cases verify group-labelled failures preserve their causes,
legacy Binning construction, and standalone table bounds. Existing DPI selection,
cluster uncertainty, rendering and architecture tests remain in the full gate.

`make check` passed: 228 unit tests, 6 locked DPI integration tests, 92.02%
coverage, lint/format, strict mypy, all 3 import contracts, wheel and sdist builds.
The first isolated build hit PyPI DNS restrictions in the sandbox; the authorized
network rerun completed the entire gate successfully. Six changed
documents, 47 local links and 5 Python examples passed checks; diff whitespace is
clean. The upstream mizani deprecation warning is still visible.

Compatibility: no-gap IDs/bounds and numerical estimates retain their meaning.
Consumers indexing result arrays by table `bin` must now use the row's compact
position or `interval_ids` mapping; consumers of interval bounds should use table
bounds/full partition rather than legacy compressed edges. These intentional
corrections are documented in the changelog and public API docs.

Stop condition: local rubric passed. Maintainer review/integration remains open.
Shared adjusted coordinates remain
unsupported; C3 inference references/coverage and A1 ownership are separate tasks.
No statistical qualification, independent acceptance, remote policy change or
release is claimed by this implementation.
