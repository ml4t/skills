---
name: ml4t-data-leakage
description: Prevent all forms of information leakage in ML pipelines
category: concepts
type: conceptual
dependencies: [lookahead-bias]
book_chapters: [2, 7, 10]
---

# Data Leakage

## Types

1. **Lookahead bias**: Using future data (see `ml4t-lookahead-bias`)
2. **Target leakage**: Features derived from target
3. **Train-test contamination**: Test info in training transforms
4. **CV leakage**: Standard k-fold on time series
5. **Survivorship bias**: Current universe for historical backtest

## Rules

### Transformations
```python
# WRONG
scaler.fit_transform(X_all)

# CORRECT
scaler.fit(X_train)
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

### Cross-Validation
```python
# WRONG
KFold(n_splits=5, shuffle=True)

# CORRECT
from ml4t.diagnostic.splitters import CombinatorialPurgedCV
CombinatorialPurgedCV(n_groups=8, n_test_groups=2, label_horizon=5)
```

### Statistics
```python
# WRONG - uses all data
threshold = df['returns'].quantile(0.75)

# CORRECT - expanding window
threshold = df['returns'].expanding().quantile(0.75).shift(1)
```

## Detection

Red flags:
- Sharpe > 2.0 on daily data
- Accuracy > 55% for return prediction
- Feature-target correlation > 0.8
- In-sample ≈ out-of-sample performance

## Checklist

- [ ] All fit() calls on training data only
- [ ] Time-series aware CV with purging
- [ ] Point-in-time data correctness
- [ ] No future statistics in features/labels
