"""Run the native user journey in a minimal environment without pandas."""

import importlib.util
import json
import sys

import numpy as np
import polars as pl

import binspect


def main():
    assert importlib.util.find_spec("pandas") is None, (
        "This gate requires no pandas install."
    )
    rng = np.random.default_rng(421)
    frame = pl.DataFrame(
        {
            "x": rng.normal(size=240),
            "y": rng.normal(size=240),
            "z": rng.normal(size=240),
            "category": ["b", "a", "c"] * 80,
            "w": rng.uniform(0.5, 2, 240),
            "cluster": np.arange(240) % 12,
            "group": ["a", "b"] * 120,
        }
    )
    result = binspect.binscatter(
        frame,
        x="x",
        y="y",
        controls=["z", "category"],
        cluster="cluster",
        weights="w",
        ci=None,
        bins=4,
    )
    assert result.n_obs == 240 and isinstance(result.table, pl.DataFrame)
    assert json.loads(result.to_json())["design"]["controls"]["control_columns"] == [
        "z",
        "category_b",
        "category_c",
    ]
    comparison = binspect.compare(
        frame,
        x="x",
        y="y",
        controls="z",
        weights="w",
        group="group",
        common_bins=False,
        ci=None,
        bins=4,
    )
    assert comparison.table.height == 8
    assert comparison.summary_frame(include_pooled=True).height == 3
    assert comparison.to_evidence()["payload"]["result"]["schema_version"] == 1
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = result.audit(annotate=None)
    figure.canvas.draw()
    plt.close(figure)
    figure = comparison.plot(annotate=None)
    figure.canvas.draw()
    plt.close(figure)
    try:
        result.to_pandas()
    except ImportError as error:
        assert "binspect-regression[pandas]" in str(error)
    else:
        raise AssertionError("pandas conversion should require the optional dependency")
    assert "pandas" not in sys.modules
    print(
        "Native Polars estimation, grouped controls, export and plots passed "
        "without pandas."
    )


if __name__ == "__main__":
    main()
