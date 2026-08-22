"""Plot lagged-return z-scores against six individual forward-hour returns."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg
from matplotlib.ticker import PercentFormatter

import binspect

HORIZONS = range(1, 7)
FORWARD_COLUMNS = [f"next_{horizon}h_return" for horizon in HORIZONS]
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
       (p1.close / p0.close) - 1 AS next_1h_return,
       (p2.close / p1.close) - 1 AS next_2h_return,
       (p3.close / p2.close) - 1 AS next_3h_return,
       (p4.close / p3.close) - 1 AS next_4h_return,
       (p5.close / p4.close) - 1 AS next_5h_return,
       (p6.close / p5.close) - 1 AS next_6h_return
FROM standardized s
JOIN hourly_bars p0
  ON p0.symbol = s.symbol AND p0.open_time = s.factor_time
JOIN hourly_bars p1
  ON p1.symbol = s.symbol AND p1.open_time = s.factor_time + 3600000
JOIN hourly_bars p2
  ON p2.symbol = s.symbol AND p2.open_time = s.factor_time + 7200000
JOIN hourly_bars p3
  ON p3.symbol = s.symbol AND p3.open_time = s.factor_time + 10800000
JOIN hourly_bars p4
  ON p4.symbol = s.symbol AND p4.open_time = s.factor_time + 14400000
JOIN hourly_bars p5
  ON p5.symbol = s.symbol AND p5.open_time = s.factor_time + 18000000
JOIN hourly_bars p6
  ON p6.symbol = s.symbol AND p6.open_time = s.factor_time + 21600000
WHERE s.lagged_return_zscore IS NOT NULL
  AND p0.close IS NOT NULL AND p0.close <> 0
  AND p1.close IS NOT NULL AND p1.close <> 0
  AND p2.close IS NOT NULL AND p2.close <> 0
  AND p3.close IS NOT NULL AND p3.close <> 0
  AND p4.close IS NOT NULL AND p4.close <> 0
  AND p5.close IS NOT NULL AND p5.close <> 0
  AND p6.close IS NOT NULL
ORDER BY s.factor_time, s.symbol
"""


def load_data(database_url: str) -> pd.DataFrame:
    columns: list[list[float]] = [[] for _ in range(7)]
    with (
        psycopg.connect(
            database_url.replace("postgresql+psycopg://", "postgresql://")
        ) as conn,
        conn.cursor(name="binspect_factor_export") as cursor,
    ):
        cursor.execute(QUERY)
        while rows := cursor.fetchmany(100_000):
            for index, values in enumerate(zip(*rows, strict=True)):
                columns[index].extend(float(value) for value in values)
    return pd.DataFrame(
        {
            "lagged_return_zscore": np.asarray(columns[0]),
            **{
                name: np.asarray(columns[index])
                for index, name in enumerate(FORWARD_COLUMNS, 1)
            },
        }
    )


def style_axis(axis: plt.Axes, horizon: int) -> None:
    axis.set_xlabel("Hourly cross-sectional z-score of lagged return")
    axis.set_ylabel(f"Forward hour {horizon} return")
    axis.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=2))
    axis.axhline(0, color="#555555", linewidth=0.7, alpha=0.7)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--bins", type=int, default=20)
    args = parser.parse_args()

    data = load_data(args.db)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, float | int]] = []
    results = []

    for horizon, column in zip(HORIZONS, FORWARD_COLUMNS, strict=True):
        result = binspect.binscatter(
            data,
            x="lagged_return_zscore",
            y=column,
            bins=args.bins,
            binning="quantile",
            ci=None,
        )
        results.append(result)
        with binspect.theme("paper"):
            figure, axis = plt.subplots(figsize=(9, 6))
        result.plot(
            ax=axis,
            theme="paper",
            annotate="audit",
            title=f"Lagged return z-score vs. forward hour {horizon} return",
        )
        style_axis(axis, horizon)
        figure.tight_layout()
        figure.savefig(
            args.output_dir / f"lagged_return_zscore_vs_next_{horizon}h_return.png",
            dpi=180,
            bbox_inches="tight",
        )
        plt.close(figure)
        result.table.to_csv(
            args.output_dir / f"lagged_return_zscore_vs_next_{horizon}h_bins.csv",
            index=False,
        )
        summary_rows.append(
            {
                "forward_hour": horizon,
                "observations": len(data),
                "correlation": data[["lagged_return_zscore", column]].corr().iloc[0, 1],
                "ols_slope": result.fit.slope,
                "r_squared": result.fit.r_sq,
                "lowest_z_bin_mean_return": result.table.iloc[0]["y_mean"],
                "highest_z_bin_mean_return": result.table.iloc[-1]["y_mean"],
            }
        )

    with binspect.theme("paper"):
        combined, axes = plt.subplots(2, 3, figsize=(16, 9), sharex=True, sharey=True)
    for horizon, result, axis in zip(HORIZONS, results, axes.flat, strict=True):
        result.plot(
            ax=axis,
            theme="paper",
            annotate=None,
            title=f"Forward hour {horizon}",
        )
        style_axis(axis, horizon)
    combined.suptitle("Lagged return z-score vs. six individual forward-hour returns")
    combined.tight_layout()
    combined.savefig(
        args.output_dir / "lagged_return_zscore_vs_next_6_individual_hours.png",
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(combined)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(
        args.output_dir / "lagged_return_zscore_forward_hours_summary.csv", index=False
    )
    print(summary.to_string(index=False))
    print(f"common complete-case observations: {len(data):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
