# C4 diagnostic policy and claims

Date: 2026-09-12. Baseline: `276d936`, stacked after PR #12.
Implementer: Codex; accountable maintainer: Josh Myers. Status: implemented and
locally verified, pending review/integration.
C3 qualified review and locked assessment remain open. This bounded C4 slice
changes descriptive decisions and explanations; covariance/coverage qualification
is not a prerequisite for correcting these independent diagnostic defects.

## Contract before implementation

Expose an immutable `DiagnosticPolicy` through `binscatter` and `compare`, with
gap threshold 0.02 and minimum bin effective sample size 30 by default. Preserve
`linear`/`curvature` as explicitly heuristic labels; replace `underpowered bins`
with `limited support` because no power calculation exists. Equality at the gap
threshold selects curvature; equality at the support threshold is sufficient.
`diagnostic_policy=None` suppresses classification (`not assessed`, reason disabled)
while retaining every estimate and decomposition. Policy values must be finite,
nonnegative for gap, at least one for effective rows; reject booleans/invalid types.

Retained zero-weight rows never supply diagnostic support. Export raw retained
counts, positive-weight counts, Kish effective sample sizes and represented
positive-weight cluster counts separately, including per-bin support and minima.
Use effective rows for the default support rule. Keep `n_obs`, bin `n`, and
`min_bin_n` as legacy retained counts; describe them accurately.

No default safe cluster threshold can be inferred from the C3 failures. Default
clustered verdicts are `not assessed` (reason cluster policy required). Callers may
explicitly set `min_bin_clusters` (integer at least two), applying both that count
and the effective-row threshold. This is a caller-chosen descriptive screening
policy, never a guarantee of covariance coverage or an acceptance of C3 risk.
Constant positive-weight outcomes use the existing zero gap/eta-squared convention
and `not assessed` (reason constant outcome), without claiming support for linearity.

Correct the signed SD identity to slope_OLS = abs(r)*slope_SD, including negative
and exactly zero covariance, where the SD reference keeps positive orientation.
State FWL equality for observation-level residuals only; a bin-mean regression
generally differs. Deviation lengths/areas do not equal weighted squared gap.
Preserve numerical estimators and original coverage protocols/reports unchanged.

Safety net: reproduce misleading zero-weight and concentrated-weight support,
constant-outcome and sparse-cluster classification before changes. Add boundary,
opt-out, strict JSON/group propagation and weighted signed-SD identity tests.
Block misleading claims, lost policy propagation, altered estimates, invalid
strict JSON or failing required checks. Three evidence-changing passes and 90
minutes; run frozen `make check`, review docs/examples, then push a draft.
No settings, release, qualified acceptance or independent approval is implied.

## Evidence and disposition

| Pass | Evidence | Disposition |
|---|---|---|
| 1 — reproduce | All four initial cases failed: retained zero-weight rows and concentrated weights were labelled linear, constant outcomes were labelled linear, and the three-cluster case was classified without an explicit cluster policy. | Correct support and decision semantics without changing estimators. |
| 2 — implement/reference | 29 policy regressions cover failures, exact cutoff boundaries, validation, scale invariance, per-bin/global counts, grouped opt-out/policy propagation, strict JSON and audit captions. Signed-SD checks now cover both signs and zero covariance with/without weights. Four new locked binsreg method checks pass. | Requested [binsreg review](binsreg-reference-review.md) informs explicit scope; no upstream endorsement or covariance guarantee. |
| 3 — full gate | `make check`: 296 unit tests, 10 real binsreg integrations, 40 independent Statsmodels references, 92.60% unit coverage, Ruff (87 files), strict mypy (29 files), all three import contracts, both development coverage protocols and wheel/sdist builds pass. | Implementation ready for maintainer review. |

The first full-gate pass identified the strict table-column expectation that needed
the two newly documented support fields. Updating that schema assertion and checking
unweighted support equals retained counts resolved it; the full gate then passed.
The suite reports 18 expected adjusted-inference warnings and one upstream timedelta
deprecation warning. No tolerance was relaxed and no dependency changed.
All 75 relative links in the changed guidance resolve. The README policy example
executes and both enabled/disabled results encode as strict JSON; final Ruff
format/lint and diff checks pass.

All eight expanded development outcome records are exactly identical to the retained
report, including failures, widths and input hashes; original coverage sanity cases
also pass. Original plans, scripts and evidence remain byte-for-byte unchanged.
The default classifier now withholds clustered verdicts; it does not change CR1
estimates or resolve C3's uneven-cluster undercoverage. Constant-outcome gap and
eta-squared remain zero by convention with an explicit unassessed reason.

C4's bounded implementation is complete; maintainer acceptance and integration
remain open. The requested upstream reference review is complete, while C3 final
assessment/acceptance remain separate. The next independent implementation is A1
result ownership and mutation isolation. No release/settings action was taken.
