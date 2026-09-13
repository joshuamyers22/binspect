"""Portable export/geometry checks complement the separately pinned PNG gate."""

from __future__ import annotations

import copy
import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree as ET

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PathCollection
from PIL import Image
from pypdf import PdfReader

import binspect

SPEC = importlib.util.spec_from_file_location(
    "figures", Path(__file__).resolve().parents[1] / "validation/figures.py"
)
assert SPEC and SPEC.loader
figures = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(figures)


@pytest.fixture(autouse=True)
def rendering():
    with figures.render_context():
        yield
        plt.close("all")


def scenario(name):
    result = figures.example_result()
    if name == "missing_ci":
        result = binspect.binscatter(x=result.x, y=result.y, bins=12, ci=None)
        figure = result.plot(show=("bins", "ci")).figure
        assert len(figure.axes[0].collections) == 1
    elif name == "negative":
        result = binspect.binscatter(x=result.x, y=-result.y, bins=12)
        figure = result.plot(show=("bins", "ci", "fit", "sd_line"), legend=True).figure
        fit_line, sd_line = figure.axes[0].lines
        assert fit_line.get_ydata()[1] < fit_line.get_ydata()[0]
        assert sd_line.get_ydata()[1] < sd_line.get_ydata()[0]
        assert fit_line.get_linestyle() != sd_line.get_linestyle()
    elif name == "long_labels":
        result = replace(
            result,
            x_name="Exposure over the preceding observation period",
            y_name="Average response across the measured outcome period",
        )
        figure, ax = plt.subplots(figsize=(9, 5))
        before = figure.get_size_inches().copy()
        assert result.plot(ax=ax, theme="paper", annotate=None) is ax
        np.testing.assert_array_equal(figure.get_size_inches(), before)
        figure.tight_layout()
    elif name == "facets":
        grouped = binspect.compare(
            x=result.x,
            y=result.y,
            group=np.where(np.arange(result.n_obs) % 2, "Group A", "Group B"),
            bins=8,
        )
        figure = grouped.plot(ncols=2, annotate=None)
        assert len(figure.axes) == 2
    elif name == "audit":
        figure = result.audit(annotate=None)
        assert len(figure.axes) == 4
    else:
        raise ValueError(name)
    return figure


@pytest.mark.parametrize(
    "name", ["missing_ci", "negative", "long_labels", "facets", "audit"]
)
@pytest.mark.parametrize("extension", ["png", "pdf", "svg"])
def test_exports_preserve_dimensions_text_and_scoped_state(name, extension, tmp_path):
    before = copy.deepcopy(dict(mpl.rcParams))
    figure = scenario(name)
    figure.canvas.draw()
    width, height = figure.get_size_inches()
    # Ensure visible labels/ticks/titles are inside the actual canvas, not merely
    # rescued by bbox_inches='tight' expanding a badly arranged figure.
    renderer = figure.canvas.get_renderer()
    for ax in figure.axes:
        labels = [
            ax.xaxis.label,
            ax.yaxis.label,
            ax.title,
        ]
        # Locators also create ticks outside view limits; those are not drawn.
        for axis in (ax.xaxis, ax.yaxis):
            low, high = sorted(axis.get_view_interval())
            labels.extend(
                label
                for tick in axis.get_major_ticks()
                if low <= tick.get_loc() <= high
                for label in (tick.label1, tick.label2)
            )
        for text in labels:
            if text.get_visible() and text.get_text():
                box = text.get_window_extent(renderer)
                assert box.x0 >= -1 and box.y0 >= -1, text.get_text()
                assert box.x1 <= width * 100 + 1 and box.y1 <= height * 100 + 1, (
                    text.get_text()
                )
    target = tmp_path / f"{name}.{extension}"
    figure.savefig(
        target, format=extension, dpi=100, facecolor="white", bbox_inches=None
    )
    assert dict(mpl.rcParams) == before
    assert target.stat().st_size > 1000
    if extension == "png":
        with Image.open(target) as image:
            assert image.size == (round(width * 100), round(height * 100))
            assert np.asarray(image.convert("RGB")).std() > 5
    elif extension == "svg":
        root = ET.parse(target).getroot()
        assert root.tag.endswith("svg")
        np.testing.assert_allclose(
            [float(v) for v in root.attrib["viewBox"].split()][2:],
            [width * 72, height * 72],
        )
        texts = " ".join(
            node.text or "" for node in root.iter() if node.tag.endswith("}text")
        )
        assert figure.axes[0].get_xlabel() in texts
        assert figure.axes[0].get_ylabel() in texts
        assert any(node.tag.endswith("}path") for node in root.iter())
    else:
        reader = PdfReader(target, strict=True)
        assert len(reader.pages) == 1
        page = reader.pages[0]
        np.testing.assert_allclose(
            [float(page.mediabox.width), float(page.mediabox.height)],
            [width * 72, height * 72],
        )
        text = page.extract_text()
        assert figure.axes[0].get_xlabel() in text
        assert figure.axes[0].get_ylabel() in text


def test_missing_intervals_omit_only_unavailable_segments():
    result = figures.example_result()
    lo, hi = result.estimates.ci_lo.copy(), result.estimates.ci_hi.copy()
    lo[::2] = hi[::2] = np.nan
    result = replace(result, estimates=replace(result.estimates, ci_lo=lo, ci_hi=hi))
    ax = result.plot(show=("bins", "ci"), annotate=None)
    points = next(c for c in ax.collections if isinstance(c, PathCollection))
    bars = next(c for c in ax.collections if isinstance(c, LineCollection))
    np.testing.assert_allclose(
        points.get_offsets(),
        np.column_stack([result.estimates.x_mean, result.estimates.y_mean]),
    )
    segments = np.asarray(bars.get_segments())
    np.testing.assert_allclose(segments[:, 0, 0], result.estimates.x_mean[1::2])
    np.testing.assert_allclose(segments[:, 0, 1], lo[1::2])
    np.testing.assert_allclose(segments[:, 1, 1], hi[1::2])


def test_image_comparator_detects_missing_marks_and_dimension_changes(tmp_path):
    expected, changed = tmp_path / "expected.png", tmp_path / "changed.png"
    pixels = np.full((100, 100, 4), 255, dtype=np.uint8)
    pixels[20:80, 48:52, :3] = 0
    Image.fromarray(pixels).save(expected)
    Image.fromarray(np.full_like(pixels, 255)).save(changed)
    with pytest.raises(ValueError, match="Image regression"):
        figures.compare_png(expected, changed)
    Image.new("RGBA", (50, 50), "white").save(changed)
    with pytest.raises(ValueError, match="dimensions"):
        figures.compare_png(expected, changed)


def test_renderer_mismatch_fails_instead_of_skipping_comparison():
    expected = figures.renderer()
    actual = copy.deepcopy(expected)
    actual["freetype"] = "unqualified"
    with pytest.raises(ValueError, match="Renderer differs"):
        figures.check_renderer(expected, actual)


def test_comparison_cannot_overwrite_baselines_via_output_argument(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(figures, "BASELINES", tmp_path)
    monkeypatch.setattr(sys, "argv", ["figures.py", "--output", str(tmp_path)])
    with pytest.raises(ValueError, match="must not overwrite"):
        figures.main()
    assert not list(tmp_path.iterdir())
