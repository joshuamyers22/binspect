# Four rendering baselines

These synthetic PNGs cover default composition, the paper preset, the four-panel
audit and standalone deviation. They complement structural export tests rather
than replacing them. Initial local inspection is recorded in the
[D2 review](../../docs/figure-export-review.md); maintainer acceptance is pending.

`manifest.json` records Matplotlib/NumPy/SciPy/Pillow/FreeType versions, CPython
3.12, bundled font hashes, rc settings, PNG hashes, the generating host and lock
hash. Rendering inputs must match; host metadata is recorded, not a claim of
cross-platform equivalence. CI pins macos-15 and uv-managed Python 3.12.14; setup-python does not provide
that macOS patch build. Local rendering
used macOS 15.1 arm64 with the same specified libraries/fonts. Other hosts need
their own passing comparison/evidence before a qualification claim.

Run `make figures` from the frozen environment. Dimension or opacity changes fail;
RGB RMS above the prespecified 0.5/255 ceiling fails. Missing reference files,
changed reference hashes and renderer mismatches fail rather than skip. Initial
same-environment comparisons gave RMS 0.0 for all four images. The small allowance
covers antialiasing variation; separate tests reject missing/misplaced intervals,
clipped visible labels, lost text and changed axes/rcParams.

Default comparison writes candidates only under `.work/figures`, never here.
For an intentional reviewed change, explicitly run
`uv run --frozen --all-extras python validation/figures.py --write-baselines`,
inspect every changed image and the manifest diff, run structural/export and full
checks, and obtain maintainer review. Never regenerate just to clear a red test,
or widen thresholds to accept an unexplained visual difference.

PDF/SVG are structurally parsed by the portable tests; only PNG has pixel baselines.
These files are synthetic binspect-generated assets under the repository license.
