# Result API

Numeric arrays are immutable owned snapshots; tables, inference dictionaries and
exports are independent editable projections. Use estimators to construct results
with complete sample/design history. See [tables and evidence](../guide/exports.md)
for selectors, schema compatibility and pandas migration.

::: binspect.BinscatterResult

::: binspect.BinscatterCollection

::: binspect.BinsregResult

## Nested values

These types expose the stored result's partition, estimate and diagnostic fields.
Core computation primitives remain internal estimation helpers and do not replace
the supported input/inference boundary. In particular, their availability does
not restore withdrawn adjusted-bin uncertainty.

::: binspect.types.Line

::: binspect.types.LineFit

::: binspect.core.binning.Binning

::: binspect.core.estimate.BinEstimates

::: binspect.core.decompose.Decomposition

::: binspect.input_metadata.SampleCounts

::: binspect.input_metadata.ControlDesign
