# Workload measurements and limits

The development implementation aggregates clustered bin scores only for occupied
bin–cluster pairs. This removes the former dense bin-count × cluster-count working
arrays while preserving the CR1 formula, positive-weight cluster counts and
undefined intervals for bins containing one cluster. Sorting occupied pair IDs
adds work; this change is primarily a memory bound, not a universal speedup.

The reduction's score/count storage grows with represented pairs (at most the
number of positive-weight rows), plus bin outputs. Other parts still allocate
row arrays and label objects. Numeric control adjustment uses dense matrices and
can dominate peak memory as control width grows. Polars inputs/results remain
native; this does not promise zero-copy processing or a conversion speedup.

## What is measured

P1 uses synthetic Polars frames of 10k, 100k and 1M rows, with 20/100 bins,
100/near-row-count clusters, 4/16 groups and 4/16 numeric controls. Each workload
has three fresh processes, each recording first and warm calls. Timed estimation
includes API input preparation and result ownership copies. Data generation and
imports are outside the timer. Rendering measures figure construction plus Agg
draw from a precomputed result, separately from estimation.

The default plot has an existing **2,000-mark rug cap**. The comparison view draws
only bins, CI and fit. Group plots include every facet. These measurements do not
cover raw scatter, custom unlimited rugs, audits, file encoders, pandas conversion,
the optional binsreg backend, categorical control expansion, or every combination
of groups, controls and clusters.

Peak RSS is the whole process high-water mark, including imports, generated data,
temporaries and allocated renderer caches. The post-estimation high-water mark is
recorded separately; subtracting the two is not an isolated rendering allocation
measurement. The parent samples child RSS every 0.1 seconds and terminates a trial
over 2 GiB or 120 seconds. A sampling guard can overshoot between samples; it is not
an OS memory reservation or a runtime limit imposed on library callers.

## Observed on the recorded workstation

Apple M1 Pro (8 logical CPUs, 16 GiB RAM), macOS arm64, Python 3.12.14,
NumPy 2.5.2, Polars 1.44.2, SciPy 1.18.1 and Matplotlib 3.11.1.
The complete grid passed all 30 candidate workloads, three trials each. The table
shows selected warm medians and maximum whole-process RSS, with all trials and
workloads retained in the repository evidence. These are local observations,
not an accepted support ceiling or cross-platform timing promise.

| Workload | Rows | Estimation s | Rendering s | Peak MiB |
|---|---:|---:|---:|---:|
| base | 1,000,000 | 0.174 | 0.025 | 272.5 |
| clusters100 | 1,000,000 | 3.671 | 0.028 | 394.3 |
| clusters_n | 100,000 | 0.399 | 0.028 | 191.9 |
| clusters_n | 1,000,000 | 4.128 | 0.032 | 554.3 |
| groups16 | 1,000,000 | 2.259 | 0.285 | 387.1 |
| controls16 | 1,000,000 | 1.186 | 0.026 | 1193.3 |
| default_plot | 1,000,000 | 0.179 | 0.035 | 294.4 |

At 100k rows/clusters and 100 bins, peak RSS fell from 431.0 to
191.9 MiB. The legacy 1M-cluster cases were not run: predicted dense
working storage exceeded the predeclared safety limit. All 28 mutually
measured numerical cases agree within rtol/atol 1e-12; the two new 1M cases
are explicitly separate from that legacy comparison. Control-width memory
and Python label preparation remain costs; a memory improvement does not
establish a general time speedup.

## Reproduce and compare

From the checkout on the recorded benchmark host:

```sh
uv sync --frozen --all-extras
make benchmark
```

Output defaults to ignored `.work/performance.json`. The harness records CPU/RAM,
OS, Python/dependencies, library/harness/lock hashes, seed and thread settings. It
runs children sequentially with one numerical/Polars worker thread, and checkpoints
each completed workload. Operating-system permission to inspect child RSS is
required; a missing monitor fails instead of running unguarded. Use `--sizes 10000`
for a shorter prespecified subset. Do not compare a partial grid as though all
workloads ran. Ten million rows remain exploratory and are not accepted by this
bounded harness.

The [repository performance record](https://github.com/joshuamyers22/binspect/blob/main/docs/performance-review.md)
retains baseline/candidate evidence and comparison results. Numerical comparison
uses the prespecified rtol/atol 1e-12, including missing-value locations, and reports
unmeasured/capped cases separately. Timing reports show individual trials and
median/min/max/standard deviation; three trials do not support tail-latency claims.
First call means first API/renderer use in a fresh process, not a cold disk cache.

```sh
uv run --frozen --all-extras python validation/performance_check.py \
  .work/performance.json --reference baseline.json
uv run --frozen --all-extras python validation/performance_check.py \
  .work/performance.json --propose .work/proposed-budgets.json
```

Budget proposals use 1.25 × each measured maximum timing and 1.20 × each peak RSS
maximum. They are review candidates, not confidence intervals or service promises.
The maintainer must accept both the baseline and controlled runner before timing
budgets can become a required gate. Acceptance fields record that review; the tool
does not authenticate or grant approval. Enforcement rejects pending acceptance,
environment changes, incomplete/missing workloads and timing/memory overruns:

```sh
uv run --frozen --all-extras python validation/performance_check.py \
  .work/performance.json --reference accepted-baseline.json --budget accepted-budgets.json
```

`make check` keeps portable numerical and allocation regressions; it does not run
timing benchmarks on an unqualified shared CI host. Accepted runner/budget setup is
still pending. Repeated measurements on this workstation do not establish general
hardware capacity, concurrent-call safety or statistical validity at high cluster
counts. See [cluster inference limits](weights.md) independently of memory scaling.
