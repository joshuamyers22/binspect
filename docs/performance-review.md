# P1 — workload measurement and occupied cluster aggregation

- Owner: Josh Myers; implementer: Codex; baseline/runner acceptance: pending.
- Date / library baseline: 2026-09-12 / `e331e3a`, stacked on D3 PR #21.
- Status: implemented and locally verified on `perf/cluster-workloads`;
  maintainer baseline/runner acceptance and integration pending.
- Scope: [P1](../binspect-plan.md), adapted from the production-template
  performance experiment and local bounded verification agreement.

## Prespecified experiment

Hypothesis: replacing dense bin-by-cluster score/count arrays with aggregation over
occupied pairs removes O(B*C) auxiliary storage without changing CR1 counts, means,
SEs or interval conventions. The current calculation has two B*C arrays plus a
score-square temporary (approximately 24*B*C bytes on this host). Occupied pairs
are at most the positive-weight row count. The simpler alternative is an explicit
dense-allocation refusal; prefer occupied aggregation if numerical references pass.
Do not modify labels, FWL, zero-weight policy, Polars outputs or pandas conversion.

Safety net: existing direct-score and Statsmodels references, new crossed/nested/
unique-label and zero-weight/cancellation cases (rtol 1e-12, atol 1e-12), plus an
allocation guard that rejects bin*cluster-sized bincount output before allocation.
Any numerical mismatch, omitted workload/failure, misleading support claim or
unbounded benchmark child is High and blocks completion. Documentation gaps are
Medium. No seeds or numerical tolerances may be tuned after observing results.

Measure Polars preparation/estimation end to end (including the API's input
conversion and immutable-result copies), separately from Matplotlib construction
and Agg draw. Synthetic data generation/imports are outside timed regions but
inside whole-process peak RSS. Each trial uses a fresh child, one first call and
one warm repeat per stage, with garbage collection between calls. Rendering uses
precomputed results; check output equivalence outside timed regions. No parallel
benchmark workers. Record individual trials, median/min/max, hardware, lock/source
identity and numerical equivalence. First-call timing is not cold disk-cache timing.

Grid: 10k, 100k and 1M rows; base 20 bins; 100 bins; 100 clusters; clusters=n
with 100 bins; 4/16 groups; 4/16 numeric controls. All cases use PCG64 seed 130101
(fresh stream per size/specification). Three fresh trials per case, all rows used
for estimation. Render both default layers and a bins/CI/fit-only view for base and
near-row-count clusters; other cases use bins/CI/fit only. Group rendering includes
all facets. The harness does not sample estimation inputs. Inspection after the
baseline run confirmed that the existing default rug selects at most 2,000 marks;
default-render measurements include that built-in behavior, not a million rug marks.
Raw scatter, audit, export encoders and custom unbounded rugs are outside this grid.

Local resource ceiling: one child at a time, 120 seconds per trial and 2 GiB RSS;
stop/record that case on exceeding either limit. Monitor RSS from the parent and
terminate the child if exceeded; sampling is a guard, not a hard allocation limit.
Preflight skips legacy dense cases above 256 MiB predicted score/count/square
storage, records the reason, and never labels them measured. No 10M trial or
general capacity promise. Host is Apple M1 Pro, 8 logical CPUs, 16 GiB RAM, macOS
arm64; controlled thread settings are recorded. Host facts required an authorized
read outside the sandbox. This workstation is a candidate benchmark host, not an
accepted CI runner.

Maximum four evidence-changing phases / 90 minutes / local compute only: baseline
harness and measurements; aggregation plus reference/guard tests; candidate grid
and comparison; full gate/docs/review. Roll back the optimization on a supported
numerical mismatch. If a workload hits a cap, record it as unqualified and document
the bounded alternative; do not increase the cap to make it pass. Numeric timing/
RSS regression budgets must be derived from retained repeated measurements and
remain proposed until a maintainer accepts the baseline and controlled runner.
Implement comparison/enforcement without fabricating that acceptance.
Before candidate measurements, fix the proposal rule at 1.25 times each timing's
maximum trial and 1.20 times each RSS maximum. These are review candidates, not
statistical confidence limits or accepted support promises; excluded/capped cases
receive no budget. Enforcement must reject pending acceptance, changed environments,
missing/incomplete cases, and time/memory overruns.

