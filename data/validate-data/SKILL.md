---
name: ml4t-validate-data
description: Quality checks for financial data before modeling
category: data
type: operational
dependencies: [fetch-data]
book_chapters: [3, 5]
---

# Validate Data

Data quality issues corrupt models silently. Validate before use.

## Core Checks

| Check | Method | Threshold |
|-------|--------|-----------|
| Missing values | `isna().sum()` | < 5% per column |
| Zero volume | `volume == 0` | Flag, don't use |
| Price jumps | `abs(ret) > 0.5` | Review manually |
| Stale prices | `close == close.shift(n)` | n < 5 consecutive |
| Negative prices | `price < 0` | Should be 0 |

## Validation Pipeline

```python
def validate_ohlcv(df: pl.DataFrame) -> dict:
    """Run standard OHLCV quality checks."""
    issues = {}

    # OHLC consistency
    issues['high_lt_low'] = (df['high'] < df['low']).sum()
    issues['close_outside'] = (
        (df['close'] > df['high']) | (df['close'] < df['low'])
    ).sum()

    # Missing data
    issues['null_close'] = df['close'].null_count()
    issues['zero_volume'] = (df['volume'] == 0).sum()

    # Extreme returns
    rets = df['close'].pct_change()
    issues['extreme_returns'] = (rets.abs() > 0.5).sum()

    return issues
```

## Corporate Actions

```python
# Check for unadjusted splits
splits = df.filter(
    (pl.col('close') / pl.col('close').shift(1) - 1).abs() > 0.4
)
# Cross-reference with split calendar
```

## Timestamp Checks

```python
# Verify timezone consistency
assert df['timestamp'].dt.time_zone == 'America/New_York'

# Check for duplicates
dupes = df.group_by(['symbol', 'date']).count().filter(pl.col('count') > 1)

# Verify trading days only
trading_days = get_trading_calendar('NYSE').sessions
```

## Guardrails

- Always validate before modeling
- Log validation results, don't just fail silently
- Price jumps often indicate unadjusted splits
- Zero volume days may be valid (halts) or errors

## Checklist

- [ ] OHLC consistency verified
- [ ] Missing values counted and handled
- [ ] Extreme returns flagged and reviewed
- [ ] Timestamps timezone-aware
- [ ] Corporate actions adjusted
- [ ] Duplicates removed
