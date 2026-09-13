"""Exercise installed-code contracts without pytest or optional test packages."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import io
import json
import platform
import sys
from pathlib import Path

import numpy as np
import polars as pl
from packaging.requirements import Requirement
from packaging.version import Version

import binspect
from binspect.exceptions import BinsregError, InvalidBinningError


def missing(call, kind, extra):
    try:
        call()
    except kind as error:
        assert f"binspect-regression[{extra}]" in str(error), str(error)
    else:
        raise AssertionError(f"Missing {extra} extra did not fail.")


def verify_floors(path, *, pandas, dpi):
    """Reject metadata drift and accidental upgrades of direct floor packages."""
    declared = {}
    active = set()
    for raw in importlib.metadata.requires("binspect-regression") or []:
        requirement = Requirement(raw)
        if requirement.marker is None or any(
            requirement.marker.evaluate({"extra": extra}) for extra in ("pandas", "dpi")
        ):
            bounds = list(requirement.specifier)
            assert len(bounds) == 1 and bounds[0].operator == ">=", raw
            declared[requirement.name] = Version(bounds[0].version)
            if (
                requirement.marker is None
                or (pandas and not dpi and requirement.name == "pandas")
                or (dpi and requirement.name == "binsreg")
            ):
                active.add(requirement.name)
    pinned = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            requirement = Requirement(line)
            bounds = list(requirement.specifier)
            assert len(bounds) == 1 and bounds[0].operator == "==", line
            pinned[requirement.name] = Version(bounds[0].version)
    assert pinned == declared, (pinned, declared)
    for name in active:
        assert Version(importlib.metadata.version(name)) == pinned[name], name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pandas", action="store_true")
    parser.add_argument("--dpi", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--floors", type=Path)
    args = parser.parse_args()
    assert "site-packages" in Path(binspect.__file__).parts, binspect.__file__
    assert (importlib.util.find_spec("pandas") is not None) == args.pandas
    assert (importlib.util.find_spec("binsreg") is not None) == args.dpi
    if args.floors:
        verify_floors(args.floors, pandas=args.pandas, dpi=args.dpi)
    rng = np.random.Generator(np.random.PCG64(140101))
    n = 2400
    x, z = rng.normal(size=(2, n))
    y = 0.8 * x + 0.3 * x**2 + z + rng.normal(size=n)
    weights = rng.uniform(0.5, 2, n)
    weights[-10:] = 0
    frame = pl.DataFrame(
        {
            "x": x,
            "y": y,
            "z": z,
            "w": weights,
            "cluster": np.arange(n) % 60,
            "group": np.where(np.arange(n) % 2, "a", "b"),
            "category": np.where(np.arange(n) % 3, "c", "d"),
        }
    )
    result = binspect.binscatter(
        frame, x="x", y="y", bins=12, weights="w", cluster="cluster"
    )
    assert isinstance(result.table, pl.DataFrame)
    design = np.column_stack([np.ones(n), x])
    expected = np.linalg.lstsq(
        design * np.sqrt(weights)[:, None], y * np.sqrt(weights), rcond=None
    )[0]
    np.testing.assert_allclose(
        [result.fit.intercept, result.fit.slope], expected, rtol=1e-12, atol=1e-12
    )
    active = (result.binning.assignment == 0) & (weights > 0)
    clusters = frame["cluster"].to_numpy()
    labels = np.unique(clusters[active])
    scores = [
        np.sum(
            weights[active & (clusters == label)]
            * (y[active & (clusters == label)] - result.estimates.y_mean[0])
        )
        for label in labels
    ]
    expected_se = (
        np.sqrt(len(labels) / (len(labels) - 1) * np.sum(np.square(scores)))
        / weights[active].sum()
    )
    np.testing.assert_allclose(
        result.estimates.se[0], expected_se, rtol=1e-12, atol=1e-12
    )
    adjusted = binspect.binscatter(
        frame, x="x", y="y", controls=["z", "category"], weights="w", bins=12, ci=None
    )
    full = np.column_stack([np.ones(n), z, frame["category"].to_numpy() == "d", x])
    expected_adjusted = np.linalg.lstsq(
        full * np.sqrt(weights)[:, None], y * np.sqrt(weights), rcond=None
    )[0][-1]
    np.testing.assert_allclose(
        adjusted.fit.slope, expected_adjusted, rtol=1e-12, atol=1e-12
    )
    assert np.isnan(adjusted.estimates.se).all()
    grouped = binspect.compare(
        frame,
        x="x",
        y="y",
        group="group",
        controls="z",
        weights="w",
        common_bins=False,
        bins=8,
        ci=None,
    )
    assert isinstance(grouped.table, pl.DataFrame) and grouped.table.height == 16
    assert grouped.summary_frame(include_pooled=True).height == 3
    assert json.loads(result.to_json())["schema_version"] == 1
    assert result.to_evidence()["payload"]["result"]["schema_version"] == 1
    assert not result.x.flags.writeable
    if args.pandas:
        import pandas as pd

        pandas_frame = pd.DataFrame(
            frame.to_dict(as_series=False), index=np.arange(n)[::-1]
        )
        compatible = binspect.binscatter(
            pandas_frame, x="x", y="y", bins=12, weights="w", cluster="cluster"
        )
        assert isinstance(compatible.table, pl.DataFrame)
        np.testing.assert_allclose(
            compatible.estimates.y_mean, result.estimates.y_mean, rtol=1e-12
        )
        projected = result.to_pandas()
        assert isinstance(projected, pd.DataFrame)
        projected.loc[0, "y_mean"] = -999
        assert result.table["y_mean"][0] != -999
    else:
        missing(result.to_pandas, ImportError, "pandas")
        assert "pandas" not in sys.modules
    if args.dpi:
        selected = binspect.binscatter(frame, x="x", y="y", bins="dpi")
        assert selected.bin_rule == "dpi" and selected.n_bins >= 2
        function = binspect.binsreg(frame, x="x", y="y", controls="z", bins=12)
        assert isinstance(function.dots, pl.DataFrame)
        assert function.intervals.height > 0
        assert np.isfinite(function.intervals.select("ci_lo", "ci_hi").to_numpy()).all()
        assert function.metadata["backend_version"] == importlib.metadata.version(
            "binsreg"
        )
    else:
        missing(
            lambda: binspect.binscatter(frame, x="x", y="y", bins="dpi"),
            InvalidBinningError,
            "dpi",
        )
        missing(lambda: binspect.binsreg(frame, x="x", y="y"), BinsregError, "dpi")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures = [result.audit(annotate=None), grouped.plot(annotate=None)]
    if args.dpi:
        figures.append(function.plot().figure)
    for figure in figures:
        output = io.BytesIO()
        figure.savefig(output, format="png")
        assert output.getvalue().startswith(b"\x89PNG")
        plt.close(figure)
    if not args.pandas:
        assert "pandas" not in sys.modules
    record = {
        "status": "pass",
        "python": platform.python_version(),
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "seed": 140101,
        "installed_code": True,
        "extras": {"pandas": args.pandas, "dpi": args.dpi},
        "versions": dict(
            sorted(
                (d.metadata["Name"], d.version)
                for d in importlib.metadata.distributions()
            )
        ),
        "checks": [
            "weighted_clustered",
            "FWL_numeric_categorical",
            "grouped_controls",
            "Polars_tables",
            "ownership_JSON",
            "optional_boundaries",
            "PNG_rendering",
        ],
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"Installed dependency contracts passed on Python {record['python']}.")


if __name__ == "__main__":
    main()
