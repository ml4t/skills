---
name: ml4t-regime-features
description: Features that capture market regime — volatility state, trend strength, liquidity — used as conditioning variables for ML models. Use when model performance varies across market environments.
dependencies: [lookahead-bias]
metadata:
  book_chapters: "8, 9"
  library: "ml4t-engineer"
---

# Regime Features

Momentum works in trending markets, mean-reversion in range-bound ones. Instead of manually switching strategies, feed regime indicators as features and let the model learn when each signal works.

## The Problem

Models trained on pooled data learn average relationships. If momentum has IC of +0.08 in trends and -0.04 in mean-reverting regimes, the pooled IC is near zero. Regime features let the model condition on the current environment rather than averaging across all of them.

## The Pattern

### WRONG
```python
import polars as pl

# Raw VIX level — non-stationary, scale-dependent, model cannot generalize
features = df.with_columns(regime_vix=pl.col("vix"))
```

### CORRECT
```python
import polars as pl

# Percentile-ranked regime indicator — stationary, bounded [0, 1]
features = df.sort("timestamp").with_columns(
    regime_vix_pctl=pl.col("vix")
    .expanding()
    .rank()
    .shift(1)
    / pl.col("vix").expanding().count().shift(1),
    regime_vol_zscore=(
        pl.col("realized_vol") - pl.col("realized_vol").rolling_mean(252).shift(1)
    )
    / pl.col("realized_vol").rolling_std(252).shift(1),
)
```

## Regime Indicator Catalog

| Indicator | Captures | Computation |
|-----------|----------|-------------|
| VIX percentile | Fear vs complacency | Expanding rank of VIX |
| Realized vol z-score | Current turbulence vs history | Rolling z-score of 21d vol |
| ADX level | Trend strength | 14-period ADX (0-100 scale) |
| Yield curve slope | Growth expectations | 10Y - 2Y treasury rate |
| Average correlation | Diversification regime | Rolling pairwise correlation |
| Credit spread | Risk appetite | HY - IG spread |

## Building Regime Features

```python
import polars as pl
import numpy as np

df = df.sort("timestamp").with_columns(
    # Trend strength (ADX-inspired: ratio of directional move to range)
    trend_strength=(
        pl.col("close").pct_change(21).abs()
        / (pl.col("close").rolling_std(21) * np.sqrt(21))
    ),
    # Correlation regime (requires panel data)
    avg_corr=pl.col("returns").rolling_corr(pl.col("market_returns"), window=63),
)
```

## Guardrails

- **Always use lagged values** — `.shift(1)` on all expanding/rolling regime stats
- **Rank or z-score** raw indicators — VIX at 20 means different things in 2017 vs 2020
- **Multiple indicators** — no single regime variable captures the full environment
- **HMM regimes have lookahead risk** — fit HMM walk-forward only, never on the full sample

## Production Implementation

`ml4t-engineer` includes regime features in its catalog:

```python
from ml4t.engineer import compute_features

features = compute_features(data, [
    "adx",
    "choppiness_index",
    "volatility_percentile_rank",
    "volatility_regime_probability",
])
```

Macro regime inputs like VIX term structure or yield-curve slope still need to
be sourced separately and joined in as external features.

## Checklist

- [ ] Regime features are stationary (percentile-ranked or z-scored)
- [ ] All use `.shift(1)` — no current-bar value in its own feature
- [ ] At least 2-3 independent regime indicators included
- [ ] Features are inputs to the model, not if/else trading rules
- [ ] HMM or changepoint models (if used) fitted walk-forward only
