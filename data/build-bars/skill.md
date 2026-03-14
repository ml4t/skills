---
name: ml4t-build-bars
description: Construct time, tick, volume, and dollar bars from trades
category: data
type: operational
dependencies: [fetch-data]
book_chapters: [4]
---

# Build Bars

Alternative bar types sample by activity rather than time.

## Bar Types

| Type | Sample On | Benefit |
|------|-----------|---------|
| Time | Fixed interval | Simple, universal |
| Tick | N trades | Activity-based |
| Volume | N shares | Liquidity-normalized |
| Dollar | $N traded | Most consistent |

## API

```python
from ml4t.data.bars import build_bars

# Time bars (default)
time_bars = build_bars(
    trades,
    bar_type='time',
    frequency='5min'
)

# Dollar bars (~constant information per bar)
dollar_bars = build_bars(
    trades,
    bar_type='dollar',
    threshold=1_000_000  # $1M per bar
)

# Volume bars
volume_bars = build_bars(
    trades,
    bar_type='volume',
    threshold=10_000  # 10K shares per bar
)
```

## Why Dollar Bars

```python
# Time bars: uneven information per bar
#   - High volume: bar has much information
#   - Low volume: bar has little information

# Dollar bars: roughly equal information per bar
#   - Always ~$1M traded
#   - More bars when active, fewer when quiet
#   - Returns closer to normal distribution
```

## Implementation

```python
def build_dollar_bars(trades: pl.DataFrame, threshold: float) -> pl.DataFrame:
    """Build dollar bars from tick data."""
    trades = trades.with_columns([
        (pl.col('price') * pl.col('size')).alias('dollar_volume'),
        (pl.col('price') * pl.col('size')).cum_sum().alias('cumsum')
    ])

    # Assign bar index based on cumulative dollar volume
    trades = trades.with_columns(
        (pl.col('cumsum') // threshold).alias('bar_idx')
    )

    # Aggregate to bars
    return trades.group_by('bar_idx').agg([
        pl.col('timestamp').first().alias('open_time'),
        pl.col('price').first().alias('open'),
        pl.col('price').max().alias('high'),
        pl.col('price').min().alias('low'),
        pl.col('price').last().alias('close'),
        pl.col('size').sum().alias('volume'),
        pl.col('dollar_volume').sum().alias('dollar_volume')
    ])
```

## Guardrails

- Dollar bars need tick data (not OHLCV)
- Threshold should yield similar bar count to time bars
- Volume/dollar bars not directly comparable across symbols
- Use dollar-normalized metrics for cross-sectional

## Checklist

- [ ] Tick data available and clean
- [ ] Threshold calibrated (~same bar count as time)
- [ ] Bars include OHLCV and dollar volume
- [ ] Time zones handled correctly
