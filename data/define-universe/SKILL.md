---
name: ml4t-define-universe
description: "Define point-in-time tradeable universes with liquidity filters. Use when constructing the investable asset set that avoids survivorship and liquidity bias."
when_to_use: "Use when specifying which assets a strategy can trade at each historical date"
dependencies: []
metadata:
  book_chapters: "2, 6"
  library: "ml4t-data"
paths: ["**/*data*.py", "**/*fetch*.py", "**/*bars*.py", "**/*universe*.py", "**/*calendar*.py", "**/*futures*.py", "**/*export*.py", "**/*synthetic*.py"]
---
# Define Universe

Using today's index constituents for a historical backtest introduces survivorship bias - you only trade winners that stayed in the index, inflating returns by 1-2% per year.

## The Problem

The S&P 500 today contains companies that survived and grew. The 2010 index
contained firms since acquired, delisted, or bankrupt. A backtest on current
members never sees these failures and overstates performance.

## The Pattern

### WRONG
```python
import polars as pl

# Current constituents applied to historical backtest
sp500_today = ["AAPL", "MSFT", "GOOGL", ...]  # 2024 list
prices = pl.read_parquet("prices.parquet").filter(
    pl.col("symbol").is_in(sp500_today)
)
# Backtest from 2010 - but these are 2024 survivors
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

universe_2015 = get_universe(all_prices, as_of="2015-01-02")
universe_2020 = get_universe(all_prices, as_of="2020-01-02")
```

## Handling Delistings

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

## Guardrails

- Free data sources (Yahoo Finance, etc.) almost always have survivorship bias - they only cover current tickers
- CRSP is the gold standard for survivorship-free US equities (includes delisting returns)
- A universe that never changes is a red flag - real indices reconstitute quarterly
- Penny stocks and micro-caps pass through if you skip liquidity filters, dominating signals with noise

## Production Implementation

```python
from ml4t.data import DataManager

dm = DataManager()
panel = dm.batch_load_universe(
    "sp500",
    start="2015-01-01",
    end="2024-12-31",
    provider="yahoo",
)
```

## Checklist

- [ ] Universe is point-in-time (no future constituents)
- [ ] Liquidity filter applied (price, volume, history)
- [ ] Delistings handled with terminal returns
- [ ] Rebalance schedule defined (quarterly typical)
- [ ] Data source is survivorship-free or bias is documented
