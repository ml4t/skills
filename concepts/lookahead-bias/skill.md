---
name: ml4t-lookahead-bias
description: Detect and prevent using future information in features/labels
category: concepts
type: conceptual
dependencies: []
book_chapters: [6, 7, 10]
---

# Lookahead Bias

Most common ML4T failure. Model uses future info → great backtest → fails live.

## Common Sources

1. **Normalization with full sample**
2. **Settlement prices for intraday signals**
3. **Labels using future statistics**
4. **Standard k-fold CV on time series**
5. **Feature selection on full dataset**

## Rules

### Normalization
```python
# WRONG
df['feat'] = (df['feat'] - df['feat'].mean()) / df['feat'].std()

# CORRECT
df['feat'] = (
    (df['feat'] - df['feat'].expanding().mean().shift(1)) /
    df['feat'].expanding().std().shift(1)
)
```

### Label Thresholds
```python
# WRONG - global threshold
threshold = returns.quantile(0.75)
y = (forward_returns > threshold).astype(int)

# CORRECT - expanding threshold
threshold = returns.expanding().quantile(0.75).shift(1)
y = (forward_returns > threshold).astype(int)
```

### Cross-Validation
```python
# WRONG
KFold(n_splits=5, shuffle=True)

# CORRECT
CombinatorialPurgedCV(n_groups=8, n_test_groups=2, label_horizon=5, embargo_size=2)
```

## Detection

- Sharpe > 2 on daily data → investigate
- Out-of-sample matches in-sample exactly
- Feature values change when recomputed with more data

## Checklist

- [ ] All statistics use expanding().shift(1)
- [ ] fit_transform() only on training data
- [ ] Time-series CV with purging/embargo
- [ ] Labels don't use future thresholds
