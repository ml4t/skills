---
name: ml4t-non-stationarity
description: Handle changing statistical properties in financial time series
category: concepts
type: conceptual
dependencies: [regime-awareness]
book_chapters: [6, 9, 15]
---

# Non-Stationarity

Financial time series have statistical properties that change over time.

## The Problem

```python
# WRONG: Assume constant parameters
model.fit(train_data['2010':'2020'])  # Bull market
model.predict(test_data['2022'])       # Different regime
```

## Types

| Type | Description | Example |
|------|-------------|---------|
| Mean shift | Average changes | Post-2008 low rates |
| Variance shift | Volatility changes | VIX spikes |
| Structural break | Relationship changes | Factor decay |
| Seasonality | Periodic patterns | January effect decay |

## Detection

```python
from statsmodels.tsa.stattools import adfuller, kpss

# ADF test: H0 = unit root (non-stationary)
adf_stat, adf_pval, *_ = adfuller(series)
stationary_adf = adf_pval < 0.05

# KPSS test: H0 = stationary
kpss_stat, kpss_pval, *_ = kpss(series)
stationary_kpss = kpss_pval > 0.05

# Best: both tests agree
```

## Mitigation

| Approach | When |
|----------|------|
| Differencing | Remove trend |
| Rolling normalization | Adjust for scale |
| Regime conditioning | Split by state |
| Expanding window | More data, slower adapt |
| Shrinking window | Less data, faster adapt |

## Rules

```python
# WRONG: Global normalization
X = (X - X.mean()) / X.std()

# CORRECT: Expanding window (no lookahead)
X = (X - X.expanding().mean()) / X.expanding().std()

# CORRECT: Rolling window with fixed lookback
X = (X - X.rolling(252).mean()) / X.rolling(252).std()
```

## Guardrails

- Always test stationarity before modeling
- Use expanding/rolling statistics (not global)
- Monitor for structural breaks in production
- Shorter windows adapt faster but have more variance

## Checklist

- [ ] Stationarity tests run (ADF + KPSS)
- [ ] Rolling normalization used
- [ ] No global statistics in features
- [ ] Regime conditioning considered
