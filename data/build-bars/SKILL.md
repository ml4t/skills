---
name: ml4t-build-bars
description: "Aggregate tick data into time, volume, and dollar bars. Use when resampling raw tick data into regular or information-driven bars."
when_to_use: "Use when working with trade-level data and need OHLCV bars with uniform information content"
dependencies: [fetch-data]
metadata:
  book_chapters: "3"
  library: "ml4t-engineer"
paths: ["**/*data*.py", "**/*fetch*.py", "**/*bars*.py", "**/*universe*.py", "**/*calendar*.py", "**/*futures*.py", "**/*export*.py", "**/*synthetic*.py"]
---
# Build Bars

Time bars sample by the clock, producing bars with wildly different information content - a 5-minute bar during the open contains 100x more trades than one at 2pm.

## The Problem

Standard time bars (1-min, 5-min, daily) sample at fixed intervals regardless of market activity. During high-volume periods, a single bar compresses thousands of trades; during quiet periods, a bar may contain just a handful. This creates heteroscedastic returns that violate the i.i.d. assumptions of most ML models. Volume and dollar bars sample by activity instead, producing bars with roughly equal information content and returns closer to normality.

## The Pattern

### WRONG
```python
import polars as pl

# Only using time bars - uneven information per bar
trades = pl.read_parquet("trades.parquet")
bars_5min = (
    trades.group_by_dynamic("timestamp", every="5m")
    .agg(
        open=pl.col("price").first(),
        close=pl.col("price").last(),
        volume=pl.col("size").sum(),
    )
)
# Bar at 9:30 has 5000 trades, bar at 14:00 has 50 trades
```

### CORRECT
```python
import numpy as np
import polars as pl

def bar_index(dollar_vol: np.ndarray, threshold: float) -> np.ndarray:
    """Bar id per trade: accumulate, close on the crossing, then RESET.

    Bucketing by the running total (cum_dollar // threshold) never resets, so
    an overshooting bar steals from the next: four $800 trades against a
    $1,000 threshold give $1,600, $800, $800, not two $1,600 bars."""
    idx = np.empty(len(dollar_vol), dtype=np.int64)
    bar, run = 0, 0.0
    for i, value in enumerate(dollar_vol):
        idx[i] = bar
        run += value
        if run >= threshold:
            bar, run = bar + 1, 0.0
    return idx

def build_dollar_bars(trades: pl.DataFrame, threshold: float) -> pl.DataFrame:
    """Build dollar bars: each bar contains ~threshold dollars traded."""
    trades = trades.sort("timestamp").with_columns(dollar_vol=pl.col("price") * pl.col("size"))
    return (
        trades
        .with_columns(bar_idx=bar_index(trades["dollar_vol"].to_numpy(), threshold))
        .group_by("bar_idx")
        .agg(
            timestamp=pl.col("timestamp").first(),
            open=pl.col("price").first(),
            high=pl.col("price").max(),
            low=pl.col("price").min(),
            close=pl.col("price").last(),
            volume=pl.col("size").sum(),
            dollar_volume=pl.col("dollar_vol").sum(),
            n_trades=pl.len(),
        )
        .sort("bar_idx")
    )

bars = build_dollar_bars(trades, threshold=1_000_000)  # $1M per bar
```

## Choosing the Threshold

Calibrate the threshold as total dollar volume divided by the desired bar count.

## Bar Type Comparison

| Type | Samples On | Information Per Bar | Returns Distribution |
|------|-----------|-------------------|---------------------|
| Time | Clock interval | Uneven | Fat-tailed, heteroscedastic |
| Tick | N trades | More uniform | Closer to normal |
| Volume | N shares | Uniform for single stock | Good for single-name |
| Dollar | $N traded | Most uniform | Closest to normal |

## Guardrails

- Dollar bars require tick-level trade data (timestamp, price, size) - cannot build from OHLCV
- Thresholds are symbol-specific: $1M/bar for AAPL vs $50K/bar for a small-cap
- Volume and dollar bars are not directly comparable across symbols - normalize returns
- Overnight gaps should be handled (exclude or flag the first bar of each session)

## Production Implementation

`ml4t-engineer` provides vectorized tick, volume, dollar, imbalance, and run-bar samplers:

```python
from ml4t.engineer.bars import DollarBarSampler

bars = DollarBarSampler(dollars_per_bar=1_000_000).sample(trades.rename({"size": "volume"}))
```

Package-level names use vectorized implementations; compatibility implementations retain the
`Original` suffix. Volume and imbalance samplers require a signed `side` column. Instantiate a
concrete sampler with its class-specific threshold keyword, not the abstract `BarSampler`.

## Checklist

- [ ] Tick data available with timestamp, price, and size columns
- [ ] Threshold calibrated to produce reasonable bar count (~same as time bars)
- [ ] Bars include OHLCV, dollar volume, and trade count
- [ ] Returns closer to normal verified (Jarque-Bera test or QQ plot)
