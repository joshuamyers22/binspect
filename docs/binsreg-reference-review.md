# C3 reference review against binsreg

Date: 2026-09-12. Requested by the maintainer as the reference for reviewing C3.
Reviewer/implementer: Codex; accountable maintainer: Josh Myers. This records
independent upstream methods and executable comparisons, not approval by binsreg's
authors or a new empirical coverage guarantee.

## Sources and version boundary

Reviewed the locked Python binsreg 3.2.1 implementation, its public function
documentation, and the authors' methodological discussion. The repository and
package are [maintained upstream](https://github.com/nppackages/binsreg).
The [software paper](https://nppackages.github.io/references/Cattaneo-Crump-Farrell-Feng_2025_Stata.pdf)
describes function targets, bias-corrected intervals and implementation checks
(sections 2, 2.3 and 2.8.2). The foundational reference is
[On Binscatter](https://nppackages.github.io/references/Cattaneo-Crump-Farrell-Feng_2024_AER.pdf).

Source SHA-256 identities from the committed environment:

- `binsreg/binsreg.py`: `b84cd50088f62cff0059950c5ee7a93012c1d16daef22250346503bf493f2c54`
- `binsreg/funs.py`: `f980540d51f4097c07ee76505085bcadd799895f89f32c0796052ff892b4f519`

These hashes identify the reviewed installed files; upstream main may change.
The existing lock pins distribution integrity. No dependencies were upgraded.

## Comparison and disposition

| Topic | Reviewed binsreg 3.2.1 behavior | Implication for binspect |
|---|---|---|
| Adjusted target | Fits a spline basis in original x jointly with controls, evaluating controls at `at` (default their means). | This function target differs from bin means of mean-restored FWL residuals. Matching full-design linear slopes does not equate the binned estimands. |
| Control uncertainty | `asyvar=False` by default. `binsreg_pred` augments the evaluation design with controls and uses full coefficient covariance; `asyvar=True` omits that contribution. | Retain withdrawal of adjusted-bin SEs/CIs. Attaching binsreg's intervals to residual-space bins would change the estimand and requires a separate method design. |
| DPI and intervals | Default dots are degree 0, while `ci=True` uses degree 1 with continuity in the inspected path. Pointwise critical values are Gaussian. Higher-degree fitting addresses approximation bias for function inference. | Our DPI count alone does not give our t intervals binsreg's formal inference properties. Keep the population-interval-average target and limits of the development grid explicit. |
| Few clusters | Effective size is capped by cluster count; `dfcheck=(20,30)` adds checks based on the requested model's dimension. Small cases warn and may change bins/degrees, including fallback constant-fit intervals. | These checks are not a universal minimum safe cluster count. Do not copy 30 into a claimed reliability guarantee or silently replace requested methods. |
| Cluster covariance | Upstream fits a full design with cluster covariance. Our bin SEs use separate local intercept-only CR1 calculations with local corrections and t df. | Direct equality of every returned interval would be a mismatched comparison. Existing Statsmodels references deliberately match each claimed design/correction. |

The software paper's section 2 explicitly limits its stated guarantees under
dependent sampling. Its numerical safeguards are useful engineering references;
they do not resolve our observed 78.2% uneven-cluster coverage. This supports
retaining explicit limitations and withholding automatic clustered diagnostic
classification until a caller specifies a descriptive policy, without endorsing
the resulting covariance coverage.

## Executable evidence

Added four mandatory tests in
[test_binsreg_contract.py](../tests/integration/test_binsreg_contract.py), using
600 synthetic rows and development seed 92001, with no assessment-seed reuse:

- Two and three clusters with five requested bins issue small-effective-size
  warnings and change the CI method to `(0,0)`. They retain respectively two and
  three constant-fit intervals. The test records this fallback rather than claiming
  upstream refuses all intervals or that the fallback is reliable.
- At a fixed control evaluation value, default full uncertainty and `asyvar=True`
  have the same interval centers but different widths. The two options are not
  interchangeable first-stage treatments.
- Actual DPI with `ci=True` selects degree-0 dots and degree-1 intervals. These
  are distinct fitted objects, not intervals centered on the original bin means.

All four pass in the locked environment and join the existing six DPI checks in
`make integration` and CI. The C3 coverage protocols, failed evidence and numerical
tolerances remain unchanged. No final-assessment simulations were run here.

## Remaining work

The upstream reference review is complete. C3 still needs final assessment under
its reviewed estimand/claim contract and maintainer acceptance. Re-enabling adjusted
uncertainty or introducing a new clustered method requires separate validation.
The independent C4 policy correction is documented in
[its verification record](diagnostic-policy-review.md). This review does not
attribute endorsement or sign-off to upstream maintainers.
