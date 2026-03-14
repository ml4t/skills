---
name: ml4t-walk-forward-cv
description: Time-series cross-validation preserving temporal order
category: validation
type: operational
dependencies: [purging-embargo]
book_chapters: [9, 12]
quantlab_module: ml4t.diagnostic.splitters
---

# Walk-Forward Cross-Validation

Temporal CV that respects time-series structure.

## Variants

| Type | Train Window | Test Window |
|------|--------------|-------------|
| Expanding | Grows | Fixed |
| Rolling | Fixed | Fixed |
| Anchored | Fixed start | Slides |

## API

```python
from sklearn.model_selection import TimeSeriesSplit
from ml4t.diagnostic.splitters import PurgedTimeSeriesSplit

# Basic walk-forward
tscv = TimeSeriesSplit(n_splits=5)

# With purging (recommended)
wf_cv = PurgedTimeSeriesSplit(
    n_splits=5,
    purge_gap=5,       # Days between train/test
    embargo_pct=0.01   # % of test to skip at start
)

for train_idx, test_idx in wf_cv.split(X):
    model.fit(X[train_idx], y[train_idx])
    pred = model.predict(X[test_idx])
```

## Expanding vs Rolling

```python
# Expanding: more data, slower adaptation
#   [----train----][test]
#   [-------train-------][test]
#   [----------train----------][test]

# Rolling: fixed data, faster adaptation
#   [----train----][test]
#        [----train----][test]
#             [----train----][test]
```

## Fold Structure

```python
def visualize_folds(splits, n_samples):
    """Visualize train/test splits."""
    for i, (train, test) in enumerate(splits):
        train_pct = len(train) / n_samples * 100
        test_pct = len(test) / n_samples * 100
        gap_start = train[-1] + 1
        gap_end = test[0] - 1
        print(f"Fold {i}: Train {train_pct:.0f}%, Test {test_pct:.0f}%, "
              f"Gap: {gap_end - gap_start + 1} samples")
```

## Rules

```python
# WRONG: Shuffle time series
cv = KFold(n_splits=5, shuffle=True)  # Leakage!

# WRONG: No gap between train and test
cv = TimeSeriesSplit(n_splits=5)  # No purging

# CORRECT: Purged walk-forward
cv = PurgedTimeSeriesSplit(n_splits=5, purge_gap=horizon)
```

## Guardrails

- Never shuffle time-series data
- Purge gap >= prediction horizon
- Test sets should span different market conditions
- More splits = more variance in estimates

## Checklist

- [ ] Temporal order preserved
- [ ] Purge gap >= label horizon
- [ ] Embargo applied
- [ ] Multiple market regimes in test sets
