---
name: ml4t-compute-features
description: "Systematic feature computation across multiple assets with group-aware operations. Use when computing technical or fundamental features for a panel of securities."
when_to_use: "Use when engineering features for a cross-sectional panel of symbols"
dependencies: [lookahead-bias]
metadata:
  book_chapters: "8"
  library: "ml4t-engineer"
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
---
# Compute Features

Computing features across a panel of assets requires group-aware operations - a global rolling mean mixes Apple's history with Tesla's. Every windowed statistic must be computed per symbol.

## The Problem

Features computed with global statistics bleed information across assets. A z-score computed over the full dataframe uses one symbol's volatility to normalize another. Worse, using `.mean()` on the full column leaks future data from late-arriving symbols into early rows.

## The Pattern

### WRONG
```python
import polars as pl

# Global statistics mix symbols and leak future
df = df.with_columns(
    mom_zscore=(pl.col("returns") - pl.col("returns").mean())
    / pl.col("returns").std()
)
```

### CORRECT
```python
import polars as pl

# Per-symbol rolling window - no cross-contamination, no lookahead
df = df.sort("symbol", "timestamp").with_columns(
    mom_zscore=(
        (pl.col("returns") - pl.col("returns").rolling_mean(504).shift(1))  # 504 ≈ 2 trading years
        / pl.col("returns").rolling_std(504).shift(1)
    ).over("symbol")
)
```

## Windowed Aggregations

Three window types, each with different use cases:

```python
# Rolling: fixed lookback, discards old data
pl.col("close").pct_change(21).over("symbol")              # 21-day momentum

# Long-horizon rolling: large window approximates expanding
pl.col("returns").rolling_mean(504).shift(1).over("symbol")   # 504 days ≈ 2 trading years

# Cross-sectional: rank across all symbols at each timestamp
pl.col("momentum").rank().over("timestamp")                 # Peer rank
```

Always `.shift(1)` expanding/rolling statistics to avoid using the current bar's value in its own feature.

## Multi-Feature Computation

```python
features = df.sort("symbol", "timestamp").with_columns(
    momentum_21d=pl.col("close").pct_change(21).over("symbol"),
    volatility_21d=pl.col("returns").rolling_std(21).over("symbol"),
    volume_ratio=pl.col("volume")
    / pl.col("volume").rolling_mean(21).shift(1).over("symbol"),
)
```

## Guardrails

- **Every `.over("symbol")`**: any rolling/expanding stat without `.over("symbol")` on panel data is a bug
- **Shift before use**: expanding stats need `.shift(1)` to avoid including the current observation
- **Sort order matters**: always `sort("symbol", "timestamp")` before windowed operations
- **Horizon alignment**: feature lookback should match label horizon - a 63-day momentum feature on a 5-day label captures noise, not signal

## Production Implementation

`ml4t-engineer` provides config-driven computation with dependency resolution for
single-series or per-symbol feature pipelines. For cross-sectional panels, keep
the explicit grouped Polars logic from this skill and apply registry features
per symbol rather than assuming automatic panel partitioning.

```python
from ml4t.engineer import compute_features, feature_catalog

# Discover available features
print(feature_catalog.list())

# Per-asset registry features
spy_features = compute_features(spy_prices, ["rsi", "macd", "bollinger_bands"])

# YAML configs are also supported
feature_specs = compute_features(spy_prices, "config/features.yaml")
```

## Checklist

- [ ] All windowed features use `.over("symbol")` for panel data
- [ ] Expanding/rolling stats are `.shift(1)` before use
- [ ] Data is sorted by `("symbol", "timestamp")` before feature computation
- [ ] No global `.mean()` / `.std()` on panel columns
- [ ] Cross-sectional features use `.over("timestamp")`
