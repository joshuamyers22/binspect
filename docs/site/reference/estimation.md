# Estimation API

This reference is generated from the checkout's source signatures/docstrings.
Read the guide's [input/weight rules](../guide/weights.md),
[adjusted estimands](../guide/adjustment.md) and [bin selection](../guide/binning.md)
before combining options. Tables always default to Polars. Application examples
in the guide are executed; illustrative docstring fragments here are not the
executable-example suite.

::: binspect.binscatter

::: binspect.compare

::: binspect.binsreg

::: binspect.DiagnosticPolicy

## Errors and warnings

Standard `ValueError`, `TypeError`, `KeyError` and optional-conversion `ImportError`
also remain possible; `BinspectError` does not wrap every invalid input. Catch
warning/error classes instead of parsing message wording.

::: binspect.exceptions
    options:
      members:
        - BinspectError
        - InsufficientDataError
        - InvalidBinningError
        - BinsregError
        - BinCountWarning
        - AdjustedInferenceWarning
        - BinsregWarning
