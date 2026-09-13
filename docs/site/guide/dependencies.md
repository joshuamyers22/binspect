# Dependency configurations

Binspect prepares eager Polars inputs natively and returns Polars tables by
default. Pandas inputs remain compatible, and `.to_pandas()` explicitly converts
result tables. Native estimation and plotting work without pandas or binsreg.

The declared runtime minimums are NumPy 1.24, Polars 1.0, SciPy 1.10 and
Matplotlib 3.7. The `[pandas]` extra requires pandas 2.0. The `[dpi]` extra now
requires binsreg 3.2.1: binsreg 1.0 installed successfully but rejected the function
adapter's confidence-interval request. This is the dependency contract for release
0.2.0; the recovery checkout reports package version 0.2.1.

## What the checks cover

The dependency checks create a fresh environment for every row, install the
package noneditably, check dependency consistency, and run outside the checkout
with Python isolation. It exercises weighted and clustered estimates against
direct calculations, numeric/categorical adjustment, grouped results, Polars
tables, explicit pandas conversion, JSON/ownership, and headless PNG rendering.
Optional configurations also execute actual DPI selection and function fitting.
Missing-extra errors must name `binspect-regression[pandas]` or
`binspect-regression[dpi]`.

| Profile | Python in CI | Dependencies |
|---|---|---|
| `minimal` | 3.10, 3.11, 3.12, 3.13 | Locked runtime only; pandas and binsreg must be absent |
| `dpi` | 3.12 | Locked runtime and DPI extra, including upstream pandas |
| `locked` | 3.12 | All locked development, docs, validation and optional extras |
| `lower` | 3.10 | Exact direct runtime minimums; no pandas/binsreg |
| `lower-pandas` | 3.10 | Exact direct runtime minimums plus pandas 2.0 |
| `lower-dpi` | 3.10 | Exact direct runtime minimums plus binsreg 3.2.1; transitive dependencies resolve compatibly |
| `current` | 3.13 (weekly/manual maintenance) | Fresh compatible runtime, pandas and DPI resolution |

The nine locked/floor configurations run on PRs. Fresh-current checks run in the
separate weekly/manual maintenance workflow, alongside current-versus-locked
statistical references on Python 3.12. Josh Myers owns triage; unresolved numerical
divergences affecting supported methods block their next release. See the
[maintenance procedure](https://github.com/joshuamyers22/binspect/blob/main/docs/MAINTENANCE.md).

The floor checker verifies constraints against installed package metadata and
rejects accidental upgrades of direct minimums. DPI's upstream plotting stack
requires newer pandas than the standalone `[pandas]` minimum; that transitive
version is resolved in `lower-dpi`, while `lower-pandas` checks pandas 2.0 alone.
These profiles test each installable extra's direct minimums. They do not claim
that all optional minimum versions can coexist in one environment.

## Run a configuration

From the checkout, with uv and the requested Python available:

```sh
make dependencies DEPENDENCY_PROFILE=lower-pandas DEPENDENCY_PYTHON=3.10
make dependencies DEPENDENCY_PROFILE=current DEPENDENCY_PYTHON=3.13
```

Fresh resolution requires package-index access. The launcher deletes any old
result at the requested output path before starting and only writes a passing
JSON record after the checks finish. The record includes every installed version,
Python/platform, UTC check time, seed 140101, Git revision, and source/configuration
hashes. Records go to `.work/dependencies/` and are also printed in CI logs.
These separate jobs complement the existing full locked test matrix and
`make check`; they do not add fresh network resolution to that local gate.

## Scope of the evidence

Python 3.10–3.13 remains the configured support scope on Linux/macOS. The metadata
permits Python ≥3.10, but no 3.14+ qualification is added. Local macOS results and
the exact dependency versions are recorded in the
[P2 review](https://github.com/joshuamyers22/binspect/blob/main/docs/dependency-review.md).
Remote CI results and maintainer review remain separate evidence.

Current resolution is dated evidence, not a reproducible lock. Constraints limit
versions of dependencies that are installed; they do not themselves install every
listed package. See [uv's resolution and constraints documentation](https://docs.astral.sh/uv/pip/compile/).
Use the committed lock to reproduce numerical reference and image-baseline checks.
The isolated journeys do not qualify all admitted dependency combinations,
cross-version pixel identity, or statistical coverage. Only binsreg 3.2.1 has
the adapter's existing reference qualification; other versions retain unverified
method status. Supply-chain audits and release-artifact qualification remain
separate plan items.
