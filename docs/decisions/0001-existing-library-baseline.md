# ADR-0001: Retain the existing library baseline during production hardening

- Status: proposed for maintainer review in G1; documents current choices, not
  proof that exceptions or statistical methods have been approved.
- Date: 2026-09-12.
- Owner: Josh Myers, maintainer identified in package metadata.
- Scope: binspect 0.1.1 production-hardening plan.
- Supersedes: none.

## Context and forces

The production template defaults to Polars for quantitative tabular work,
Statsmodels for regression/inference, Pyright for strict Python types, Python
3.11+ support, and proprietary licensing in generated projects. It also permits
project-specific, evidence-backed departures and omits containers for libraries
when they add no value.

binspect is an existing MIT library whose public inputs/results include pandas.
Its core uses NumPy/SciPy, with optional binsreg selection. Strict mypy and a
Python 3.10–3.13 matrix already exist. A blanket template copy would change its
dependency footprint, compatibility, and potentially distribution terms without
establishing improved correctness. Existing green tests do not establish that
custom inference should be retained without stronger validation.

Evidence: [manifest](../../pyproject.toml),
[API](../../src/binspect/api.py), [results](../../src/binspect/results.py),
[numerical core](../../src/binspect/core/lines.py),
[CI](../../.github/workflows/ci.yml), and [review](../project-plan-review.md).

## Options considered

1. Convert the public/data pipeline to Polars, replace the statistical engine with
   Statsmodels, and migrate type/runtime tooling as a prerequisite.
2. Retain the existing library boundaries and tools, document their costs, and
   require independent statistical and performance evidence before stabilizing.
3. Retain everything indefinitely based on the existing test suite.

Option 2 is proposed. Option 1 risks unrelated API/dependency churn before known
defects are fixed; option 3 ignores confirmed defects and inference uncertainty.

## Proposed decision

- Keep pandas at named input/control/label/table boundaries and NumPy arrays in
  numerical calculations. Inventory pandas use inside core helpers and either
  justify the narrow categorical boundary or move preparation outward. Do not
  add a Polars pipeline until measurements/user needs justify it.
- Retain current NumPy/SciPy estimators conditionally. C3 must specify each
  covariance/weight/design contract and compare it against matched, locked
  Statsmodels references. If equivalence or coverage is unsupported, change the
  implementation or withdraw the supported claim; this ADR is no waiver.
- Keep Statsmodels in the explicit validation environment rather than introducing
  it as an unconditional runtime requirement merely for template conformity.
  Pin/test optional binsreg independently.
- Keep strict mypy and the tested Python 3.10–3.13 range for this milestone.
  Runtime support and type-checker changes need measured benefits and a
  compatibility decision. Keep uv, its authoritative lock, Ruff, and pytest.
- Preserve MIT distribution terms and package/import names. Do not copy a
  generated proprietary license.
- Use library packaging and CI instead of a Docker/deployed-service skeleton.
  Service config, auth, health endpoints, runtime dependency exports, hosted
  telemetry, and backups do not apply without a deployable application.

## Consequences and verification

Public compatibility and a small runtime dependency set are preserved. Costs
include maintaining the pandas boundary, custom-estimator validation, and explicit
exceptions to reusable defaults. G1 records acceptance or revision; C1–C4,
A1–A3, and P1–P2 supply the evidence. Numerical failures are not acceptable
exceptions just because a dependency change would be inconvenient.

Reconsider this decision if independent inference checks fail, pandas conversion
is a measured bottleneck, the public API needs another backend, mypy leaves a
demonstrated boundary gap, or the project gains a deployable service. Prefer a
bounded adapter change with migration/reference tests over an unmeasured rewrite.
License changes always remain a separate owner decision.

Security/release controls are defined and reviewed through G2/P3/R1–R3, not
approved by this ADR or by the agent drafting it.
