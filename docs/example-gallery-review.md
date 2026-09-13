# D3 — reproducible synthetic example gallery

- Owner: Josh Myers; implementer: Codex; maintainer review pending.
- Date / baseline: 2026-09-12 / `b9b9db5`, stacked on D2 PR #20.
- Task: D3 in [the production plan](../binspect-plan.md).
- Status: implemented and locally verified on `docs/reproducible-gallery`;
  maintainer review/integration pending.

## Contract before iteration

Provide executable seeded linear, nonlinear, heteroskedastic, clustered, weighted,
discrete-x and grouped-control examples, with visible figures and explanations of
both useful and misleading interpretations. Use seven independent PCG64 streams,
seeds 120101–120107, solely for synthetic teaching examples. Do not run reserved
assessment seeds, search seeds for favorable pictures, or treat examples as coverage
validation. Record versions, source/lock identity and reproducible numerical outputs.

Keep Polars inputs/results and explicit optional pandas conversion; numerical
methods, defaults, runtime dependencies and plotting behavior stay unchanged.
The Markdown gallery is the single source of executable examples and runs in the
existing documentation gate. A checkout-only launcher retains artifacts at an
explicit destination; generated output defaults to ignored `.work/`.

Existing numerical/plot contracts and documentation execution are the safety net.
Check mathematical identities and case-specific limitations within the examples;
verify two fresh runs reproduce data/result/image hashes on the recorded host.
Inspect every figure, run strict docs and the full gate for executable changes.
Retain synthetic images plus a compact manifest, not raw data or logs.

Block High errors: incorrect estimands, misleading inference/causal claims,
unexecuted code presented as reproducible, lost Polars semantics, or destructive
default output. Missing planned cases/provenance and unreadable labels are Medium
and must be resolved. Maximum four evidence-changing passes / 75 minutes / local
compute only. At the ceiling, record remaining findings and next action; do not
change numerical tolerances or seeds to make checks pass. Stop when checks pass.
Local inspection is not independent or maintainer acceptance; no merge, deployment,
release, performance qualification or new statistical support is included.

## Evidence ledger

| Pass | Changed evidence | Actual result / disposition |
|---|---|---|
| Baseline | D3 scope, documentation runner, statistical limits and reserved seeds inspected | Seven-case gallery absent; existing runner executes every Python fence in fresh page processes. D2 baselines remain separate regression fixtures. |
| 1 | Nine executable blocks, seven synthetic cases and checkout launcher | Corrected initial group access to the public `collection.results` mapping after execution caught incorrect indexing. All case assertions pass. Discrete merging and two-row group-tail warnings remain visible. Seeds and numerical tolerances unchanged. |
| 2 | Local visual inspection of all seven figures and interpretation review | Means/lines, covariance contrasts, weighting, tied support and restored group coordinates are visible. Reduced crowded heteroskedastic x ticks to integer labels and inspected the revised figure. Corrected the discrete explanation to identify the two lowest values sharing a bin. No renderer/library behavior changed. |
| 3 | Two fresh launcher processes and isolated native installation | Seven PNGs and complete manifests are byte-identical between final formatted-source runs. The isolated base install also reproduces every input/result/figure hash without pandas or binsreg. Source and committed image hashes match the manifest; changed local Markdown links resolve. |
| 4 | Full required gate | Lint/format, strict mypy, four import contracts, 427 unit tests (94.64% coverage), native journey, 34 DPI/binsreg integrations, 40 Statsmodels references, all development coverage gates, 38 documentation blocks/quickstart, strict site and four D2 baselines pass. The final build failed only at sandbox DNS resolution for hatchling; an authorized `uv build` retry produced wheel/sdist successfully. |

## Recorded examples and reproducibility

The [gallery](site/guide/gallery.md) contains the executable source; the
[launcher](../examples/gallery.py) reuses the existing Markdown fence extractor
and executes it in a fresh process with a 60-second timeout. It writes only to
the requested output directory, defaulting to ignored `.work/gallery`, and does
not update site assets during checks. The existing docs/CI runner automatically
executes the new page's nine blocks in temporary storage. No extra test framework,
runtime dependency or workflow job is added.

