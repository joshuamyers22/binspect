"""Quickstart: audit a linear model that is quietly wrong.

Run with ``python examples/quickstart.py``. Writes ``docs/hero.png``.

The DGP here is deliberately mild: a saturating relationship that a linear model
fits with a respectable R-squared, so nothing in the regression output looks amiss.
The binscatter is what makes the problem visible.
"""

from __future__ import annotations

import pathlib

import matplotlib.pyplot as plt
import numpy as np

import binspect


def main() -> None:
    rng = np.random.default_rng(11)
    n = 25_000

    # Diminishing returns: the effect of x on y flattens out at the top.
    x = rng.gamma(shape=2.0, scale=2.0, size=n)
    y = 8.0 * np.log1p(x) + rng.normal(scale=3.0, size=n)

    bs = binspect.binscatter(x=x, y=y, bins=25)
    print(bs.summary())

    # The regression on its own looks perfectly healthy:
    print(
        f"\nA linear model reports R² = {bs.fit.r_sq:.3f}, slope = {bs.fit.slope:.3f}."
    )
    print(
        f"Bin means sit {bs.decomposition.gap:.1%} of total variance off that line: "
        f"{bs.verdict}."
    )

    with binspect.theme("notebook"):
        fig, ax = plt.subplots()

    bs.plot(
        ax=ax,
        theme="notebook",
        annotate="audit",
        title="Diminishing returns hiding inside a healthy R²",
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    out = pathlib.Path(__file__).resolve().parent.parent / "docs" / "hero.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
