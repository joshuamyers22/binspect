# D2 — exported figures and rendering baselines

- Owner: Josh Myers; implementer: Codex; maintainer visual acceptance pending.
- Date / baseline: 2026-09-12 / `519cf69`, stacked on D1 PR #19.
- Task: D2 in [the production plan](../binspect-plan.md).
- Status: implemented and locally verified on `test/figure-exports`;
  maintainer visual acceptance/integration pending. No general accessibility or
  cross-platform acceptance implied.

## Contract before iteration

Preserve artist/axes identity, scoped rcParams, numeric results and Polars/pandas
contracts. Add four justified raster baselines: default, paper, audit and standalone
deviation. Pin renderer/dependency/font inputs and record the actual host. Compare
pixel arrays with a prespecified RMS ceiling of 0.5 on the 0–255 scale; fail on
shape differences. This small antialiasing allowance is not a license to accept
missing layers, clipped text or altered data. Independently test those behaviors.
Baseline creation is an explicit review action, never an automatic failing-test fix.

Exercise PNG, PDF and SVG output for missing intervals, negative slopes, long
labels, multiple panels and caller axes. Check labels/geometry before export and
inspect generated artifacts. Record grayscale, protan/deutan/tritan simulations
and white/light-gray/dark-background observations for named themes. Simulation
and local visual inspection do not certify accessibility; label failing/unreviewed
combinations explicitly. Preserve existing palettes unless a bounded supported-path
defect requires correction. Do not add a dark theme or claim general print quality.

Required evidence: focused structural/export regressions, reproducible four-image
comparison, deliberately changed-image and renderer-mismatch failure checks,
visual inspection/contact sheets, strict docs and full `make check`. Block High
findings: missing/mislocated estimates/intervals, clipped supported-layout labels,
state leakage, silent baseline regeneration, or unsupported claims. Incomplete
scope/documentation is Medium and must be resolved. Maximum four evidence-changing
passes / 90 minutes / local compute only. At the ceiling record remaining findings
and next owner/action; never relax numerical/reference or image thresholds.

Use synthetic data only, no assessment seeds. Write disposable render/export
outputs under ignored `.work/`; commit only four baselines, their manifest and
small review evidence. No new runtime I/O, deployment, merge or release. Maintainer
visual acceptance and statistical/release qualification remain separate.

## Evidence ledger

| Pass | Changed evidence | Result / disposition |
|---|---|---|
| Baseline | Existing artist/state tests, named themes and locked renderer inspected | No image baselines/export gate. Local renderer: Matplotlib 3.11.1, FreeType 2.14.3, Pillow 12.3.0 on Python 3.12.14/macOS arm64. Palette docstring makes unqualified color-vision/printing claims that require correction. |
| 1 | Four explicit initial baselines, renderer/font/hash guard, export geometry/text tests | First geometry probe counted locator ticks outside the view and hidden labels on shared axes. The check now inspects actual tick objects within view limits, retaining the one-pixel canvas-edge allowance. No layout/default or numerical tolerance changed. |
| 2 | PNG/PDF/SVG checks, deliberate missing-mark/shape/renderer failures and baseline overwrite guard | 19 new checks pass: 15 format/scenario combinations plus partial-CI position preservation, image-regression rejection, renderer mismatch rejection and protected baseline output. Four same-environment baseline comparisons have RMS 0.0 against the prespecified 0.5 ceiling. |
| 3 | Visual inspection of four baselines, long-label/negative/facet/missing-CI artifacts and three 15-panel simulation/background sheets | Main estimates/labels are intact on the tested light backgrounds. Dark backgrounds lose text/context, especially paper estimates. Notebook/deck luminance does not guarantee separation; near-coincident lines, short deck legend handles and faint raw/residual marks require care. Documented limits and removed universal palette claims; palette values unchanged. |
| 4 | Final full gate, strict guide build and diff/dependency review | `make check` completes successfully: 427 unit tests, 34 DPI/binsreg integrations, 40 Statsmodels references, 94.64% coverage, all development coverage gates, native journey, 29 documentation blocks/quickstart, strict site, four baseline comparisons and wheel/sdist builds. |

## Evidence and scope

