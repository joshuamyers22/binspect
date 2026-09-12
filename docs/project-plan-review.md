# Adversarial review of the project plan

Date: 2026-09-12. Baseline: `59c6a39` on `main`, package `0.1.1`.
Scope: the original project plan, public documentation, numerical paths, existing
tests, packaging configuration, and tracked workflows. This is a planning review
with targeted implementation probes, not an exhaustive code or security audit.

**Conclusion:** production hardening must precede new statistical features.
The previous blanket completion claim is unsupported, and several contracts are
incorrect. The [replacement plan](../binspect-plan.md) supplies ordered tasks,
dependencies, and acceptance criteria. Implementation findings below remain open.

The first rewrite did not use the production project template. The subsequent
[template alignment](template-alignment.md) records its direct application,
additional repository/security/supply-chain gates, and scoped exceptions. It
supplements these findings rather than treating the earlier review as template
conformance evidence.

P1 means a misleading statistical claim, incorrect supported behavior, or a
material release-readiness gap. P2 means an integrity, operability, or planning
gap that must be resolved before claiming production readiness.

## Findings and disposition

| ID | Priority | Finding and evidence | Disposition |
|---|---|---|---|
| AR1 | P1 | The original plan claims v0.1–v0.4 completion including HC1, while `api.py` has no covariance selector and `core/lines.py` provides classical/cluster slope SEs. The proposed external workflow, documentation site, and image baseline suite are absent from tracked files. Installed test plugins do not establish those tests exist. | Completion claim removed. Baseline separates implementation from validation. C3, D1–D2, R1–R3 remain open. |
| AR2 | P1 | `core/selection.py:_select_dpi` returns `out.nbinsrot_regul`, a ROT result, for a DPI request. It also instructs users to install the wrong distribution extra. The adapter receives x/y only despite public weights/clusters/partition options. | C1 is the next task. Reproduction below confirms distinct DPI and returned values. |
| AR3 | P1 | The original FWL claim asserts equality for a slope through bin means. FWL preserves the full-model coefficient through observation-level residualization; aggregation changes the regression. The weighted saturated-fit claim also incorrectly names OLS instead of WLS. | Plan corrected. C3–C4 require independent equivalence checks and synchronized source/README wording. |
| AR4 | P1 | `comparison.py:compare` selects pooled adjusted edges, then residualizes each group independently and restores its own means. Coordinates can differ enough for the default common-bin call to fail. Empty bins also collapse and renumber within groups, weakening interval identity. The existing controls comparison test uses `common_bins=False`. | C2 requires a defined coordinate contract and stable interval identity; an explicit unsupported-combination error is an acceptable interim fix. |
| AR5 | P1 | Independent and clustered bin intervals are calculated after control residualization. FWL coefficient equality does not establish coverage for these adjusted bin means. Per-bin CR1 uses local cluster counts, unlike the old promised blanket equality with a global saturated-model correction. Current matrix/score tests check arithmetic but do not demonstrate coverage or matched external equivalence. | C3 requires an estimand/covariance/df specification, matched references, and simulations. Coverage failure is a validation risk, not asserted as a reproduced defect. |
| AR6 | P1 | `core/lines.py:fit_sd_line` signs its reference slope, but its docstring and the original plan multiply that slope by signed r. This gives the wrong sign for negative correlation. The identity test uses only the positive-slope fixture. Claims in `core/decompose.py` and `viz/layers.py` that displayed marks/area equal weighted lack of fit also omit weighting, squaring, or normalization. | Correct identities recorded in the plan. C4 covers source prose and sign/degeneracy regression tests. |
| AR7 | P1 | The original feature queue treats median/IQR displays as quantile regression and leaves uniform bands without an estimand or inference design. IQR measures dispersion, not estimator uncertainty; mean residualization cannot simply be transferred to quantile regression. | Separate descriptive and inferential designs; defer to F1–F2 after qualification. |
| AR8 | P2 | `core/decompose.py` uses fixed verdict thresholds and raw bin counts. Retained zero-weight observations can improve that count without adding statistical information. README's promise that zero-weight rows never affect point estimates is too broad because retained rows can move partitions. | C4 requires configurable/exported heuristic policy and explicit support measures. Plan distinguishes direct fit effects from partition-mediated effects. |
| AR9 | P2 | `BinscatterResult` is frozen, but its nested arrays remain writable. Mutating stored x can leave fit coefficients and tables describing different data. Serialization lacks a full record of selector and inference choices. | A1–A2 require ownership, mutation, and provenance contracts. Probe below confirms writable result data. |
| AR10 | P2 | `core/estimate.py:estimate_bins` allocates dense arrays with `n_bins * n_cluster_values` entries for scores and represented clusters. The original 10M-row benchmark aspiration has no measured time/memory budget. With 40 bins and 1M clusters, two 8-byte arrays alone are about 640 MB, before intermediates and input storage. | P1 requires measured scaling and a bounded or sparse aggregation path before high-cardinality claims. No large-memory experiment was run. |
| AR11 | P2 | The plan calls release publishing tag-triggered, while `release.yml` uses `release: published`. CI builds do not establish clean installation of wheel/sdist outside the checkout or successful artifact handoff. Repository configuration alone cannot establish deployed environment protections. | Correct trigger documented; R1–R3 add artifact, configuration, release, and recovery evidence. No publishing was performed. |
| AR12 | P2 | The plan mixes current APIs with unsupported `bands=`, nonexistent `bin_rule`, a DataFrame description for `decomposition`, a wrong distribution-name skeleton, resolved design questions, and an unordered feature wishlist. It calls every visualization arithmetic boundary import-linter-enforced. | Replace speculative API/tree templates with source-linked contracts, correct architecture scope, and stable milestone IDs. D1/A3 carry remaining cross-document synchronization. |

