---
name: ml4t-microstructure-features
description: Features from order flow and market microstructure — bid-ask spread, VPIN, order imbalance, Kyle's lambda. Use when building intraday or short-horizon models with tick/quote data.
dependencies: []
metadata:
  book_chapters: "3, 8"
  library: ""
---

# Microstructure Features

OHLCV bars discard 99% of the information in the order book. Microstructure features extract signals from trade flow, spread dynamics, and price impact that daily data cannot capture.

## The Problem

Models built on daily OHLCV miss short-lived signals: institutional block trades, liquidity withdrawal before events, and informed order flow. These signals are visible in tick data (trades, quotes, order book snapshots) but require purpose-built features to extract.

## The Pattern

### WRONG
```python
import polars as pl

# Only OHLCV features — misses order flow, liquidity, and price impact
features = df.with_columns(
    ret=pl.col("close").pct_change(),
    vol=pl.col("close").pct_change().rolling_std(20),
    volume_ma=pl.col("volume").rolling_mean(20),
)
```

### CORRECT
```python
import polars as pl
import numpy as np

# Microstructure features from tick/quote data
def compute_microstructure(trades: pl.DataFrame, quotes: pl.DataFrame) -> pl.DataFrame:
    # 1. Order flow imbalance (tick rule classification)
    signed = trades.with_columns(
        signed_vol=pl.when(pl.col("price") > pl.col("price").shift(1))
        .then(pl.col("size"))
        .when(pl.col("price") < pl.col("price").shift(1))
        .then(-pl.col("size"))
        .otherwise(0)
    )
    ofi = signed.group_by_dynamic("timestamp", every="5m").agg(
        ofi=pl.col("signed_vol").sum(),
        total_vol=pl.col("size").sum(),
    )

    # 2. Relative spread (liquidity cost)
    spread = quotes.with_columns(
        rel_spread=(pl.col("ask") - pl.col("bid")) / ((pl.col("ask") + pl.col("bid")) / 2)
    )

    # 3. Amihud illiquidity (price impact per dollar volume)
    amihud = trades.group_by_dynamic("timestamp", every="1d").agg(
        amihud=pl.col("price").pct_change().abs().mean()
        / (pl.col("price") * pl.col("size")).sum()
    )
    return ofi, spread, amihud
```

## Key Microstructure Features

| Feature | Data Needed | What It Captures |
|---------|-------------|------------------|
| Order flow imbalance (OFI) | Trades | Net buying/selling pressure |
| Relative spread | Quotes | Liquidity cost, informed trading |
| VPIN | Trades | Probability of informed trading |
| Kyle's lambda | Trades + quotes | Price impact per unit flow |
| Amihud illiquidity | Daily bars | Price sensitivity to volume |
| VWAP deviation | Intraday bars | Institutional activity |

## VPIN (Volume-Synchronized Probability of Informed Trading)

```python
def compute_vpin(trades: pl.DataFrame, bucket_size: int = 1000) -> pl.Series:
    """Estimate informed trading probability from volume buckets."""
    signed = trades.with_columns(
        signed_vol=pl.when(pl.col("price") > pl.col("price").shift(1))
        .then(pl.col("size")).otherwise(-pl.col("size"))
    )
    # Bucket by fixed volume, compute buy/sell imbalance per bucket
    buckets = signed.with_columns(bucket=(pl.col("size").cum_sum() // bucket_size))
    vpin = buckets.group_by("bucket").agg(
        imbalance=pl.col("signed_vol").sum().abs() / pl.col("size").sum()
    )
    return vpin.select("imbalance").to_series().rolling_mean(50)
```

## Guardrails

- **Data requirements are high** — tick/quote data is 100-1000x larger than daily bars
- **Latency matters for live trading** — stale microstructure features lose value in milliseconds
- **Most useful for intraday horizons** — daily aggregates of microstructure signals lose granularity
- **Trade classification accuracy** — tick rule is ~80% accurate; Lee-Ready improves to ~85%

## Checklist

- [ ] Tick or quote data available at required granularity
- [ ] Trade classification method documented (tick rule, Lee-Ready, or exchange-provided)
- [ ] Feature horizon matches trading horizon (intraday features for intraday strategies)
- [ ] Spread and OFI computed per-symbol, not globally
- [ ] Data latency acceptable for intended use (live vs research)
