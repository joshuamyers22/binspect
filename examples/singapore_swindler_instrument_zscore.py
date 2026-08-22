"""Plot instrument-level lagged-return z-scores against first-hour returns."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg
from matplotlib.ticker import PercentFormatter

import binspect

HOUR_MS = 3_600_000
LOOKBACK_HOURS = 24

QUERY = f"""
WITH instrument_history AS (
    SELECT factor_time,
           symbol,
           lagged_24_return,
           AVG(lagged_24_return) OVER instrument_window AS history_mean,
           STDDEV_SAMP(lagged_24_return) OVER instrument_window AS history_std,
           COUNT(lagged_24_return) OVER instrument_window AS history_count
    FROM factor_rankings
    WINDOW instrument_window AS (
        PARTITION BY symbol
        ORDER BY factor_time
        RANGE BETWEEN {LOOKBACK_HOURS * HOUR_MS} PRECEDING AND {HOUR_MS} PRECEDING
    )
), standardized AS (
    SELECT factor_time,
           symbol,
           (lagged_24_return - history_mean) / NULLIF(history_std, 0)
             AS instrument_lagged_return_zscore
    FROM instrument_history
    WHERE history_count = {LOOKBACK_HOURS}
)
SELECT s.instrument_lagged_return_zscore,
       (future.close / current.close) - 1 AS next_1h_return
FROM standardized s
JOIN hourly_bars current
  ON current.symbol = s.symbol AND current.open_time = s.factor_time
JOIN hourly_bars future
  ON future.symbol = s.symbol
 AND future.open_time = s.factor_time + {HOUR_MS}
WHERE s.instrument_lagged_return_zscore IS NOT NULL
  AND current.close IS NOT NULL
  AND current.close <> 0
  AND future.close IS NOT NULL
ORDER BY s.factor_time, s.symbol
"""


def load_data(database_url: str) -> pd.DataFrame:
    x_values: list[float] = []
    y_values: list[float] = []
    with (
        psycopg.connect(
            database_url.replace("postgresql+psycopg://", "postgresql://")
        ) as conn,
        conn.cursor(name="binspect_instrument_zscore") as cursor,
    ):
        cursor.execute(QUERY)
        while rows := cursor.fetchmany(100_000):
            x_values.extend(float(row[0]) for row in rows)
            y_values.extend(float(row[1]) for row in rows)
    return pd.DataFrame(
        {
            "instrument_lagged_return_zscore": np.asarray(x_values),
            "next_1h_return": np.asarray(y_values),
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--observations-per-bin", type=int, default=2_000)
    args = parser.parse_args()
    if args.observations_per_bin < 1:
        parser.error("--observations-per-bin must be positive")

    data = load_data(args.db)
    number_of_bins = math.ceil(len(data) / args.observations_per_bin)
    result = binspect.binscatter(
        data,
        x="instrument_lagged_return_zscore",
        y="next_1h_return",
        bins=number_of_bins,
        binning="quantile",
        ci=None,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with binspect.theme("paper"):
        figure, axis = plt.subplots(figsize=(10, 6))
    result.plot(
        ax=axis,
        theme="paper",
        annotate="minimal",
        title=(
            "Instrument-level lagged-return z-score vs. first-hour return "
            "(2,000 observations/bin)"
        ),
    )
    axis.set_xlabel("Lagged return z-score vs. instrument's prior 24 observations")
    axis.set_ylabel("First forward-hour return")
    axis.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=2))
    axis.axhline(0, color="#555555", linewidth=0.7, alpha=0.7)
    figure.tight_layout()

    stem = "instrument_lagged_return_zscore_vs_next_1h_2000_per_bin"
    plot_path = args.output_dir / f"{stem}.png"
    table_path = args.output_dir / f"{stem}.csv"
    figure.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    result.table.to_csv(table_path, index=False)

    correlation = data.corr().iloc[0, 1]
    print(f"observations: {len(data):,}")
    print(f"bins: {number_of_bins:,}")
    print(f"smallest bin: {int(result.table['n'].min()):,}")
    print(f"largest bin: {int(result.table['n'].max()):,}")
    print(f"correlation: {correlation:.8f}")
    print(f"OLS slope: {result.fit.slope:.8f}")
    print(f"R-squared: {result.fit.r_sq:.8f}")
    print(f"wrote {plot_path}")
    print(f"wrote {table_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
