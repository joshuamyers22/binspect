"""The drawing contract.

Two things matter more than pixels: an axes passed in is the axes handed back, and
importing or theming binspect never mutates the caller's rcParams.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import copy

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

import binspect
from binspect.viz import figure, layers
from binspect.viz.theme import theme as theme_fn


@pytest.fixture
def result(concave):
    return binspect.binscatter(concave, y="y", x="x", bins=20)


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_returns_the_axes_it_was_given(result):
    _, ax = plt.subplots()
    returned = result.plot(ax=ax)
    assert returned is ax


def test_creates_a_figure_when_none_supplied(result):
    ax = result.plot()
    assert ax.figure is not None


def test_default_layers_draw_something(result):
    ax = result.plot()
    assert len(ax.collections) >= 1  # bin means
    assert len(ax.lines) >= 1  # fit line
    assert ax.get_xlabel() == "x"
    assert ax.get_ylabel() == "y"


def test_layers_can_be_selected(result):
    ax = result.plot(show=("bins",), annotate=None)
    assert len(ax.lines) == 0
    assert len(ax.collections) == 1


def test_sd_line_adds_a_line(result):
    bare = result.plot(show=("fit",), annotate=None)
    with_sd = result.plot(show=("fit", "sd_line"), annotate=None)
    assert len(with_sd.lines) == len(bare.lines) + 1


def test_unknown_layer_is_refused(result):
    with pytest.raises(ValueError, match="unknown layer"):
        result.plot(show=("bins", "nonsense"))


def test_annotate_levels(result):
    assert len(result.plot(annotate=None).texts) == 0
    assert len(result.plot(annotate="minimal").texts) == 1
    audit = result.plot(annotate="audit").texts[0].get_text()
    assert "η²" in audit and result.verdict in audit


def test_bad_annotate_level_is_refused(result):
    with pytest.raises(ValueError, match="annotate must be"):
        result.plot(annotate="loud")


@pytest.mark.parametrize("name", ["notebook", "paper", "deck"])
def test_every_theme_draws(result, name):
    ax = result.plot(theme=name)
    assert len(ax.collections) >= 1


def test_unknown_theme_is_refused(result):
    with pytest.raises(KeyError, match="unknown theme"):
        result.plot(theme="brutalist")


def test_layers_are_usable_standalone(result):
    _, ax = plt.subplots()
    layers.deviation_layer(ax, result)
    # One LineCollection for all bins, not one Line2D each.
    assert len(ax.collections) == 1
    assert len(ax.lines) == 0


def test_deviation_target_must_be_valid(result):
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match="target must be"):
        layers.deviation_layer(ax, result, target="vibes")


def test_smooth_target_is_available(result):
    _, ax = plt.subplots()
    layers.deviation_layer(ax, result, target="smooth")
    assert len(ax.collections) == 1


def test_lines_span_the_bins_not_the_tails(result):
    """Tail observations must not stretch the axes past where bin means live."""
    _, ax = plt.subplots()
    layers.fit_layer(ax, result)
    drawn_lo, drawn_hi = ax.lines[0].get_xdata()
    assert drawn_lo > result.x.min()
    assert drawn_hi < result.x.max()


def test_span_data_covers_every_observation(result):
    _, ax = plt.subplots()
    layers.fit_layer(ax, result, span="data")
    drawn_lo, drawn_hi = ax.lines[0].get_xdata()
    assert drawn_lo == pytest.approx(result.x.min())
    assert drawn_hi == pytest.approx(result.x.max())


def test_bad_span_is_refused(result):
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match="span must be"):
        layers.fit_layer(ax, result, span="everything")


def test_layer_kwargs_reach_the_layer(result):
    ax = result.plot(show=("bins",), layer_kwargs={"bins": {"size_by_n": True}})
    assert len(ax.collections) == 1


def test_import_does_not_mutate_rcparams():
    before = copy.deepcopy(dict(mpl.rcParams))
    import importlib

    importlib.reload(binspect)
    assert dict(mpl.rcParams) == before


def test_theme_context_restores_rcparams():
    before = copy.deepcopy(dict(mpl.rcParams))
    with binspect.theme("deck"):
        assert mpl.rcParams["font.size"] != before["font.size"]
    assert dict(mpl.rcParams) == before


def test_theme_context_restores_on_exception():
    before = copy.deepcopy(dict(mpl.rcParams))
    with pytest.raises(RuntimeError), binspect.theme("paper"):
        raise RuntimeError("boom")
    assert dict(mpl.rcParams) == before


def test_plotting_does_not_leak_theme(result):
    before = copy.deepcopy(dict(mpl.rcParams))
    result.plot(theme="deck")
    assert dict(mpl.rcParams) == before


def test_theme_overrides_are_scoped():
    before = mpl.rcParams["font.size"]
    with theme_fn("notebook", **{"font.size": 42.0}):
        assert mpl.rcParams["font.size"] == 42.0
    assert mpl.rcParams["font.size"] == before


def test_layer_order_is_fixed():
    assert figure.LAYER_ORDER.index("bins") == len(figure.LAYER_ORDER) - 1
    assert figure.LAYER_ORDER.index("deviation") < figure.LAYER_ORDER.index("fit")
