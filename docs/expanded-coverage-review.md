# C3 expanded development coverage: evidence and disposition

Date: 2026-09-12. Implementer: Codex; accountable maintainer: Josh Myers.
Qualified reviewer: unassigned. Status: implemented and verified, pending review
and integration; this is development evidence, not final statistical acceptance.

## Prespecification and verification

The [expanded protocol](EXPANDED_COVERAGE_PLAN.md) was committed as `3cc3b65`
before simulations. The harness and CI changes were then committed as `710d5e1`.
The [aggregate development report](evidence/inference-expanded-development-2026-09-12.json)
comes from that clean protocol commit. Its embedded hashes match the committed
plan, script and unchanged dependency lock. Each scenario also records generated
input hashes, warnings, bin counts, valid/failed counts, and mean interval widths.

| Pass | Evidence | Disposition |
|---|---|---|
| 1 — protocol and harness | Eleven deterministic checks cover analytic targets against independent numerical quadrature, original interval IDs, right-side knot selection, failure denominators, gate semantics, sanitized errors and unexpected-error propagation. All pass. | No seed/tolerance adjustment; ready for prespecified development. |
| 2 — clean-commit development | Eight scenarios × 1,000 replicates; all complete without invalid estimates or per-replicate warnings. Fixed-nonflat and 60-cluster required coverage metrics pass. Uneven-cluster diagnostics fail as below. | Preserve every outcome. No estimator change or new supported-coverage claim. |
| 3 — quality and evidence review | 262 unit tests, 6 real DPI integrations, 40 independent inference references, 92.49% unit coverage, Ruff (81 files), strict mypy (28 source files), all three import contracts, both development protocols, and wheel/sdist builds pass. | Implementation ready for maintainer/qualified review; C3 acceptance remains open. |

`make check` completed every validation target, then the isolated build encountered
sandbox DNS failure fetching hatchling. Retrying only `make build` with network
permission succeeded. No statistical checks were skipped or tolerances relaxed.
The unit suite reports 18 expected adjusted-inference warnings; the existing DPI
integration suite reports one upstream timedelta deprecation warning.
Final documentation checks resolve all 80 relative links, verify report hashes
against `710d5e1`, confirm unchanged historical evidence/lock, and reject the
assessment CLI phase before output. Ruff's final 82-file format check and
`git diff --check` pass.

The run used Python 3.12.14, NumPy 2.5.2, SciPy 1.18.1, Statsmodels 0.15.0 and
binsreg 3.2.1 with PCG64 development seeds 71000–71007. The original plan,
withdrawal record, v1 locked report and lockfile remain unchanged. Reserved
assessment seeds 81000–81007 were not run. Reproduce this development report at
clean `710d5e1` with `make coverage-expanded`; output is also written to the ignored
`.work/expanded-coverage-development.json` file. CI uses the same command.

## Results and supported interpretation

The prespecified nominal-95% band is [92.243%, 97.757%]. Bin targets are true
population averages over the interval containing x=0; selected partitions have
random interval targets. Cluster slopes target 1.5 using the public CR1 SE and
reference df. All denominators are 1,000, including any invalid replicate as a miss.

| Scenario | Bin coverage | Slope coverage | Nominal-band outcome |
|---|---:|---:|---|
| Fixed bins, quadratic mean | 94.6% | Not evaluated | Required sanity case passes |
| Quantile bins, quadratic mean | 95.0% | Not evaluated | Diagnostic inside band |
| DPI bins, quadratic mean | 94.3% | Not evaluated | Diagnostic inside band |
| 60 balanced clusters | 94.1% | 93.5% | Both required sanity cases pass |
| 5 balanced clusters | 94.7% | 93.3% | Both diagnostics inside band |
| 2 balanced clusters | 94.3% | 94.2% | Both diagnostics inside band |
| 3 clusters sized 480/60/60 | **78.2%** | **91.7%** | Both diagnostics outside band |
| Same uneven sizes, reliability weights | **80.7%** | 92.6% | Bin diagnostic outside band |

DPI selected between 16 and 31 bins, calling the actual selector each time with
no fallback or clipping. A passing result for this one polynomial DGP does not
validate general post-selection inference, function-at-a-point intervals, formal
binsreg intervals, or simultaneous bands.

Three uneven clusters produced severe bin undercoverage despite exact arithmetic
agreement in prior reference tests. The unweighted slope also fell outside the
band. Matching CR1 formulas does not establish adequate population coverage, and
cluster count alone cannot define a safe threshold. The passing balanced two-cluster
case had mean bin-interval width 14.08 outcome units; its coverage result does not
establish precision or general usefulness. These Gaussian, independent-cluster
cases do not qualify arbitrary dependence, weights or cluster leverage patterns.

The required development gate passes because diagnostic deviations were explicitly
designated for reporting before execution. It would fail on any invalid replicate
or deviation in a required metric. This does not accept the known uneven-cluster
risk: public guidance now links the observed limitation, and a qualified reviewer
must decide the support policy before C3 sign-off. Adjusted-bin uncertainty remains
unavailable under the earlier correction.

## Remaining acceptance work

Josh Myers assigns a qualified reviewer to evaluate the estimands, coverage grid,
uneven-cluster support/diagnostic policy and scope of claims. Accept or amend the
protocol before using reserved fresh assessment seeds; preserve failures and use
new seeds if revising after assessment. No minimum safe cluster count or replacement
covariance estimator is inferred from these development results. C4 remains the
next implementation item after the applicable C3 disposition; its diagnostic
policy work can use this evidence without claiming statistical certification.