## Evidence ledger

| Phase | Changed evidence | Result / next action |
|---|---|---|
| Baseline inspection | Dense score/count/square allocation and existing CR1 references | 100 bins × 1M clusters implies ~2.4 GB in those working arrays alone; allocation fix and measured envelope required. |
| 1 — baseline | Guarded harness, three trials × 30 workloads, 14 focused CR1/storage tests | 28 workloads measured; two 1M near-row-count cluster cases skipped before legacy dense allocation. Thirteen numeric cases passed on the legacy core; the allocation guard reproduced the dense failure before allocation. Hardware/RSS monitoring required authorized execution outside the sandbox. |
| 2 — candidate | Occupied-pair aggregation plus proposed-budget comparison/enforcement | All 35 focused tests (14 new CR1/storage, 13 existing bin estimates, eight budget checks) and strict mypy pass. Source committed at `3962f88` before candidate measurements. No method/default/tolerance change. |
| 3 — final measurement | Initial candidate grid plus fail-closed RSS monitor regression | Initial candidate passes all 30 workloads under the declared caps. A simulated failed `ps` probe exposed an overly permissive exit-code path; the monitor now terminates any still-running child when a probe fails. Three monitor regressions pass. Final baseline/candidate grids rerun sequentially with the identical final harness, using an isolated legacy source checkout. |
| 4 — full gate and disposition | Retained final grid, numerical comparison, real pending-budget rejection and full project checks | All 30 candidate workloads pass three trials; all 28 measurable legacy comparisons pass rtol/atol 1e-12. The final gate passes lint/format, strict types/import contracts, 454 unit tests, 74 integrations/references, native journey, development coverage, 38 documentation blocks/quickstart, strict site and four exact D2 baselines. Final build succeeds on authorized retry after sandbox DNS failure. |

## Measurement controls and limitations

Clock: Python `time.perf_counter`, wall seconds; no profiler runs inside timed
regions. Three fresh processes per workload each supply first/warm timings. Means,
SEs/CIs, counts, slope/intercept/SE, gap and partition edges/IDs are compared outside
timing with the prespecified tolerances. Repeat trials also require identical
numerical arrays. These checks accompany the stronger direct CR1 and Statsmodels
references; they do not validate new inferential claims.

The parent monitors RSS with `ps` and also records the child's `getrusage` peak;
Linux KiB versus macOS byte units are normalized explicitly. Time-limit, RSS-limit
and monitor-failure tests verify child termination/reaping. Missing/nonfinite
metrics, time/memory regressions, incomplete workloads and incompatible identities
are rejected by the budget checker. Proposed budgets are not marked accepted by
the implementation or tests (test acceptance records are synthetic fixtures).

Thread settings constrain Polars/BLAS/OpenMP libraries to one worker. The workstation
was not CPU-affinity isolated; governor, thermal/power state, firmware and unrelated
OS/background activity were not measured or controlled. First calls do not imply
cold filesystem caches. No tail percentiles, confidence bounds, concurrent-use
capacity or universal throughput claim is justified by three repeats here. These
limitations are why runner and numeric budget acceptance remain explicit open work.

The final legacy run uses a detached source checkout at `e331e3a` with the final
harness copied into it and `PYTHONPATH` selecting its `src` directory; the imported
library path was verified. The candidate uses the active checkout. Both run through
the same frozen environment, identical thread settings and harness bytes, one
after the other. Source hashes distinguish implementations; source commits remain
recoverable. Preliminary reports stay in ignored `.work/`; only final raw evidence
and proposed budgets are retained for review.

