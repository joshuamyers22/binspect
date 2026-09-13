# Composing plots

`result.plot(ax=ax)` returns the exact supplied Matplotlib Axes. Without `ax` it
creates one. Defaults draw deviation marks, rug, fit, available confidence limits
and bin means, with a minimal caption and no legend. The draw order is fixed
regardless of the order in `show`; unknown layer names raise an error.

```python
import copy
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import binspect
from binspect.viz import deviation_layer

rng = np.random.default_rng(86)
x = rng.normal(size=1200)
result = binspect.binscatter(x=x, y=np.tanh(x) + rng.normal(size=x.size), bins=10)
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
before = copy.deepcopy(dict(mpl.rcParams))
assert (
    result.plot(
        ax=axes[0],
        theme="paper",
        show=("bins", "fit", "ci"),
        annotate=None,
        layer_kwargs={"bins": {"size_by_n": True}, "fit": {"label": "Observation fit"}},
    )
    is axes[0]
)
assert deviation_layer(axes[1], result, theme="paper") is axes[1]
assert dict(mpl.rcParams) == before
fig.savefig("composition.png", dpi=120)
plt.close(fig)
```

Every standalone layer accepts an Axes/result and returns that Axes. Style kwargs
go to Matplotlib artists; `layer_kwargs` routes them by layer in a composed plot.
The optional `raw`, `smooth` and `sd_line` layers are off by default. Fit/SD spans
the bin means with padding; `span='data'` includes tail observations. `size_by_n`
uses retained raw counts. A smoother through bin means is descriptive, not a
separate fitted model for quoting a slope.

`ci` draws nothing when limits are unavailable, including adjusted bins. Its bars
describe mean uncertainty, not the spread of observations (`y_sd`).
`annotate='audit'` adds diagnostics; `annotate=None` removes captions.

## Scoped themes and composed figures

```python
with binspect.theme("paper", **{"font.size": 12}):
    assert mpl.rcParams["font.size"] == 12
assert dict(mpl.rcParams) == before

audit = result.audit(theme="paper", marginals=True, residuals=True, hist_bins=20)
assert len(audit.axes) == 4
audit.savefig("audit.png", dpi=120)
plt.close(audit)
```

Themes `notebook`, `paper` and `deck` are scoped and restore rcParams even on
exceptions. A plot still applies its own theme inside an outer context; pass the
desired theme explicitly. Standalone layers use theme style values but do not
open a full rcParams context. Global theme dictionaries are mutable; changing
them directly is not scoped styling.

`audit()` returns a new Figure with optional marginals and residual panels; it
does not accept `ax`. `collection.plot(layout='facets')` also returns a Figure,
with shared x/y axes by default and up to three columns. Individual group results
can instead be plotted into supplied axes. Facet figure creation uses caller
rcParams, while each panel applies its requested theme.

The separate binsreg result plot accepts only optional `ax`, uses caller styles
and returns that Axes. It marks dots and intervals at their own fitted centers.
See [plotting API](../reference/plotting.md) for signatures.

The [export guide and visual review](figure-exports.md) records local PNG/PDF/SVG
checks, four pinned raster baselines and grayscale/color-vision simulations.
Existing presets lose labels/context on dark backgrounds. These checks do not
certify accessibility or every vector reader; maintainer visual acceptance remains open.
