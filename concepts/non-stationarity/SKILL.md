---
name: ml4t-non-stationarity
description: Handle changing statistical properties in financial time series. Use when normalizing features, selecting lookback windows, or diagnosing model decay.
dependencies: [regime-awareness]
metadata:
  book_chapters: "6, 9"
  library: "ml4t-diagnostic"
---

# Non-Stationarity

Financial time series have means, variances, and correlations that change over time. A model trained on 2015--2019 low-volatility data will underperform in a 2020 regime shift if it assumes fixed parameters.

## The Problem

Global normalization (subtracting the full-sample mean and dividing by the full-sample standard deviation) embeds future information into every observation. It also assumes the distribution is stable, which is false for financial data. Post-2008 interest rates, COVID volatility, and factor decay are all examples of structural shifts that invalidate fixed-parameter assumptions.

A model trained on globally normalized features will overfit to the training regime and degrade when the regime changes.

## The Pattern

### WRONG

```python
import numpy as np

# Global normalization: uses future data and assumes stationarity
X_norm = (X - X.mean(axis=0)) / X.std(axis=0)
```

### CORRECT

```python
import polars as pl

# Expanding normalization: only uses past data, adapts to changing distribution
features = pl.DataFrame({"feat": feat_values, "timestamp": dates})

features = features.with_columns(
    feat_norm=(
        (pl.col("feat") - pl.col("feat").shift(1).cum_mean())
        / pl.col("feat").shift(1).rolling_std(window_size=252)
    )
)
```

## Detection: ADF + KPSS Together

Run both tests. They have opposite null hypotheses, so agreement is strong evidence:

```python
from statsmodels.tsa.stattools import adfuller, kpss

adf_stat, adf_pval, *_ = adfuller(series)
kpss_stat, kpss_pval, *_ = kpss(series, regression="c")

stationary = (adf_pval < 0.05) and (kpss_pval > 0.05)  # both agree
```

| ADF rejects? | KPSS rejects? | Conclusion |
|--------------|---------------|------------|
| Yes | No | Stationary |
| No | Yes | Non-stationary |
| Yes | Yes | Trend-stationary (difference first) |
| No | No | Inconclusive (get more data) |

## Mitigation Strategies

| Approach | When to use | Trade-off |
|----------|-------------|-----------|
| Expanding window | Default safe choice | Slow to adapt, no lookahead |
| Rolling window (e.g., 252d) | Faster adaptation needed | More variance, loses early data |
| First differencing | Remove trend/unit root | Loses level information |
| Regime conditioning | Known structural breaks | Requires regime labels |

## Guardrails

- `X.mean()` or `X.std()` without `.expanding()` or `.rolling()` is a red flag in any feature pipeline.
- Shorter rolling windows adapt faster but have higher estimation variance -- 126d to 504d is the typical range.
- Test stationarity on raw features before modeling; non-stationary inputs produce unstable coefficients.
- Monitor feature distributions in production -- a mean shift > 2 sigma signals model retraining.

## Production Implementation

`ml4t-diagnostic` provides stationarity testing utilities:

```python
from ml4t.diagnostic.evaluation.stationarity import analyze_stationarity

stationarity = analyze_stationarity(feature_series, include_tests=["adf", "kpss"])
print(stationarity.consensus)
print(stationarity.summary_df)
```

## Checklist

- [ ] Stationarity tests (ADF + KPSS) run on all features before modeling
- [ ] Normalization uses expanding or rolling window, never global statistics
- [ ] Rolling window length chosen deliberately (not default)
- [ ] Feature distributions monitored for structural breaks in production
- [ ] Non-stationary series differenced or transformed before use
