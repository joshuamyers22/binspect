"""Backtest the hourly lagged-return rank 1-5 long / 16-20 short portfolio."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg
from matplotlib.ticker import PercentFormatter

HOURS_PER_YEAR = 365.25 * 24

QUERY = """
WITH ranked_returns AS (
    SELECT rankings.factor_time,
           rankings.rank,
           (future.close / current.close) - 1 AS next_1h_return
    FROM factor_rankings rankings
    JOIN hourly_bars current
      ON current.symbol = rankings.symbol
     AND current.open_time = rankings.factor_time
    JOIN hourly_bars future
      ON future.symbol = rankings.symbol
     AND future.open_time = rankings.factor_time + 3600000
    WHERE rankings.rank BETWEEN 1 AND 20
      AND current.close IS NOT NULL
      AND current.close <> 0
      AND future.close IS NOT NULL
), portfolio_returns AS (
    SELECT factor_time,
           AVG(next_1h_return) FILTER (WHERE rank BETWEEN 1 AND 5)
             AS long_return,
           AVG(next_1h_return) FILTER (WHERE rank BETWEEN 16 AND 20)
             AS short_asset_return,
           COUNT(*) FILTER (WHERE rank BETWEEN 1 AND 5) AS long_count,
           COUNT(*) FILTER (WHERE rank BETWEEN 16 AND 20) AS short_count
    FROM ranked_returns
    GROUP BY factor_time
)
SELECT factor_time,
       long_return,
       short_asset_return,
       long_return - short_asset_return AS portfolio_return
FROM portfolio_returns
WHERE long_count = 5 AND short_count = 5
ORDER BY factor_time
"""


def load_returns(database_url: str) -> pd.DataFrame:
    rows: list[tuple[int, float, float, float]] = []
    with (
        psycopg.connect(
            database_url.replace("postgresql+psycopg://", "postgresql://")
        ) as conn,
        conn.cursor(name="rank_portfolio_backtest") as cursor,
    ):
        cursor.execute(QUERY)
        while batch := cursor.fetchmany(100_000):
            rows.extend(
                (int(time), float(long), float(short), float(portfolio))
                for time, long, short, portfolio in batch
            )
    return pd.DataFrame(
        rows,
        columns=[
            "factor_time_ms",
            "long_return",
            "short_asset_return",
            "portfolio_return",
        ],
    )


def performance_summary(returns: pd.Series) -> dict[str, float | int | str]:
    wealth = (1 + returns).cumprod()
    elapsed_hours = (
        int((returns.index.max() - returns.index.min()) / pd.Timedelta(hours=1)) + 1
    )
    annualized_return = (
        wealth.iloc[-1] ** (HOURS_PER_YEAR / elapsed_hours) - 1
        if wealth.iloc[-1] > 0
        else np.nan
    )
    annualized_volatility = returns.std(ddof=1) * np.sqrt(HOURS_PER_YEAR)
    return {
        "start_utc": returns.index.min().isoformat(),
        "end_utc": returns.index.max().isoformat(),
        "observations": len(returns),
        "elapsed_hours": elapsed_hours,
        "coverage": len(returns) / elapsed_hours,
        "cumulative_return": wealth.iloc[-1] - 1,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "annualized_sharpe": (
            returns.mean() / returns.std(ddof=1) * np.sqrt(HOURS_PER_YEAR)
        ),
        "maximum_drawdown": (wealth / wealth.cummax() - 1).min(),
        "positive_hour_rate": (returns > 0).mean(),
        "mean_hourly_return": returns.mean(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()

    data = load_returns(args.db)
    if data.empty:
        raise RuntimeError("No hours contain all five long and all five short ranks.")
    data["factor_time"] = pd.to_datetime(
        data.pop("factor_time_ms"), unit="ms", utc=True
    )
    data = data.set_index("factor_time")
    if (data["portfolio_return"] <= -1).any():
        raise RuntimeError(
            "Portfolio return reached -100%; compounded equity is invalid."
        )

    data["short_return"] = -data["short_asset_return"]
    data["equity"] = (1 + data["portfolio_return"]).cumprod()
    data["drawdown"] = data["equity"] / data["equity"].cummax() - 1
    data["year"] = data.index.year

    summary = pd.DataFrame([performance_summary(data["portfolio_return"])])
    yearly = (
        data.groupby("year", sort=True)["portfolio_return"]
        .apply(lambda values: (1 + values).prod() - 1)
        .rename("portfolio_return")
        .reset_index()
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = "rank_1_5_long_16_20_short_hourly_portfolio"
    returns_path = args.output_dir / f"{stem}_returns.csv"
    summary_path = args.output_dir / f"{stem}_summary.csv"
    yearly_path = args.output_dir / f"{stem}_yearly.csv"
    plot_path = args.output_dir / f"{stem}.png"
    data.drop(columns="year").to_csv(returns_path)
    summary.to_csv(summary_path, index=False)
    yearly.to_csv(yearly_path, index=False)

    figure, (equity_axis, yearly_axis) = plt.subplots(2, 1, figsize=(11, 8))
    equity_axis.plot(data.index, data["equity"], color="#1f1f1f", linewidth=1.2)
    equity_axis.set_yscale("log")
    equity_axis.set_ylabel("Portfolio equity (log scale)")
    equity_axis.set_title(
        "Hourly rank portfolio: long 1-5, short 16-20 (equal-weighted legs)"
    )
    equity_axis.grid(alpha=0.25)

    colors = np.where(yearly["portfolio_return"] >= 0, "#287d4f", "#a33a3a")
    yearly_axis.bar(
        yearly["year"].astype(str), yearly["portfolio_return"], color=colors
    )
    yearly_axis.axhline(0, color="#555555", linewidth=0.8)
    yearly_axis.set_yscale("symlog", linthresh=0.5)
    yearly_axis.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    yearly_axis.set_ylabel("Compounded return")
    yearly_axis.set_xlabel("Calendar year")
    yearly_axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close(figure)

    print(summary.to_string(index=False))
    print("\nYearly compounded returns")
    print(yearly.to_string(index=False))
    print(f"wrote {plot_path}")
    print(f"wrote {returns_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {yearly_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
