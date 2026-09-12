# C3 continuation: withdraw adjusted-bin uncertainty and enforce identification

- Date: 2026-09-12; baseline `8331653`, stacked after PR #10.
- Implementer: Codex; accountable maintainer: Josh Myers; qualified review pending.
- Status: implemented and locally verified; review/integration pending. This is a proposed supported-behavior change,
  not a new estimator or acceptance of residual inference risk.

## Contract before implementation

The [locked assessment](evidence/inference-coverage-2026-09-12.json) found 87.4%
population coverage for nominal 95% adjusted-bin intervals. Descriptive bin means
and validated full-design slopes remain useful. Withdraw public adjusted-bin SEs,
confidence limits and their reference df until a reviewed first-stage uncertainty
method exists. Return NaN (JSON null), retain means/dispersion/counts and slope SEs,
and issue an actionable warning when an adjusted interval is requested. `ci=None`
explicitly requests descriptive bins without the warning. Shared adjusted bins
remain rejected. Do not invent an alternative estimand or reuse consumed seeds.

Also test numerical identification before residualization. An x already in the
control span must fail explicitly rather than estimate a slope from roundoff.
Control duplicates may remain if x adds rank. Normalize design columns by their
weighted Euclidean norms for rank/least-squares decisions so changing control units
does not silently drop a control or change residual df. Use NumPy's documented
default [SVD rank cutoff](https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_rank.html)
(largest singular value × max(shape) × machine epsilon);
this is numerical identification, not a weak-instrument/statistical-strength test.
No new arbitrary condition-number threshold is introduced.

Safety net: new before/after API regressions for withdrawal and exact confounding;
retain existing reference checks for the old bin-uncertainty primitive separately
from the public API; add matched references for redundant/rescaled controls and
few/unbalanced clusters. Existing tolerances stay rtol=1e−9, atol=1e−11 for
well-conditioned equivalent designs. Test numerical-rank refusal at singularity,
not a fabricated accuracy guarantee for arbitrarily near-singular designs.

Blocking findings: returning adjusted uncertainty as supported, altered identified
slope meaning, lost rank/weight semantics, discarded reference/coverage failures,
or failing required checks. At most three evidence-changing review passes and
90 minutes; local/read-only GitHub and existing CI, no publication/settings changes.
Stop when this rubric passes; leave broader C3 scenarios and qualified acceptance
explicitly open. User continuation authorizes preparing/pushing the reviewable fix.

## Coverage protocol amendment

The original analysis plan and locked JSON stay unchanged. Current development
checks keep seeds 41000–41004 as regression cases. For the withdrawn adjusted
formula, first assert that the public result suppresses uncertainty, then evaluate
the existing low-level bin primitive only as a labelled historical diagnostic.
This preserves the 89.2% failure as evidence rather than erasing or repairing it
through changed tolerances. Such internal arithmetic is not supported adjusted
inference. The current CLI must refuse a new assessment using consumed v1 seeds;
historical reproduction remains available at clean `c19c2a8`.

This pass adds deterministic numerical/reference cases, not new Monte Carlo
assessment evidence. Nonflat/DPI and broader few-cluster coverage, a reviewed
adjusted uncertainty method, and a qualified statistical reviewer remain C3 work.

## Evidence and disposition

- Before the implementation, all 12 initial regressions failed: four adjusted
  weight/cluster combinations still returned unsupported uncertainty, six scaled
  confounding cases and one zero-weight-only identification case returned a slope,
  and descriptive adjustment retained bin SEs. After correction, those cases plus
  numerical near-singularity pass (13 tests). Existing grouped regressions now
  check withdrawal in both pooled and individual results while preserving slopes.
- Added 12 Statsmodels full-design references for redundant controls scaled by
  1e−12, 1 and 1e12 across weight/cluster combinations. Four additional cases match
  CR1 slope arithmetic with two balanced clusters or three clusters sized
  160/20/20. These do not establish few-cluster coverage. All 24 earlier reference
  cases remain, including the withdrawn adjusted primitive's arithmetic checks;
  no tolerance was relaxed.
- `make check` passed on Python 3.12.14: 251 unit tests, 6 real DPI integration
  tests, 40 inference references, 92.49% unit coverage, Ruff (78 files), strict
  mypy (28 source files), all three import contracts, wheel and sdist builds.
  The unit suite reports 18 expected adjusted-inference warnings from existing
  calls; the DPI suite reports one upstream NumPy timedelta deprecation warning.
- Development replay retained all five outcomes, with zero failed replicates:
  iid 95.5%, weighted 95.1%, clustered 95.9%, withdrawn adjusted formula 89.2%
  (outside the original band), unadjusted quantile 94.2%. All three required
  unadjusted sanity cases pass; adjusted public suppression is a hard assertion.
  Generated-input SHA-256 remains
  `003088e89bf9e87e4cc9b1c2280ce2ec65ac57c84c10231dee1a30d5206b8a54`.
  This run used the development working tree, not a new locked assessment.
- The original analysis plan, locked assessment JSON and dependency lockfile
  remain unchanged. The amended CLI rejects assessment before generating inputs;
  v2 development reports label the withdrawn formula explicitly.
- Reviewed the API, strict JSON, summary, plotting and grouped paths: adjusted
  bins expose no SE/CI/reference df or confidence artists; slope covariance and
  df retain the existing contract. Public guidance and changelog describe the
  behavior change and the warning opt-out.
- All 72 relative links in the changed documentation resolve, the updated README
  adjustment example executes without its warning, and format/diff checks pass.

The bounded implementation gate passes. C3 remains open for expanded nonflat/DPI
and few-cluster coverage under a new prespecified assessment protocol, plus named
qualified review. Re-enabling adjusted-bin uncertainty requires a separately
validated method. Column normalization does not promise numerical accuracy for
arbitrary near-singular designs or extreme weights; capacity/conditioning work
remains in A2/P1. No independent acceptance or release approval is implied.