All data are locally generated synthetic teaching data under the repository MIT
license. PCG64 seeds 120101–120107 are declared once and kept fixed. There was no
seed search, dataset download or use of reserved assessment seeds. The committed
[manifest](site/assets/gallery/manifest.json) records seeds, row counts, Polars
input hashes, complete strict-JSON result hashes, selected numerical outputs,
PNG hashes, versions, font/FreeType identity and source/lock hashes. D3 does not
modify library source; its library implementation is inherited from `b9b9db5`.
The page/launcher hashes identify this slice's example code even though the
unreleased distribution still reports 0.1.1.

| Case / seed | Observable result in this fixed draw | Interpretation boundary |
|---|---|---|
| Linear / 120101 | Slope 1.4971 matches observation-level least squares; gap 0.000389 | Small gap is descriptive, not model or causal certification. |
| Nonlinear / 120102 | Same slope 0.01880 with two/twelve bins; gap changes from 0.000635 to 0.923582 | Coarse means hide curvature; gap is not a p-value. |
| Heteroskedastic / 120103 | Approximately linear means with visibly increasing observation residual spread | Bin intervals are not prediction intervals; classical slope covariance does not account for this variance pattern. |
| Clustered / 120104 | Independent/CR1 means and slope 0.79723 agree, intervals differ | Sixty balanced clusters demonstrate covariance choice, not a safe support threshold. Default verdict remains not assessed. |
| Weighted / 120105 | Equal-weight slope 0.98847 versus precision-weighted 0.11489; latter matches direct WLS | Weighting changes the projection of a curved mean; known precision alone does not validate misspecified slope inference. |
| Discrete x / 120106 | Twenty requested quantile bins realize four; explicit half-integer edges give five | More requested bins cannot create support. The merging warning remains visible. |
| Grouped controls / 120107 | Adjusted slopes 0.87044/0.90004 match within-group full designs; all adjusted bin SEs/CIs unavailable | Restored means retain group separation; independent adjusted IDs do not identify common intervals. Raw group tails have two rows. |

Local visual review covers the seven PNGs (one 720×460, five 1100×400 and one
1100×800). The final heteroskedastic figure was re-inspected after its tick-spacing
change; other figure hashes remained stable. These are teaching figures, not
additional D2 regression baselines or independent accessibility acceptance.

`uv run --frozen --all-extras python examples/gallery.py --output ...` generated
the final `.work/gallery-first` and `.work/gallery-second` artifacts. Their full
manifests and all seven PNGs agree byte for byte. A separate
`uv run --isolated --frozen --no-dev python examples/gallery.py --output .work/gallery-native`
installed 15 base packages and reproduced the same numerical/image evidence;
that run preceded source-only Markdown formatting, so its page hash differs.
The retained site assets match the final formatted source manifest.

Recorded host: macOS arm64, CPython 3.12.14, NumPy 2.5.2, Polars 1.44.2,
SciPy 1.18.1, Matplotlib 3.11.1, Pillow 12.3.0 and FreeType 2.14.3.
Lock SHA-256: `b8fdf6e1b0243cfb90c63cbf292dd8700347b76b56b3bd8244891612a9dbf40e`.
Bitwise portability across hosts/dependencies is not claimed. No statistical
formula, default, Polars/pandas conversion contract or package version changed.

## Review disposition

All required local checks pass, with the final build completed by an authorized
network retry after the `make check` invocation stopped at sandbox DNS resolution.
That invocation's log is ignored `.work/d3-check.log`; the retry reported successful
0.1.1 wheel/sdist builds. No numerical tests, seeds or thresholds were altered.
The documentation gate executes 38 blocks plus quickstart (nine gallery blocks
added to 29), and the unchanged four D2 baseline comparisons each have RMS 0.0.
No unresolved High/Medium finding remains within D3's declared scope.

Maintainer review/integration, statistical acceptance and release/publication remain
separate. Remote CI is not represented as completed by these local checks. The
plan records P1 workload measurement and limits as the next implementation item;
no capacity claim is introduced here.
