---
name: ml4t-survivorship-bias
description: "Account for delisted and removed securities in historical analysis. Use when constructing universes or computing cross-sectional features to avoid survivor-only inflation."
when_to_use: "Use when constructing trading universes or evaluating strategies on equity, crypto, or ETF panels"
dependencies: []
metadata:
  book_chapters: "2, 6"
  library: "ml4t-data"
---
# Survivorship Bias

Testing a strategy only on securities that exist today removes the worst performers from history, inflating backtest returns by 1--2% per year.

## The Problem

If you download today's S&P 500 constituents and run a backtest starting in 2008, you exclude Lehman Brothers, Bear Stearns, Washington Mutual, and every other company that was removed after distress. The remaining panel has a built-in upward bias because you already know these firms survived.

This is worst for value and small-cap strategies, which overweight distressed names -- exactly the ones that get delisted. A long-short value backtest on a survivor-biased universe can show +3% alpha that vanishes entirely on a survivorship-free dataset.

## The Pattern

### WRONG

```python
import polars as pl

# Use today's index members for a historical backtest
current_members = pl.read_csv("sp500_current.csv")  # 2024 list
prices = pl.read_parquet("prices.parquet")

backtest_universe = prices.filter(
    pl.col("symbol").is_in(current_members["symbol"])
)
# Missing: every company removed between 2008 and 2024
```

### CORRECT

```python
import polars as pl

# Use point-in-time index constituents
constituents = pl.read_parquet("sp500_constituents_history.parquet")
prices = pl.read_parquet("prices.parquet")  # includes delisted symbols

# For each date, use only the members as of that date
backtest_universe = prices.join(
    constituents,
    on=["symbol", "timestamp"],
    how="inner",
)
```

## Delisting Returns

Dropping a delisted stock on its last trading day ignores the terminal return. Include delisting outcomes:

```python
delisting_return = {
    "bankruptcy":      -1.00,   # total loss
    "acquisition":      0.00,   # use actual tender premium if available
    "going_private":    0.00,   # use tender offer price
    "exchange_change":  0.00,   # continue tracking on new exchange
}
# Apply the delisting return on the last traded date
```

## Data Source Quality

| Source | Survivorship-free? | Notes |
|--------|-------------------|-------|
| CRSP | Yes | Gold standard, includes delistings |
| NASDAQ Data Link (Wiki) | Yes | 1962--2018, includes delisted companies |
| Yahoo Finance | No | Current tickers only |
| Most free APIs | No | Survivor-biased by default |
| Crypto exchanges | Partial | Coins get delisted frequently |

## Guardrails

- Any universe built from a single "current members" list is survivor-biased.
- S&P 500 changes 20--25 constituents per year; over a 10-year backtest that is 200+ changes.
- Free data almost always has survivorship bias. Budget for CRSP or equivalent if equity research is serious.
- ETF and crypto markets have high turnover -- fund closures and coin delistings are common and material.

## Production Implementation

`ml4t-data` exposes a survivorship-bias-free historical US equities archive through 2018:

```python
from ml4t.data.providers.wiki_prices import WikiPricesProvider

provider = WikiPricesProvider()
aapl = provider.fetch_ohlcv("AAPL", "2010-01-01", "2018-03-27")
# The archive includes delisted companies; PIT constituents still need explicit handling
```

## Checklist

- [ ] Universe uses point-in-time index constituents, not current membership
- [ ] Delisting returns included (not silently dropped)
- [ ] Index reconstitution events tracked over the backtest period
- [ ] Data source documented for survivorship treatment
- [ ] Value/small-cap strategies double-checked for survivorship sensitivity
