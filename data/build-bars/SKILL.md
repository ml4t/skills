---
name: ml4t-build-bars
description: "Aggregate tick data into time, volume, and dollar bars. Use when resampling raw tick data into regular or information-driven bars."
when_to_use: "Use when working with trade-level data and need OHLCV bars with uniform information content"
dependencies: [fetch-data]
metadata:
  book_chapters: "3"
  library: ""
paths: ["**/*data*.py", "**/*fetch*.py", "**/*bars*.py", "**/*universe*.py", "**/*calendar*.py", "**/*futures*.py", "**/*export*.py", "**/*synthetic*.py"]
---
# Build Bars

Time bars sample by the clock, producing bars with wildly different information content — a 5-minute bar during the open contains 100x more trades than one at 2pm.

## The Problem

Standard time bars (1-min, 5-min, daily) sample at fixed intervals regardless of market activity. During high-volume periods, a single bar compresses thousands of trades; during quiet periods, a bar may contain just a handful. This creates heteroscedastic returns that violate the i.i.d. assumptions of most ML models. Volume and dollar bars sample by activity instead, producing bars with roughly equal information content and returns closer to normality.

## The Pattern

### WRONG
```python
import polars as pl

# Only using time bars — uneven information per bar
trades = pl.read_parquet("trades.parquet")
bars_5min = (
    trades.group_by_dynamic("timestamp", every="5m")
    .agg(
        open=pl.col("price").first(),
        high=pl.col("price").max(),
        low=pl.col("price").min(),
        close=pl.col("price").last(),
        volume=pl.col("size").sum(),
    )
)
# Bar at 9:30 has 5000 trades, bar at 14:00 has 50 trades
```

### CORRECT
```python
import polars as pl

def build_dollar_bars(trades: pl.DataFrame, threshold: float) -> pl.DataFrame:
    """Build dollar bars: each bar contains ~threshold dollars traded."""
    bars = (
        trades
        .sort("timestamp")
        .with_columns(
            dollar_vol=(pl.col("price") * pl.col("size")),
        )
        .with_columns(
            cum_dollar=pl.col("dollar_vol").cum_sum(),
        )
        .with_columns(
            bar_idx=(pl.col("cum_dollar") // threshold).cast(pl.Int64),
        )
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
    return bars

# Threshold: target ~same number of bars as time bars over the day
bars = build_dollar_bars(trades, threshold=1_000_000)  # $1M per bar
```

## Choosing the Threshold

Calibrate so dollar bars produce roughly the same number of bars as time bars over the same period.

```python
# Estimate: total dollar volume / desired number of bars
total_dollar_vol = (trades["price"] * trades["size"]).sum()
n_time_bars = 78  # 6.5 hours * 12 five-minute bars
threshold = total_dollar_vol / n_time_bars
```

## Bar Type Comparison

| Type | Samples On | Information Per Bar | Returns Distribution |
|------|-----------|-------------------|---------------------|
| Time | Clock interval | Uneven | Fat-tailed, heteroscedastic |
| Tick | N trades | More uniform | Closer to normal |
| Volume | N shares | Uniform for single stock | Good for single-name |
| Dollar | $N traded | Most uniform | Closest to normal |

Dollar bars are preferred because they normalize for both price level and activity.

## Guardrails

- Dollar bars require tick-level trade data (timestamp, price, size) — cannot build from OHLCV
- Thresholds are symbol-specific: $1M/bar for AAPL vs $50K/bar for a small-cap
- Volume and dollar bars are not directly comparable across symbols — normalize returns
- Overnight gaps should be handled (exclude or flag the first bar of each session)
- Bar counts drop on quiet days, increase on volatile days — this is the intended behavior

## Checklist

- [ ] Tick data available with timestamp, price, and size columns
- [ ] Threshold calibrated to produce reasonable bar count (~same as time bars)
- [ ] Bars include OHLCV, dollar volume, and trade count
- [ ] Overnight/session boundaries handled
- [ ] Returns closer to normal verified (Jarque-Bera test or QQ plot)
