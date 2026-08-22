"""Plot cross-sectional z-scores of volatility-adjusted lagged returns."""

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
WITH previous_bars AS (
    SELECT symbol,
           open_time,
           close,
           LAG(open_time) OVER instrument_bars AS previous_open_time,
           LAG(close) OVER instrument_bars AS previous_close
    FROM hourly_bars
    WINDOW instrument_bars AS (PARTITION BY symbol ORDER BY open_time)
), bar_returns AS (
    SELECT symbol,
           open_time,
           CASE
               WHEN open_time - previous_open_time = {HOUR_MS}
               THEN (close / NULLIF(previous_close, 0)) - 1
           END AS hourly_return
    FROM previous_bars
), rolling_volatility AS (
    SELECT symbol,
           open_time,
           STDDEV_SAMP(hourly_return) OVER volatility_window AS hourly_volatility,
           COUNT(hourly_return) OVER volatility_window AS return_count
    FROM bar_returns
    WINDOW volatility_window AS (
        PARTITION BY symbol
        ORDER BY open_time
        RANGE BETWEEN {LOOKBACK_HOURS * HOUR_MS} PRECEDING AND {HOUR_MS} PRECEDING
    )
), risk_adjusted AS (
    SELECT rankings.factor_time,
           rankings.symbol,
           rankings.lagged_24_return / NULLIF(vol.hourly_volatility, 0)
             AS risk_adjusted_lagged_return
    FROM factor_rankings rankings
    JOIN rolling_volatility vol
      ON vol.symbol = rankings.symbol
     AND vol.open_time = rankings.factor_time
    WHERE vol.return_count = {LOOKBACK_HOURS}
), standardized AS (
    SELECT factor_time,
           symbol,
           (risk_adjusted_lagged_return
             - AVG(risk_adjusted_lagged_return) OVER (PARTITION BY factor_time))
           / NULLIF(
               STDDEV_SAMP(risk_adjusted_lagged_return)
                   OVER (PARTITION BY factor_time),
               0
           ) AS risk_adjusted_lagged_return_zscore
    FROM risk_adjusted
)
SELECT standardized.risk_adjusted_lagged_return_zscore,
       (future.close / current.close) - 1 AS next_1h_return
FROM standardized
JOIN hourly_bars current
  ON current.symbol = standardized.symbol
 AND current.open_time = standardized.factor_time
JOIN hourly_bars future
  ON future.symbol = standardized.symbol
 AND future.open_time = standardized.factor_time + {HOUR_MS}
WHERE standardized.risk_adjusted_lagged_return_zscore IS NOT NULL
  AND current.close IS NOT NULL
  AND current.close <> 0
  AND future.close IS NOT NULL
ORDER BY standardized.factor_time, standardized.symbol
"""


def load_data(database_url: str) -> pd.DataFrame:
    x_values: list[float] = []
    y_values: list[float] = []
    with (
        psycopg.connect(
            database_url.replace("postgresql+psycopg://", "postgresql://")
        ) as conn,
        conn.cursor(name="binspect_volatility_adjusted") as cursor,
    ):
        cursor.execute(QUERY)
        while rows := cursor.fetchmany(100_000):
            x_values.extend(float(row[0]) for row in rows)
            y_values.extend(float(row[1]) for row in rows)
    return pd.DataFrame(
        {
            "risk_adjusted_lagged_return_zscore": np.asarray(x_values),
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
        x="risk_adjusted_lagged_return_zscore",
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
            "Cross-sectional z-score of volatility-adjusted lagged return "
            "vs. first-hour return"
        ),
    )
    axis.set_xlabel("Cross-sectional z-score of volatility-adjusted lagged return")
    axis.set_ylabel("First forward-hour return")
    axis.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=2))
    axis.axhline(0, color="#555555", linewidth=0.7, alpha=0.7)
    figure.tight_layout()

    stem = "volatility_adjusted_lagged_return_zscore_vs_next_1h_2000_per_bin"
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
