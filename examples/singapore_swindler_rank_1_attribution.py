"""Attribute the rank-1 long sleeve's hourly returns to individual assets."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg

QUERY = """
WITH valid_portfolio_hours AS (
    SELECT short_rank.factor_time
    FROM factor_rankings short_rank
    JOIN hourly_bars short_current
      ON short_current.symbol = short_rank.symbol
     AND short_current.open_time = short_rank.factor_time
    JOIN hourly_bars short_future
      ON short_future.symbol = short_rank.symbol
     AND short_future.open_time = short_rank.factor_time + 3600000
    WHERE short_rank.rank = 20
      AND short_current.close IS NOT NULL
      AND short_current.close <> 0
      AND short_future.close IS NOT NULL
)
SELECT rankings.factor_time,
       rankings.symbol,
       (future.close / current.close) - 1 AS next_1h_return
FROM factor_rankings rankings
JOIN valid_portfolio_hours valid
  ON valid.factor_time = rankings.factor_time
JOIN hourly_bars current
  ON current.symbol = rankings.symbol
 AND current.open_time = rankings.factor_time
JOIN hourly_bars future
  ON future.symbol = rankings.symbol
 AND future.open_time = rankings.factor_time + 3600000
WHERE rankings.rank = 1
  AND current.close IS NOT NULL
  AND current.close <> 0
  AND future.close IS NOT NULL
ORDER BY rankings.factor_time
"""


def load_returns(database_url: str) -> pd.DataFrame:
    rows: list[tuple[int, str, float]] = []
    with (
        psycopg.connect(
            database_url.replace("postgresql+psycopg://", "postgresql://")
        ) as conn,
        conn.cursor(name="rank_1_asset_attribution") as cursor,
    ):
        cursor.execute(QUERY)
        while batch := cursor.fetchmany(100_000):
            rows.extend(
                (int(time), str(symbol), float(hourly_return))
                for time, symbol, hourly_return in batch
            )
    return pd.DataFrame(rows, columns=["factor_time_ms", "symbol", "next_1h_return"])


def build_attribution(data: pd.DataFrame) -> pd.DataFrame:
    data = data.assign(log_return=np.log1p(data["next_1h_return"]))
    attribution = (
        data.groupby("symbol", sort=False)
        .agg(
            holding_hours=("next_1h_return", "size"),
            arithmetic_contribution=("next_1h_return", "sum"),
            log_return_contribution=("log_return", "sum"),
            mean_hourly_return=("next_1h_return", "mean"),
            hourly_volatility=("next_1h_return", "std"),
            positive_hour_rate=("next_1h_return", lambda values: (values > 0).mean()),
            worst_hour=("next_1h_return", "min"),
            best_hour=("next_1h_return", "max"),
        )
        .reset_index()
    )
    total_arithmetic = attribution["arithmetic_contribution"].sum()
    total_hours = attribution["holding_hours"].sum()
    attribution["share_of_rank_1_hours"] = attribution["holding_hours"] / total_hours
    attribution["share_of_arithmetic_contribution"] = (
        attribution["arithmetic_contribution"] / total_arithmetic
    )
    return attribution.sort_values("arithmetic_contribution", ascending=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()

    data = load_returns(args.db)
    if data.empty:
        raise RuntimeError("No valid next-hour returns exist for rank 1.")
    if (data["next_1h_return"] <= -1).any():
        raise RuntimeError("Rank-1 return reached -100%; log attribution is undefined.")
    data["factor_time"] = pd.to_datetime(
        data.pop("factor_time_ms"), unit="ms", utc=True
    )
    attribution = build_attribution(data)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = "rank_1_long_asset_attribution"
    detail_path = args.output_dir / f"{stem}_hourly.csv"
    attribution_path = args.output_dir / f"{stem}.csv"
    plot_path = args.output_dir / f"{stem}.png"
    data.to_csv(detail_path, index=False)
    attribution.to_csv(attribution_path, index=False)

    display = pd.concat(
        [
            attribution.tail(15),
            attribution.head(15).sort_values("arithmetic_contribution"),
        ]
    ).drop_duplicates("symbol")
    display = display.sort_values("arithmetic_contribution")
    display["plot_symbol"] = display["symbol"].map(
        lambda symbol: symbol.encode("ascii", "backslashreplace").decode("ascii")
    )
    colors = np.where(display["arithmetic_contribution"] >= 0, "#287d4f", "#a33a3a")
    figure_height = max(6.0, 0.3 * len(display))
    figure, axis = plt.subplots(figsize=(10, figure_height))
    axis.barh(display["plot_symbol"], display["arithmetic_contribution"], color=colors)
    axis.axvline(0, color="#555555", linewidth=0.8)
    axis.set_xlabel("Additive sum of hourly rank-1 returns")
    axis.set_ylabel("Asset")
    axis.set_title("Rank-1 long sleeve: 15 largest positive and negative contributors")
    axis.grid(axis="x", alpha=0.25)
    figure.tight_layout()
    figure.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close(figure)

    print(f"rank-1 hours: {len(data):,}")
    print(f"assets appearing at rank 1: {len(attribution):,}")
    print(f"arithmetic return sum: {data['next_1h_return'].sum():.8f}")
    print(f"long-only compounded return: {(1 + data['next_1h_return']).prod() - 1:.8f}")
    print("\nLargest positive contributors")
    print(attribution.head(10).to_string(index=False))
    print("\nLargest negative contributors")
    print(
        attribution.tail(10)
        .sort_values("arithmetic_contribution")
        .to_string(index=False)
    )
    print(f"wrote {plot_path}")
    print(f"wrote {attribution_path}")
    print(f"wrote {detail_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
