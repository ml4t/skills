---
name: ml4t-validate-data
description: Systematic data quality validation before modeling. Use when ingesting new data or before any model training run.
dependencies: [fetch-data]
metadata:
  book_chapters: "2, 3"
  library: "ml4t-data"
---

# Validate Data

Unvalidated data silently corrupts models — a single unadjusted stock split can make a momentum signal look 10x stronger than reality.

## The Problem

Financial data arrives with missing values, duplicate timestamps, unadjusted corporate actions, stale prices, and impossible OHLC relationships. Using raw data without checks means your model trains on artifacts. A 50% overnight return that is actually a 2:1 split will dominate any feature that touches price changes. You will not see this in your loss function — the model happily fits the noise.

## The Pattern

### WRONG
```python
import polars as pl

# Trust the data, start modeling immediately
df = pl.read_parquet("prices.parquet")
features = df.with_columns(ret=pl.col("close").pct_change())
model.fit(features)  # Trained on splits, gaps, duplicates
```

### CORRECT
```python
import polars as pl

def validate_ohlcv(df: pl.DataFrame) -> dict[str, int]:
    """Run standard OHLCV quality checks. Returns issue counts."""
    issues = {}

    # OHLC consistency: high >= low, close within [low, high]
    issues["high_lt_low"] = df.filter(pl.col("high") < pl.col("low")).height
    issues["close_outside_hl"] = df.filter(
        (pl.col("close") > pl.col("high")) | (pl.col("close") < pl.col("low"))
    ).height

    # Missing data
    issues["null_close"] = df["close"].null_count()
    issues["zero_volume"] = df.filter(pl.col("volume") == 0).height

    # Extreme returns (likely unadjusted splits)
    rets = df.sort("symbol", "timestamp").with_columns(
        pl.col("close").pct_change().over("symbol").alias("ret")
    )
    issues["extreme_returns"] = rets.filter(pl.col("ret").abs() > 0.5).height

    # Duplicate timestamps
    issues["duplicates"] = (
        df.group_by("symbol", "timestamp").len()
        .filter(pl.col("len") > 1).height
    )

    # Stale prices (5+ identical closes in a row)
    stale = df.sort("symbol", "timestamp").with_columns(
        (pl.col("close") == pl.col("close").shift(1)).over("symbol").alias("same")
    )
    issues["stale_5d"] = stale.filter(
        pl.col("same").rolling_sum(5).over("symbol") >= 5
    ).height

    # Report
    for check, count in issues.items():
        if count > 0:
            print(f"  FAIL: {check} = {count}")
    return issues

df = pl.read_parquet("prices.parquet")
issues = validate_ohlcv(df)
assert issues["high_lt_low"] == 0, "OHLC consistency violated"
assert issues["duplicates"] == 0, "Duplicate timestamps found"
```

## Corporate Action Detection

Flag likely unadjusted splits: overnight return >40% with no corresponding volume spike. Filter for `abs(ret) > 0.4` AND `volume / rolling_mean(volume, 20) < 3.0` — real moves come with volume, splits do not.

## Guardrails

- Run validation before every model training, not just at initial load
- Extreme returns (>50%) are almost always data errors, not real moves
- Zero-volume days may be valid (halts) or errors — check per-exchange rules
- Stale prices for 5+ consecutive days indicate a dead feed, not a flat market
- Timestamps must be timezone-aware — naive datetimes cause silent alignment errors

## Production Implementation

`ml4t-data` includes built-in validation at load time:

```python
from ml4t.data import DataManager

dm = DataManager()
df = dm.load("etfs", validate=True)  # Runs all checks, raises on critical failures
```

## Checklist

- [ ] OHLC consistency verified (high >= low, close within range)
- [ ] Missing values counted and below threshold
- [ ] Duplicate timestamps removed
- [ ] Extreme returns flagged and cross-referenced with corporate actions
- [ ] Stale prices detected
- [ ] Timestamps are timezone-aware
