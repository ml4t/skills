---
name: ml4t-feature-families
description: Five families of financial features — momentum, mean-reversion, volatility, carry, and value — each capturing different market dynamics. Use when designing a diversified feature set for alpha models.
dependencies: []
metadata:
  book_chapters: "8"
  library: "ml4t-engineer"
---

# Feature Families

A model trained on six momentum variants learns one signal six ways. Diversifying across feature families — each driven by a different economic mechanism — produces more robust predictions.

## The Problem

Feature sets dominated by a single family (e.g., all momentum) are highly correlated internally. The model wastes capacity learning redundant information and becomes fragile when that one mechanism stops working. A momentum crash wipes out all signal simultaneously.

## The Pattern

### WRONG
```python
import polars as pl

# All momentum variants — same family, correlated, fragile
features = df.with_columns(
    mom_5d=pl.col("close").pct_change(5).over("symbol"),
    mom_21d=pl.col("close").pct_change(21).over("symbol"),
    mom_63d=pl.col("close").pct_change(63).over("symbol"),
    mom_126d=pl.col("close").pct_change(126).over("symbol"),
    mom_252d=pl.col("close").pct_change(252).over("symbol"),
)
```

### CORRECT
```python
import polars as pl
import numpy as np

# One representative from each family — diverse signals
features = df.sort("symbol", "timestamp").with_columns(
    # Momentum: trend-following
    momentum_63d=pl.col("close").pct_change(63).over("symbol"),
    # Mean-reversion: deviation from moving average
    mean_rev_z=(pl.col("close") - pl.col("close").rolling_mean(20).over("symbol"))
    / pl.col("close").rolling_std(20).over("symbol"),
    # Volatility: risk regime
    realized_vol=pl.col("returns").rolling_std(21).over("symbol") * np.sqrt(252),
    # Carry: yield/cost signal (example: dividend yield or funding rate)
    carry_proxy=pl.col("dividend_yield"),
    # Value: fundamental anchor
    pe_ratio=pl.col("pe_ratio"),
)
```

## The Five Families

| Family | Mechanism | Typical Horizon | Example Features |
|--------|-----------|-----------------|------------------|
| Momentum | Trend continuation | 1-12 months | Price return, risk-adjusted return, MACD |
| Mean-reversion | Overreaction snap-back | 1-5 days | RSI, z-score vs MA, Bollinger %B |
| Volatility | Risk regime | 5-60 days | Realized vol, GARCH forecast, VIX ratio |
| Carry | Yield differential | Ongoing | Dividend yield, funding rate, roll yield |
| Value | Fundamental anchor | Months-years | P/E, P/B, EV/EBITDA |

## Diversity Diagnostic

```python
# Check inter-family correlation — should be low
corr = features.select(feature_cols).to_pandas().corr()
avg_cross_family = corr.abs().mean().mean()  # Target: < 0.3
```

## Guardrails

- **Max 2-3 features per family** in initial models — add more only if IC justifies it
- **Cross-family correlation < 0.3** on average — higher means redundancy
- **Each feature needs an economic hypothesis** — if you cannot explain *why* it predicts, it may be noise
- **Not all families apply to all assets**: carry is irrelevant for assets without yield

## Production Implementation

`ml4t-engineer` provides a catalog of 120+ features organized by family:

```python
from ml4t.engineer.api import compute_features
from ml4t.engineer.core.registry import feature_catalog

# Browse by family
feature_catalog.list_features(family="momentum")
feature_catalog.list_features(family="volatility")

# Compute a diversified set
features = compute_features(data, [
    "momentum_63d", "rsi_14", "realized_vol_21d", "roll_yield",
])
```

## Checklist

- [ ] Features span at least 3 of the 5 families
- [ ] No single family contributes more than 40% of total features
- [ ] Cross-family correlation checked (target < 0.3)
- [ ] Each feature has a stated economic hypothesis
- [ ] Family coverage documented in feature config
