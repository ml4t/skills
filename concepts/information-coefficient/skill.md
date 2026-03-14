---
name: ml4t-information-coefficient
description: Measure predictive power of signals with IC and Rank IC
category: concepts
type: conceptual
dependencies: []
book_chapters: [9, 16]
quantlab_module: ml4t.diagnostic.metrics
---

# Information Coefficient

Correlation between predicted and realized values, the primary signal quality metric.

## Definitions

| Metric | Formula | Use Case |
|--------|---------|----------|
| IC | pearson(forecast, actual) | Linear relationships |
| Rank IC | spearman(forecast, actual) | Cross-sectional ranking |
| IC_IR | mean(IC) / std(IC) | Signal consistency |

## Interpretation

| IC | Quality | Notes |
|----|---------|-------|
| > 0.10 | Excellent | Rare, verify not overfit |
| 0.05-0.10 | Good | Typical for strong factors |
| 0.02-0.05 | Moderate | Usable with enough bets |
| < 0.02 | Weak | Needs high capacity |

## API

```python
from ml4t.diagnostic.metrics import information_coefficient

# Cross-sectional IC (per period)
ic_series = information_coefficient(
    predictions=signal,      # (time, assets)
    returns=forward_returns, # (time, assets)
    method='spearman'        # or 'pearson'
)

# Aggregate statistics
ic_mean = ic_series.mean()
ic_std = ic_series.std()
ic_ir = ic_mean / ic_std
```

## Fundamental Law

```python
# IR ≈ IC * sqrt(BR)
# IR = Information Ratio (Sharpe of active returns)
# IC = Information Coefficient
# BR = Breadth (number of independent bets)

# Implication: Low IC can work with high breadth
ic = 0.02
breadth = 500  # stocks per rebalance * rebalances per year
expected_ir = ic * np.sqrt(breadth)  # ≈ 0.45
```

## Rules

```python
# WRONG: Report single-period IC
best_ic = ic_series.max()

# CORRECT: Report IC statistics with HAC adjustment
from scipy.stats import ttest_1samp
t_stat, p_val = ttest_1samp(ic_series, 0)
# Use Newey-West for autocorrelation
```

## Guardrails

- Always use Rank IC for cross-sectional signals
- Report IC_IR, not just mean IC
- Use HAC standard errors for significance
- Decay analysis: plot IC by horizon

## Checklist

- [ ] IC calculated per period (not pooled)
- [ ] Rank IC used for cross-sectional
- [ ] IC_IR reported (mean/std)
- [ ] Statistical significance with HAC
- [ ] IC decay by horizon analyzed