### Supporting upstream references

The upstream Python selector documents separate ROT and DPI outputs, supporting
AR2's distinction. Pin a supported version when implementing the adapter.
See [binsregselect source](https://github.com/nppackages/binsreg/blob/main/Python/binsreg/src/binsreg/binsregselect.py).

Cluster covariance corrections and inferential degrees of freedom are separate
choices; a reference comparison must configure both explicitly. See
[statsmodels covariance configuration](https://github.com/statsmodels/statsmodels/blob/main/statsmodels/base/covtype.py).

Covariate adjustment and formal binscatter inference require a method-specific
design. These are reasons to validate the existing adjusted-bin behavior and use
an established backend for future formal inference, not proof that the current
intervals fail in every setting. See Cattaneo, Crump, Farrell, and Feng,
[On Binscatter (2024)](https://nppackages.github.io/references/Cattaneo-Crump-Farrell-Feng_2024_AER.pdf).

## Reproducible probes

Run from the reviewed checkout using its existing development environment.
These probes demonstrate findings; they have not been added as permanent tests
because this change updates the plan rather than implementing the fixes.

### AR2 — DPI request returns ROT

```python
import numpy as np
import binspect
from binsreg import binsregselect

rng = np.random.default_rng(7)
x = rng.normal(size=4000)
y = np.sin(x) + rng.normal(scale=0.4, size=x.size)
upstream = binsregselect(y=y, x=x)
result = binspect.binscatter(x=x, y=y, bins="dpi")
print(upstream.nbinsrot_regul, upstream.nbinsdpi, result.binning.requested_bins)
```

Observed with binsreg 3.2.1 and NumPy 2.5.2: `35 65 35`. Exact numbers can change
with upstream versions; the contract defect is selecting the ROT field for a DPI
request.

### AR3 and AR6 — false algebraic identities

```python
import numpy as np
import binspect
from binspect.core.lines import fit_ols, fit_sd_line

x = np.arange(6.0)
r = binspect.binscatter(x=x, y=x**3, bins=2, ci=None)
between = fit_ols(r.estimates.x_mean, r.estimates.y_mean, weights=r.estimates.n)
print(r.fit.slope, between.slope)

fit = fit_ols(x, -x)
sd = fit_sd_line(x, -x)
print(fit.slope, fit.r * sd.slope, abs(fit.r) * sd.slope)
```

Observed: observation slope `23.8`, bin-means slope `23.0`; signed-SD example
`-1.0 1.0 -1.0`. The no-controls case already disproves the general bin-means
identity. Sparse-bin warnings are expected in this tiny demonstration.

### AR4 — valid grouped controls fail with default common bins

```python
import numpy as np
import binspect

rng = np.random.default_rng(0)
group = np.repeat(["a", "b"], 100)
control = rng.normal(size=200) + np.repeat([-3.0, 3.0], 100)
x = 5 * control + rng.normal(size=200)
y = x + control + rng.normal(size=200)
binspect.compare(x=x, y=y, group=group, controls=control, bins=5)
```

Observed: `InvalidBinningError: custom edges must cover the full range of x`,
with the first group's adjusted range approximately `[-17.69, -11.51]`.
These are internally selected pooled edges, not invalid edges supplied by a caller.

### AR9 — frozen container does not freeze data

```python
import numpy as np
import binspect

r = binspect.binscatter(x=np.arange(100.0), y=np.arange(100.0), bins=5)
r.x[0] = 10000.0
print(r.x[0], r.fit.slope)
```

Observed: `10000.0 1.0`. Mutation succeeds while the stored fit remains unchanged.

## Validation and limits

Baseline command: `.venv/bin/pytest --cov --cov-report=term -m "not external"`.
Result: **160 passed, 90.41% coverage**, Python 3.12.14, on 2026-09-12.
The targeted probes above expose gaps despite that green baseline.

Inspected tracked source, tests, README, contribution/reproducibility/release
instructions, pyproject configuration, and CI/release YAML. Verified upstream
selector terminology and covariance-reference configuration against primary
sources. No remote branch-protection settings, PyPI publisher configuration,
coverage simulations, large-data benchmarks, or new release artifacts were
validated in this review.

This documentation change corrects the planning failures and records implementation
work. C1–R3 remain open; no production-readiness claim follows from this review.
