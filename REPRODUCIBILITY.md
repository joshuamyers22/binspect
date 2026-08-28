# Reproducibility

Python 3.12 is the default local runtime; the package remains tested across its
declared Python range. Install the exact development environment with
`uv sync --frozen --all-extras`, then run `make check`. Update dependencies only
with `uv lock --upgrade` and commit the resulting `uv.lock` change.
