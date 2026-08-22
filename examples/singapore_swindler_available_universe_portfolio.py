"""Backtest extreme lagged-return ranks across all stored hourly symbols."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg

HOURS_PER_YEAR = 365.25 * 24

QUERY = """
WITH candidates AS (
    SELECT current.open_time AS factor_time,
           current.symbol,
           (lag_23.close / lag_24.close) - 1 AS lagged_24_return,
           (future.close / current.close) - 1 AS next_1h_return
    FROM hourly_bars current
    JOIN hourly_bars lag_24
      ON lag_24.symbol = current.symbol
     AND lag_24.open_time = current.open_time - 86400000
    JOIN hourly_bars lag_23
      ON lag_23.symbol = current.symbol
     AND lag_23.open_time = current.open_time - 82800000
    JOIN hourly_bars future
      ON future.symbol = current.symbol
     AND future.open_time = current.open_time + 3600000
    WHERE lag_24.close IS NOT NULL
      AND lag_24.close <> 0
      AND lag_23.close IS NOT NULL
      AND current.close IS NOT NULL
      AND current.close <> 0
      AND future.close IS NOT NULL
), ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY factor_time
               ORDER BY lagged_24_return ASC, symbol ASC
           ) AS worst_rank,
           ROW_NUMBER() OVER (
               PARTITION BY factor_time
               ORDER BY lagged_24_return DESC, symbol ASC
           ) AS best_rank,
           COUNT(*) OVER (PARTITION BY factor_time) AS universe_size
    FROM candidates
)
SELECT factor_time,
       MAX(symbol) FILTER (WHERE worst_rank = 1) AS long_symbol,
       MAX(lagged_24_return) FILTER (WHERE worst_rank = 1) AS long_signal,
       MAX(next_1h_return) FILTER (WHERE worst_rank = 1) AS long_return,
       MAX(symbol) FILTER (WHERE best_rank = 1) AS short_symbol,
       MAX(lagged_24_return) FILTER (WHERE best_rank = 1) AS short_signal,
       MAX(next_1h_return) FILTER (WHERE best_rank = 1) AS short_asset_return,
       MAX(universe_size) AS universe_size
FROM ranked
GROUP BY factor_time
HAVING MAX(universe_size) >= 2
ORDER BY factor_time
"""


def load_returns(database_url: str) -> pd.DataFrame:
    rows: list[tuple[int, str, float, float, str, float, float, int]] = []
    with (
        psycopg.connect(
            database_url.replace("postgresql+psycopg://", "postgresql://")
        ) as conn,
        conn.cursor(name="available_universe_portfolio") as cursor,
    ):
        cursor.execute(QUERY)
        while batch := cursor.fetchmany(100_000):
            rows.extend(
                (
                    int(time),
                    str(long_symbol),
                    float(long_signal),
                    float(long_return),
                    str(short_symbol),
                    float(short_signal),
                    float(short_return),
                    int(universe_size),
                )
                for (
                    time,
                    long_symbol,
                    long_signal,
                    long_return,
                    short_symbol,
                    short_signal,
                    short_return,
                    universe_size,
                ) in batch
            )
    return pd.DataFrame(
        rows,
        columns=[
            "factor_time_ms",
            "long_symbol",
            "long_signal",
            "long_return",
            "short_symbol",
            "short_signal",
            "short_asset_return",
            "universe_size",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()

    data = load_returns(args.db)
    if data.empty:
        raise RuntimeError("No hours contain at least two eligible stored symbols.")
    data["factor_time"] = pd.to_datetime(
        data.pop("factor_time_ms"), unit="ms", utc=True
    )
    data = data.set_index("factor_time")
    data["short_return"] = -data["short_asset_return"]
    data["portfolio_return"] = data["long_return"] + data["short_return"]
    data["static_capital"] = 1 + data["portfolio_return"].cumsum()
    data["drawdown"] = data["static_capital"] / data["static_capital"].cummax() - 1
    data["year"] = data.index.year

    elapsed_hours = (
        int((data.index.max() - data.index.min()) / pd.Timedelta(hours=1)) + 1
    )
    nonpositive = data.loc[data["static_capital"] <= 0]
    returns = data["portfolio_return"]
    summary = pd.DataFrame(
        [
            {
                "start_utc": data.index.min().isoformat(),
                "end_utc": data.index.max().isoformat(),
                "observations": len(data),
                "coverage": len(data) / elapsed_hours,
                "distinct_selected_symbols": int(
                    pd.concat([data["long_symbol"], data["short_symbol"]]).nunique()
                ),
                "minimum_hourly_universe": int(data["universe_size"].min()),
                "median_hourly_universe": float(data["universe_size"].median()),
                "maximum_hourly_universe": int(data["universe_size"].max()),
                "ending_static_capital": data["static_capital"].iloc[-1],
                "minimum_static_capital": data["static_capital"].min(),
                "first_nonpositive_utc": (
                    nonpositive.index[0].isoformat() if not nonpositive.empty else None
                ),
                "long_cumulative_pnl": data["long_return"].sum(),
                "short_cumulative_pnl": data["short_return"].sum(),
                "cumulative_pnl": returns.sum(),
                "annualized_pnl": returns.sum() * HOURS_PER_YEAR / elapsed_hours,
                "annualized_volatility": returns.std(ddof=1) * np.sqrt(HOURS_PER_YEAR),
                "annualized_sharpe": returns.mean()
                / returns.std(ddof=1)
                * np.sqrt(HOURS_PER_YEAR),
                "maximum_drawdown": data["drawdown"].min(),
                "positive_hour_rate": (returns > 0).mean(),
                "mean_hourly_return": returns.mean(),
            }
        ]
    )
    yearly = (
        data.groupby("year", sort=True)["portfolio_return"]
        .sum()
        .rename("pnl_on_initial_capital")
        .reset_index()
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = "available_hourly_universe_extreme_rank_static_portfolio"
    returns_path = args.output_dir / f"{stem}_returns.csv"
    summary_path = args.output_dir / f"{stem}_summary.csv"
    yearly_path = args.output_dir / f"{stem}_yearly.csv"
    plot_path = args.output_dir / f"{stem}.png"
    data.drop(columns="year").to_csv(returns_path)
    summary.to_csv(summary_path, index=False)
    yearly.to_csv(yearly_path, index=False)

    figure, (capital_axis, universe_axis) = plt.subplots(2, 1, figsize=(11, 8))
    capital_axis.plot(data.index, data["static_capital"], color="#1f1f1f")
    capital_axis.axhline(0, color="#a33a3a", linewidth=0.8)
    capital_axis.set_ylabel("Static capital (initial capital = 1)")
    capital_axis.set_title(
        "All stored hourly symbols: long worst lagged return, short best"
    )
    capital_axis.grid(alpha=0.25)

    daily_universe = data["universe_size"].resample("1D").last().dropna()
    universe_axis.plot(daily_universe.index, daily_universe, color="#375a7f")
    universe_axis.set_ylabel("Available symbols")
    universe_axis.set_xlabel("UTC date")
    universe_axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close(figure)

    print(summary.to_string(index=False))
    print("\nYearly P&L on initial capital")
    print(yearly.to_string(index=False))
    print(f"wrote {plot_path}")
    print(f"wrote {returns_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {yearly_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