## Retained final measurements

All 30 candidate workloads pass three fresh trials under the prespecified caps.
The legacy core runs 28; its two 1M near-row-count cluster workloads are preflight
skips, not inferred measurements. All 28 comparable numerical vectors agree at
rtol/atol 1e-12. Each trial also passes first/warm output equivalence.

- [Legacy raw trials and identity](evidence/performance-baseline-2026-09-12.json)
- [Candidate raw trials and identity](evidence/performance-candidate-2026-09-12.json)
- [Numerical comparison](evidence/performance-comparison-2026-09-12.json)
- [Proposed budgets; acceptance pending](evidence/performance-budgets-2026-09-12.json)

Times below are warm-call median [min, max] in seconds across three fresh trials.
RSS is the maximum whole-process high-water mark in MiB, not isolated allocations.
Raw reports also retain first-call times, standard deviations and estimation peaks.

| Workload | Estimation seconds | Rendering seconds | Candidate peak MiB | Legacy peak MiB |
|---|---:|---:|---:|---:|
| base_10000 | 0.0019 [0.0019, 0.0019] | 0.0263 [0.0259, 0.0271] | 150.2 | 150.4 |
| bins100_10000 | 0.0021 [0.0021, 0.0022] | 0.0250 [0.0249, 0.0251] | 149.8 | 151.1 |
| clusters100_10000 | 0.0376 [0.0371, 0.0376] | 0.0271 [0.0268, 0.0282] | 149.5 | 149.8 |
| clusters_n_10000 | 0.0398 [0.0397, 0.0402] | 0.0247 [0.0241, 0.0251] | 150.3 | 197.6 |
| groups4_10000 | 0.0235 [0.0230, 0.0235] | 0.0757 [0.0756, 0.0758] | 150.8 | 151.4 |
| groups16_10000 | 0.0267 [0.0263, 0.0270] | 0.2727 [0.2649, 0.2757] | 157.8 | 157.3 |
| controls4_10000 | 0.0042 [0.0041, 0.0043] | 0.0271 [0.0264, 0.0285] | 156.1 | 156.0 |
| controls16_10000 | 0.0106 [0.0104, 0.0114] | 0.0281 [0.0270, 0.0282] | 174.5 | 171.6 |
| default_plot_10000 | 0.0019 [0.0018, 0.0019] | 0.0348 [0.0342, 0.0364] | 150.1 | 150.1 |
| clusters_n_default_10000 | 0.0395 [0.0392, 0.0396] | 0.0343 [0.0332, 0.0363] | 151.3 | 197.6 |
| base_100000 | 0.0157 [0.0151, 0.0158] | 0.0274 [0.0254, 0.0278] | 159.3 | 160.1 |
| bins100_100000 | 0.0171 [0.0169, 0.0175] | 0.0279 [0.0275, 0.0293] | 158.9 | 158.8 |
| clusters100_100000 | 0.3669 [0.3627, 0.3726] | 0.0273 [0.0265, 0.0273] | 167.9 | 167.9 |
| clusters_n_100000 | 0.3991 [0.3975, 0.4047] | 0.0276 [0.0271, 0.0277] | 191.9 | 431.0 |
| groups4_100000 | 0.2184 [0.2174, 0.2193] | 0.0716 [0.0712, 0.0727] | 167.8 | 168.3 |
| groups16_100000 | 0.2232 [0.2209, 0.2251] | 0.2677 [0.2666, 0.2715] | 173.7 | 172.9 |
| controls4_100000 | 0.0405 [0.0393, 0.0407] | 0.0285 [0.0276, 0.0290] | 227.0 | 223.9 |
| controls16_100000 | 0.1016 [0.1001, 0.1025] | 0.0267 [0.0257, 0.0300] | 243.4 | 243.8 |
| default_plot_100000 | 0.0147 [0.0147, 0.0148] | 0.0351 [0.0350, 0.0354] | 157.9 | 160.1 |
| clusters_n_default_100000 | 0.3933 [0.3901, 0.3961] | 0.0363 [0.0359, 0.0371] | 186.7 | 430.8 |
| base_1000000 | 0.1743 [0.1722, 0.1848] | 0.0250 [0.0248, 0.0270] | 272.5 | 286.9 |
| bins100_1000000 | 0.1927 [0.1902, 0.1933] | 0.0267 [0.0266, 0.0289] | 293.9 | 304.0 |
| clusters100_1000000 | 3.6707 [3.6455, 3.8634] | 0.0278 [0.0251, 0.0322] | 394.3 | 371.3 |
| clusters_n_1000000 | 4.1285 [4.0327, 4.1618] | 0.0317 [0.0279, 0.0322] | 554.3 | not run |
| groups4_1000000 | 2.2064 [2.2006, 2.2684] | 0.0719 [0.0695, 0.0767] | 367.5 | 397.4 |
| groups16_1000000 | 2.2589 [2.1970, 2.2652] | 0.2846 [0.2580, 0.2858] | 387.1 | 379.3 |
| controls4_1000000 | 0.4291 [0.4265, 0.4298] | 0.0276 [0.0262, 0.0289] | 598.2 | 580.8 |
| controls16_1000000 | 1.1863 [1.1825, 1.2387] | 0.0262 [0.0258, 0.0274] | 1193.3 | 1186.9 |
| default_plot_1000000 | 0.1792 [0.1769, 0.1795] | 0.0354 [0.0344, 0.0355] | 294.4 | 303.6 |
| clusters_n_default_1000000 | 4.0182 [4.0081, 4.0681] | 0.0369 [0.0367, 0.0378] | 554.2 | not run |

