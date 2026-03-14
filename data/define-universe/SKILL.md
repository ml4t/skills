---
name: ml4t-define-universe
description: Define point-in-time tradeable universes with liquidity filters. Use when specifying which assets a strategy can trade at each historical date.
dependencies: []
metadata:
  book_chapters: "2, 6"
  library: "ml4t-data"
---

# Define Universe

Using today's index constituents for a historical backtest introduces survivorship bias — you only trade winners that stayed in the index, inflating returns by 1-2% per year.

## The Problem

The S&P 500 today contains companies that survived and grew. The S&P 500 in 2010 contained Lehman Brothers, Enron's successors, and hundreds of firms since acquired, delisted, or bankrupt. A strategy backtested on current members never sees these failures, systematically overstating performance. Beyond survivorship, illiquid assets that pass no real-world execution test can dominate signal if you skip liquidity filters.

## The Pattern

### WRONG
```python
import polars as pl

# Current constituents applied to historical backtest
sp500_today = ["AAPL", "MSFT", "GOOGL", ...]  # 2024 list
prices = pl.read_parquet("prices.parquet").filter(
    pl.col("symbol").is_in(sp500_today)
)
# Backtest from 2010 — but these are 2024 survivors
```

### CORRECT
```python
import polars as pl

def get_universe(
    prices: pl.DataFrame,
    as_of: str,
    min_price: float = 5.0,
    min_avg_dollar_volume: float = 5_000_000,
    min_history_days: int = 252,
    lookback_days: int = 63,
) -> list[str]:
    """Point-in-time universe: only assets tradeable on as_of date."""
    cutoff = pl.lit(as_of).str.to_date()

    candidates = (
        prices.filter(pl.col("timestamp") <= cutoff)
        .group_by("symbol")
        .agg(
            last_price=pl.col("close").last(),
            avg_dollar_vol=(pl.col("close") * pl.col("volume"))
                .tail(lookback_days).mean(),
            n_days=pl.col("timestamp").n_unique(),
            last_trade=pl.col("timestamp").max(),
        )
        .filter(
            (pl.col("last_price") >= min_price)
            & (pl.col("avg_dollar_vol") >= min_avg_dollar_volume)
            & (pl.col("n_days") >= min_history_days)
            & (pl.col("last_trade") == cutoff)  # Must be actively trading
        )
    )
    return candidates["symbol"].to_list()

# Recompute universe at each rebalance date — never use a static list
universe_2015 = get_universe(all_prices, as_of="2015-01-02")
universe_2020 = get_universe(all_prices, as_of="2020-01-02")
```

## Handling Delistings

Ignoring delistings biases returns upward. When an asset leaves the universe, assign its terminal return.

```python
DELISTING_RETURNS = {
    "bankruptcy": -1.0,
    "acquisition": 0.0,     # Use actual tender premium if available
    "going_private": 0.0,
}

def apply_delisting_returns(returns: pl.DataFrame, delistings: pl.DataFrame):
    """Replace last return with delisting return for removed assets."""
    return returns.join(delistings, on=["symbol", "timestamp"], how="left").with_columns(
        pl.when(pl.col("delist_type").is_not_null())
        .then(pl.col("delist_return"))
        .otherwise(pl.col("ret"))
        .alias("ret")
    )
```

## Rebalance Hysteresis

Avoid excessive turnover from assets entering and leaving near filter thresholds.

```python
# Buffer: asset must exceed threshold by 5% to enter,
# but only drops out if it falls 5% below threshold
ENTRY_THRESHOLD = 5_250_000   # $5M * 1.05
EXIT_THRESHOLD  = 4_750_000   # $5M * 0.95
```

## Guardrails

- Free data sources (Yahoo Finance, etc.) almost always have survivorship bias — they only cover current tickers
- CRSP is the gold standard for survivorship-free US equities (includes delisting returns)
- A universe that never changes is a red flag — real indices reconstitute quarterly
- Penny stocks and micro-caps pass through if you skip liquidity filters, dominating signals with noise

## Production Implementation

`ml4t-data` provides point-in-time universe construction:

```python
from ml4t.data import DataManager

dm = DataManager()
# Survivorship-free panel with delisting returns
equities = dm.load("us_equities")
# Universe filters applied via DataManager configuration
```

## Checklist

- [ ] Universe is point-in-time (no future constituents)
- [ ] Liquidity filter applied (price, volume, history)
- [ ] Delistings handled with terminal returns
- [ ] Rebalance schedule defined (quarterly typical)
- [ ] Hysteresis buffer prevents churn at thresholds
- [ ] Data source is survivorship-free or bias is documented
