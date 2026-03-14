---
name: ml4t-continuous-futures
description: Build roll-adjusted continuous futures series without artificial price jumps. Use when constructing futures time series for backtesting or feature engineering.
dependencies: [fetch-data]
metadata:
  book_chapters: "2, 3"
  library: "ml4t-data"
---

# Continuous Futures

Naively concatenating front-month futures contracts creates artificial price jumps at each roll, corrupting returns and every feature derived from price levels.

## The Problem

Futures contracts expire. When you roll from the March contract to the June contract, the price can jump $5 overnight — not because the market moved, but because the new contract trades at a different level (contango or backwardation). Concatenating contracts without adjustment produces fake returns of 2-5% at every roll date. A momentum signal built on this series will fire on roll artifacts, not real trends. Over a year with 4-12 rolls, this distortion compounds.

## The Pattern

### WRONG
```python
import polars as pl

# Naive concatenation — price jumps at every roll
contracts = pl.read_parquet("futures_contracts.parquet")
continuous = (
    contracts.sort("timestamp")
    .group_by("timestamp")
    .agg(pl.col("close").first())  # Just take front month
)
# 3-5% fake returns at each quarterly roll
```

### CORRECT
```python
import polars as pl
import numpy as np

def panama_canal_adjust(
    contracts: pl.DataFrame,
    roll_dates: list[str],
) -> pl.DataFrame:
    """Back-adjust prices using Panama Canal (additive) method.

    At each roll, shift all prior history by the gap between old and
    new contract so that returns across the roll boundary are real.
    """
    df = contracts.sort("timestamp")
    adj = df["close"].to_numpy().copy().astype(np.float64)

    for roll_date in sorted(roll_dates, reverse=True):
        mask = df["timestamp"].to_numpy() < np.datetime64(roll_date)
        # Gap = new contract close - old contract close on roll date
        roll_idx = np.searchsorted(df["timestamp"].to_numpy(), np.datetime64(roll_date))
        if roll_idx == 0 or roll_idx >= len(adj):
            continue
        gap = adj[roll_idx] - adj[roll_idx - 1]
        # Subtract gap from all prior prices (Panama canal back-adjustment)
        adj[mask] -= gap

    return df.with_columns(adj_close=pl.Series("adj_close", adj))
```

## Roll Methods

| Method | Adjustment | Preserves | Best For |
|--------|-----------|-----------|----------|
| Panama (additive) | Shift by price gap | Returns and levels | Trend following |
| Ratio (multiplicative) | Multiply by price ratio | Percentage returns | Cross-asset comparison |
| Return-based | Chain daily returns | Returns only | Pure return signals |
| No adjustment | None | Nothing useful | Never use for backtesting |

## Term Structure and Carry

Loading multiple contract months enables carry signals — the slope of the futures term structure.

```python
# Carry = (front - back) / front
front = prices.filter(pl.col("position") == 0)
back = prices.filter(pl.col("position") == 1)

carry = front.join(back, on=["product", "timestamp"], suffix="_back").with_columns(
    carry=(pl.col("close") - pl.col("close_back")) / pl.col("close")
)
# Negative carry (contango) = cost of holding; positive (backwardation) = benefit
```

## Guardrails

- Always use `adj_close` for returns and features — raw `close` is only for current price reference
- Roll dates vary by product: energy rolls monthly, equity index rolls quarterly
- Panama adjustment changes historical price levels — do not use adjusted prices for margin calculations
- Carry signals require accurate term structure with at least 2 contract months

## Production Implementation

`ml4t-data` provides futures download managers plus configurable continuous-contract builders:

```python
from ml4t.data import FUTURES_REGISTRY
from ml4t.data.futures import ContinuousContractBuilder, FuturesDataManager

manager = FuturesDataManager.from_config("configs/ml4t_futures.yaml")
futures = manager.load_ohlcv("ES")
continuous = ContinuousContractBuilder().build("ES", data_source="databento")

# Access roll specifications
es_spec = FUTURES_REGISTRY["ES"]  # Roll days, expiry rules, margin
```

## Checklist

- [ ] Roll method chosen and documented (Panama for most uses)
- [ ] All prior history back-adjusted at each roll
- [ ] Returns across roll dates verified (no artificial jumps)
- [ ] Multiple contract months available for carry signals
- [ ] Roll dates sourced from exchange calendar, not hardcoded