The [four PNGs and manifest](../tests/baseline/README.md) are explicit initial
review candidates, not independent visual acceptance. Default composition is
720×460, paper 550×360, audit 864×644 and standalone deviation 720×460. Baselines
were visually inspected at their rendered sizes. The audit's residual marks are
faint; this is recorded rather than described as universally readable. Baseline
comparison checks dimensions/alpha and RGB RMS, and validates baseline hashes.
It never silently skips a mismatched renderer or writes into baseline storage
without the explicit replacement flag. The initial set was generated once;
no failing-image-driven regeneration or threshold adjustment occurred.

The [portable tests](../tests/test_figure_exports.py) parse PDF with pypdf and SVG
with the standard XML parser, checking text, page dimensions and format structure.
PNG dimensions and nonblank content are checked. Label/tick/title geometry is
checked on the Agg canvas before export, with caller dimensions and rcParams
preserved. Partial missing-CI segments retain the correct x/low/high coordinates
without dropping bin markers. PDF/SVG pixel equivalence, every reader/printer,
unbounded label lengths and tagged-document accessibility are not qualified.

The [guide and three contact sheets](site/guide/figure-exports.md) retain the
qualitative grayscale/color-vision/background evidence. The
[measurement record](evidence/figure-colors-2026-09-12.json) reports linear
luminance and contrast ratios for nominal palette-text swatches, not every
rendered artist or a conformance threshold. Nominal dark-background text ratios
are 1.08–1.14. Original/grayscale/severity-100 protan/deutan/tritan views were
inspected for notebook/paper/deck on white, #F2F2F2 and #202124: 45 panels total.
Neutral-gray simulation output was checked within one 8-bit channel level.

Color simulation uses Machado, Oliveira and Fernandes (2009),
[DOI 10.1109/TVCG.2009.113](https://doi.org/10.1109/TVCG.2009.113), severity-100
numerical matrices checked against
[colorspacious' transcription](https://github.com/njsmith/colorspacious/blob/master/colorspacious/cvd.py).
The original authors' server timed out during retrieval; this transcription
explicitly identifies their supplementary data. The local implementation decodes
sRGB, applies matrices in linear RGB, clips gamut and re-encodes. It does not fetch
anything during checks. Simulation is not a substitute for accessibility testing
with users. Dark/transparent-on-dark presets remain unsupported/unqualified;
recommend opaque white exports and explicit layout/legend space.

## Environment and verification

`uv sync --frozen --all-extras` and final `make check` pass. Ruff/format, strict
mypy (38 source files), four import contracts and the isolated native installation
without pandas pass. All required statistical gates pass with existing uneven-
cluster diagnostic failures preserved. The full gate log is ignored
`.work/d2-check.log`; export artifacts/simulation originals are in ignored
`.work/figure-review`. Reserved assessment seeds were not run.

The only dependency addition is development-only pypdf 6.18.1 for actual PDF
parsing. Its lock/install required an authorized retry after sandbox DNS failure;
the final full gate/build needed no retry. Existing numerical/runtime dependencies
are unchanged. Lock SHA-256:
`b8fdf6e1b0243cfb90c63cbf292dd8700347b76b56b3bd8244891612a9dbf40e`.

Local host: macOS 15.1 arm64, CPython 3.12.14, Matplotlib 3.11.1, NumPy 2.5.2,
SciPy 1.18.1, Pillow 12.3.0 and FreeType 2.14.3. The manifest hashes bundled
DejaVu Sans/Serif fonts and records rc settings. Version/font sensitivity follows
[Matplotlib's image-comparison guidance](https://matplotlib.org/stable/api/testing_api.html).
The dedicated CI job uses macos-15 (arm64 per the
[GitHub runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners))
and Python 3.12.14 with the frozen lock and renderer guard. That configured job
is not a claim of a completed remote CI run or immutable OS image; host details
are recorded separately from the compared renderer inputs. Portable structural
checks remain in the normal Python/OS unit matrix; broader qualification is P2.

## Review disposition

No unresolved local High finding remains within the declared export scope.
The supported-path renderer behavior and numeric results are unchanged; the only
library-source edits correct palette documentation/comments. Maintainer visual
acceptance of the initial baselines and integration remain pending. No merge,
deployment, release or independent statistical acceptance occurred.

General accessibility, custom/dark backgrounds, print/viewer pixel equivalence,
M2/C3 acceptance and release/dependency gates remain open as documented. D3
reproducible examples is the next implementation item.