The recorded pending budget was passed to the real checker and rejected as
expected. Budget acceptance was not fabricated to obtain a passing gate.

The memory hypothesis is supported for high-cardinality clusters: 100k rows/
clusters at 100 bins falls from 431.0 to 191.9 MiB peak RSS, and the previously
skipped 1M case completes at 554.3 MiB. This does not imply uniform improvement:
at 1M rows with only 100 clusters, peak RSS rises from 371.3 to 394.3 MiB because
occupied-pair factorization adds row-sized temporaries where the old dense grid
was small. The largest candidate peak is 1193.3 MiB for 1M rows/16 numeric controls.
Keep these costs visible; no universal speedup or arbitrary-width control support
is claimed. Independent benchmark acceptance must consider this tradeoff.

## Disposition

The implementation is ready for maintainer review. Required local checks pass:
454 unit tests (27 new), 34 DPI/binsreg integrations and 40 Statsmodels references,
94.65% coverage, strict mypy on 38 source files and four import contracts. The
isolated native journey passes without pandas. All three development coverage
protocols pass required gates with pre-existing diagnostic failures still visible;
reserved assessment seeds were not run. Thirty-eight executable documentation
blocks plus quickstart and the strict site build pass. All four unchanged D2
baseline comparisons have RMS 0.0.

The `make check` invocation stopped only at its final build step when sandbox DNS
could not resolve hatchling. An authorized `uv build` retry produced the 0.1.1
wheel and sdist successfully; the earlier checks were not rerun unnecessarily.
The gate log remains ignored `.work/p1-check.log`. No dependencies, package version,
Polars/pandas boundary or statistical conventions changed.

Maintainer acceptance of the candidate baseline and controlled runner remains open.
The prepared numeric budgets cannot pass the accepted-budget gate until that review
is recorded; this change does not configure an unqualified timing CI job. General
capacity, 10M rows, combined worst cases and inference qualification remain open.
No unresolved local High/Medium finding remains in the declared implementation
scope. P2 dependency configurations is the next implementation item. No merge,
release, site publication or external runtime telemetry occurred.
