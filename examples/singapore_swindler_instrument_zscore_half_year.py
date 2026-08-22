"""Compare instrument-level lagged-return z-scores by calendar half-year."""

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
SELECT s.factor_time,
       s.instrument_lagged_return_zscore,
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
    timestamps: list[int] = []
    x_values: list[float] = []
    y_values: list[float] = []
    with (
        psycopg.connect(
            database_url.replace("postgresql+psycopg://", "postgresql://")
        ) as conn,
        conn.cursor(name="binspect_instrument_zscore_half_year") as cursor,
    ):
        cursor.execute(QUERY)
        while rows := cursor.fetchmany(100_000):
            timestamps.extend(int(row[0]) for row in rows)
            x_values.extend(float(row[1]) for row in rows)
            y_values.extend(float(row[2]) for row in rows)
    data = pd.DataFrame(
        {
            "factor_time": pd.to_datetime(timestamps, unit="ms", utc=True),
            "instrument_lagged_return_zscore": np.asarray(x_values),
            "next_1h_return": np.asarray(y_values),
        }
    )
    years = data["factor_time"].dt.year.astype(str)
    halves = np.where(data["factor_time"].dt.month <= 6, "H1", "H2")
    data["half_year"] = years + " " + halves
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--observations-per-bin", type=int, default=2_000)
    args = parser.parse_args()
    if args.observations_per_bin < 1:
        parser.error("--observations-per-bin must be positive")

    data = load_data(args.db)
    periods = sorted(data["half_year"].unique())
    columns = min(3, len(periods))
    rows = math.ceil(len(periods) / columns)
    with binspect.theme("paper"):
        figure, axes = plt.subplots(
            rows,
            columns,
            figsize=(5.4 * columns, 4.6 * rows),
            squeeze=False,
            sharex=True,
            sharey=True,
        )

    summary_rows: list[dict[str, float | int | str]] = []
    bin_tables: list[pd.DataFrame] = []
    for period, axis in zip(periods, axes.flat, strict=False):
        period_data = data.loc[data["half_year"] == period]
        number_of_bins = math.ceil(len(period_data) / args.observations_per_bin)
        result = binspect.binscatter(
            period_data,
            x="instrument_lagged_return_zscore",
            y="next_1h_return",
            bins=number_of_bins,
            binning="quantile",
            ci=None,
        )
        result.plot(
            ax=axis,
            theme="paper",
            annotate=None,
            title=f"{period}: n={len(period_data):,}, bins={number_of_bins}",
        )
        axis.set_xlabel("Instrument lagged-return z-score")
        axis.set_ylabel("First forward-hour return")
        axis.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=2))
        axis.axhline(0, color="#555555", linewidth=0.7, alpha=0.7)

        period_bins = result.table.copy()
        period_bins.insert(0, "half_year", period)
        bin_tables.append(period_bins)
        summary_rows.append(
            {
                "half_year": period,
                "observations": len(period_data),
                "bins": number_of_bins,
                "correlation": period_data[
                    ["instrument_lagged_return_zscore", "next_1h_return"]
                ]
                .corr()
                .iloc[0, 1],
                "ols_slope": result.fit.slope,
                "r_squared": result.fit.r_sq,
            }
        )

    for axis in axes.flat[len(periods) :]:
        axis.set_visible(False)

    figure.suptitle(
        "Instrument-level lagged-return z-score by calendar half-year", y=0.995
    )
    figure.tight_layout(rect=(0, 0, 1, 0.975), h_pad=1.6)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = args.output_dir / "instrument_lagged_return_zscore_half_year.png"
    bins_path = args.output_dir / "instrument_lagged_return_zscore_half_year_bins.csv"
    summary_path = (
        args.output_dir / "instrument_lagged_return_zscore_half_year_summary.csv"
    )
    figure.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    pd.concat(bin_tables, ignore_index=True).to_csv(bins_path, index=False)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(summary_path, index=False)

    print(summary.to_string(index=False))
    print(f"wrote {plot_path}")
    print(f"wrote {bins_path}")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
