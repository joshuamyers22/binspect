"""Backtest an hourly long-short portfolio formed from lagged-return ranks."""

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
    WHERE (
        rankings.rank BETWEEN %(long_start)s AND %(long_end)s
        OR rankings.rank BETWEEN %(short_start)s AND %(short_end)s
    )
      AND current.close IS NOT NULL
      AND current.close <> 0
      AND future.close IS NOT NULL
), portfolio_returns AS (
    SELECT factor_time,
           AVG(next_1h_return) FILTER (
               WHERE rank BETWEEN %(long_start)s AND %(long_end)s
           ) AS long_return,
           AVG(next_1h_return) FILTER (
               WHERE rank BETWEEN %(short_start)s AND %(short_end)s
           ) AS short_asset_return,
           COUNT(*) FILTER (
               WHERE rank BETWEEN %(long_start)s AND %(long_end)s
           ) AS long_count,
           COUNT(*) FILTER (
               WHERE rank BETWEEN %(short_start)s AND %(short_end)s
           ) AS short_count
    FROM ranked_returns
    GROUP BY factor_time
)
SELECT factor_time,
       long_return,
       short_asset_return,
       long_return - short_asset_return AS portfolio_return
FROM portfolio_returns
WHERE long_count = %(long_count)s AND short_count = %(short_count)s
ORDER BY factor_time
"""


def load_returns(
    database_url: str,
    long_start: int,
    long_end: int,
    short_start: int,
    short_end: int,
) -> pd.DataFrame:
    rows: list[tuple[int, float, float, float]] = []
    with (
        psycopg.connect(
            database_url.replace("postgresql+psycopg://", "postgresql://")
        ) as conn,
        conn.cursor(name="rank_portfolio_backtest") as cursor,
    ):
        cursor.execute(
            QUERY,
            {
                "long_start": long_start,
                "long_end": long_end,
                "short_start": short_start,
                "short_end": short_end,
                "long_count": long_end - long_start + 1,
                "short_count": short_end - short_start + 1,
            },
        )
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


def performance_summary(
    returns: pd.Series, capital_mode: str
) -> dict[str, float | int | str | None]:
    elapsed_hours = (
        int((returns.index.max() - returns.index.min()) / pd.Timedelta(hours=1)) + 1
    )
    equity = (
        (1 + returns).cumprod()
        if capital_mode == "compounding"
        else 1 + returns.cumsum()
    )
    if capital_mode == "compounding":
        annualized_return = (
            equity.iloc[-1] ** (HOURS_PER_YEAR / elapsed_hours) - 1
            if equity.iloc[-1] > 0
            else np.nan
        )
    else:
        annualized_return = returns.sum() * HOURS_PER_YEAR / elapsed_hours
    annualized_volatility = returns.std(ddof=1) * np.sqrt(HOURS_PER_YEAR)
    nonpositive = equity.loc[equity <= 0]
    return {
        "start_utc": returns.index.min().isoformat(),
        "end_utc": returns.index.max().isoformat(),
        "observations": len(returns),
        "elapsed_hours": elapsed_hours,
        "coverage": len(returns) / elapsed_hours,
        "capital_mode": capital_mode,
        "ending_capital": equity.iloc[-1],
        "minimum_capital": equity.min(),
        "first_nonpositive_utc": (
            nonpositive.index[0].isoformat() if not nonpositive.empty else None
        ),
        "cumulative_return": equity.iloc[-1] - 1,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "annualized_sharpe": (
            returns.mean() / returns.std(ddof=1) * np.sqrt(HOURS_PER_YEAR)
        ),
        "maximum_drawdown": (equity / equity.cummax() - 1).min(),
        "positive_hour_rate": (returns > 0).mean(),
        "mean_hourly_return": returns.mean(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--long-start", type=int, default=1)
    parser.add_argument("--long-end", type=int, default=5)
    parser.add_argument("--short-start", type=int, default=16)
    parser.add_argument("--short-end", type=int, default=20)
    parser.add_argument(
        "--capital-mode",
        choices=("compounding", "static"),
        default="compounding",
    )
    args = parser.parse_args()
    if not (1 <= args.long_start <= args.long_end <= 20):
        parser.error("long ranks must satisfy 1 <= start <= end <= 20")
    if not (1 <= args.short_start <= args.short_end <= 20):
        parser.error("short ranks must satisfy 1 <= start <= end <= 20")
    if args.long_end >= args.short_start:
        parser.error("long and short rank ranges must not overlap")

    data = load_returns(
        args.db,
        args.long_start,
        args.long_end,
        args.short_start,
        args.short_end,
    )
    if data.empty:
        raise RuntimeError("No hours contain every requested long and short rank.")
    data["factor_time"] = pd.to_datetime(
        data.pop("factor_time_ms"), unit="ms", utc=True
    )
    data = data.set_index("factor_time")
    if (data["portfolio_return"] <= -1).any():
        raise RuntimeError(
            "Portfolio return reached -100%; compounded equity is invalid."
        )

    data["short_return"] = -data["short_asset_return"]
    data["equity"] = (
        (1 + data["portfolio_return"]).cumprod()
        if args.capital_mode == "compounding"
        else 1 + data["portfolio_return"].cumsum()
    )
    data["drawdown"] = data["equity"] / data["equity"].cummax() - 1
    data["year"] = data.index.year

    summary = pd.DataFrame(
        [performance_summary(data["portfolio_return"], args.capital_mode)]
    )
    yearly_groups = data.groupby("year", sort=True)["portfolio_return"]
    yearly = (
        (
            yearly_groups.apply(lambda values: (1 + values).prod() - 1)
            if args.capital_mode == "compounding"
            else yearly_groups.sum()
        )
        .rename("portfolio_return")
        .reset_index()
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = (
        f"rank_{args.long_start}_{args.long_end}_long_"
        f"{args.short_start}_{args.short_end}_short_hourly_portfolio"
    )
    if args.capital_mode == "static":
        stem += "_static_capital"
    returns_path = args.output_dir / f"{stem}_returns.csv"
    summary_path = args.output_dir / f"{stem}_summary.csv"
    yearly_path = args.output_dir / f"{stem}_yearly.csv"
    plot_path = args.output_dir / f"{stem}.png"
    data.drop(columns="year").to_csv(returns_path)
    summary.to_csv(summary_path, index=False)
    yearly.to_csv(yearly_path, index=False)

    figure, (equity_axis, yearly_axis) = plt.subplots(2, 1, figsize=(11, 8))
    equity_axis.plot(data.index, data["equity"], color="#1f1f1f", linewidth=1.2)
    if args.capital_mode == "compounding":
        equity_axis.set_yscale("log")
        equity_axis.set_ylabel("Portfolio equity (log scale)")
    else:
        equity_axis.set_ylabel("Static-base capital (initial capital = 1)")
    equity_axis.set_title(
        f"Hourly rank portfolio: long {args.long_start}-{args.long_end}, "
        f"short {args.short_start}-{args.short_end} ({args.capital_mode} capital)"
    )
    equity_axis.grid(alpha=0.25)

    colors = np.where(yearly["portfolio_return"] >= 0, "#287d4f", "#a33a3a")
    yearly_axis.bar(
        yearly["year"].astype(str), yearly["portfolio_return"], color=colors
    )
    yearly_axis.axhline(0, color="#555555", linewidth=0.8)
    yearly_axis.set_yscale("symlog", linthresh=0.5)
    yearly_axis.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    yearly_axis.set_ylabel(
        "Compounded return"
        if args.capital_mode == "compounding"
        else "P&L on initial capital"
    )
    yearly_axis.set_xlabel("Calendar year")
    yearly_axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close(figure)

    print(summary.to_string(index=False))
    print(
        "\nYearly compounded returns"
        if args.capital_mode == "compounding"
        else "\nYearly P&L on initial capital"
    )
    print(yearly.to_string(index=False))
    print(f"wrote {plot_path}")
    print(f"wrote {returns_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {yearly_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
