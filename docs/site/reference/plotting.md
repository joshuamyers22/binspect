# Plotting API

Standalone layers return their supplied Axes; composition fixes the draw order.
Style kwargs go to Matplotlib artists. The single-result `.plot` forwards to
`binspect.viz.plot`, and `.audit` forwards to `binspect.viz.audit`. See
[composition and scoped themes](../guide/plotting.md) for return types, defaults
and theme limits. Result methods, including collection facets and the separate
function adapter plot, are in the [result reference](results.md).

::: binspect.viz.figure
    options:
      members: [DEFAULT_LAYERS, LAYER_ORDER, plot]

::: binspect.viz.audit.audit

::: binspect.viz.layers
    options:
      members: [raw_layer, deviation_layer, rug_layer, fit_layer, sd_line_layer, smooth_layer, ci_layer, bins_layer]

::: binspect.viz.annotate_layer

::: binspect.viz.caption_text

::: binspect.viz.theme.theme

::: binspect.viz.Theme

::: binspect.viz.get_theme

::: binspect.viz.Palette

::: binspect.viz.get_palette

Named `THEMES` and `PALETTES` have `notebook`, `paper`, `deck` keys. Presets
override the custom Theme constructor defaults shown above. The registries and
Theme.rc dictionaries are mutable; prefer the scoped context to global mutation.
