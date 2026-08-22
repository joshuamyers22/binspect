"""Plot first-hour returns in lagged-return z-score bins of about 2,000 rows."""

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

QUERY = """
WITH standardized AS (
    SELECT factor_time,
           symbol,
           (lagged_24_return
             - AVG(lagged_24_return) OVER (PARTITION BY factor_time))
           / NULLIF(STDDEV_SAMP(lagged_24_return) OVER (PARTITION BY factor_time), 0)
             AS lagged_return_zscore
    FROM factor_rankings
)
SELECT s.lagged_return_zscore,
       (future.close / current.close) - 1 AS next_1h_return
FROM standardized s
JOIN hourly_bars current
  ON current.symbol = s.symbol AND current.open_time = s.factor_time
JOIN hourly_bars future
  ON future.symbol = s.symbol
 AND future.open_time = s.factor_time + 3600000
WHERE s.lagged_return_zscore IS NOT NULL
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
        conn.cursor(name="binspect_first_hour_2000") as cursor,
    ):
        cursor.execute(QUERY)
        while rows := cursor.fetchmany(100_000):
            x_values.extend(float(row[0]) for row in rows)
            y_values.extend(float(row[1]) for row in rows)
    return pd.DataFrame(
        {
            "lagged_return_zscore": np.asarray(x_values),
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
        x="lagged_return_zscore",
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
        title="Lagged return z-score vs. first-hour return (2,000 observations/bin)",
    )
    axis.set_xlabel("Hourly cross-sectional z-score of lagged return")
    axis.set_ylabel("First forward-hour return")
    axis.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=2))
    axis.axhline(0, color="#555555", linewidth=0.7, alpha=0.7)
    figure.tight_layout()

    stem = "lagged_return_zscore_vs_next_1h_2000_observations_per_bin"
    plot_path = args.output_dir / f"{stem}.png"
    table_path = args.output_dir / f"{stem}.csv"
    figure.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    result.table.to_csv(table_path, index=False)

    print(f"observations: {len(data):,}")
    print(f"bins: {number_of_bins:,}")
    print(f"smallest bin: {int(result.table['n'].min()):,}")
    print(f"largest bin: {int(result.table['n'].max()):,}")
    print(f"wrote {plot_path}")
    print(f"wrote {table_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
