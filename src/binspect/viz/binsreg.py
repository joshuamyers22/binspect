"""Plot the separate original-coordinate binsreg function result."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

if TYPE_CHECKING:
    from ..binsreg_results import BinsregResult


def plot(result: BinsregResult, ax: Axes | None = None) -> Axes:
    """Draw point estimates and intervals around their own fitted centers."""
    if ax is None:
        _, ax = plt.subplots()
    dots, ci, meta = result.dots, result.intervals, result.metadata
    ax.scatter(dots.x, dots.fit, label="Dot fit")
    if len(ci):
        center = ci["fit"].to_numpy()
        ax.errorbar(
            ci.x,
            center,
            yerr=np.vstack((center - ci.ci_lo, ci.ci_hi - center)),
            fmt="x",
            label="Interval fit",
        )
    ax.set_xlabel(meta["x_name"])
    ax.set_ylabel(f"{meta['y_name']} (function estimate)")
    ax.set_title(f"binsreg: {meta['inference_status']}")
    ax.legend()
    return ax
