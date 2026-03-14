---
name: ml4t-cpcv
description: Combinatorial Purged Cross-Validation generates a distribution of backtest paths instead of a single estimate. Use when evaluating strategy robustness or detecting overfitting in time-series models.
dependencies: [purging-embargo]
metadata:
  book_chapters: "7"
  library: "ml4t-diagnostic"
---

# Combinatorial Purged Cross-Validation

Standard k-fold CV on time series produces one biased performance estimate. CPCV generates C(N,k) train/test combinations with purging and embargo, yielding a **distribution** of results that reveals overfitting.

## The Problem

A single train/test split gives one Sharpe ratio — you cannot tell if it is skill or luck. Standard k-fold shuffles temporal order, leaking future information. Even `TimeSeriesSplit` produces only a handful of sequential folds, each with different train sizes, making comparison unreliable. You need many unbiased performance samples to build a distribution.

## The Pattern

Partition data into N groups, select k as test sets, train on the rest. Purge samples whose labels overlap the test boundary, add an embargo buffer. Repeat for all C(N,k) combinations.

### WRONG

```python
from sklearn.model_selection import KFold

# Shuffled k-fold on time series — future leaks into training
cv = KFold(n_splits=5, shuffle=True, random_state=42)
scores = []
for train_idx, test_idx in cv.split(X):
    model.fit(X[train_idx], y[train_idx])
    scores.append(model.score(X[test_idx], y[test_idx]))
print(f"Mean score: {np.mean(scores):.3f}")  # Overly optimistic
```

### CORRECT

```python
import numpy as np
from itertools import combinations
from sklearn.model_selection import TimeSeriesSplit

# Manual CPCV with purging using standard tools
n_groups, n_test, horizon, embargo = 8, 2, 5, 2
n_samples = len(X)
group_size = n_samples // n_groups
scores = []

for test_groups in combinations(range(n_groups), n_test):
    test_mask = np.zeros(n_samples, dtype=bool)
    for g in test_groups:
        test_mask[g * group_size:(g + 1) * group_size] = True

    # Purge: remove training samples within horizon of test boundaries
    train_mask = ~test_mask.copy()
    for i in np.where(np.diff(test_mask.astype(int)) != 0)[0]:
        purge_start = max(0, i + 1 - horizon)
        purge_end = min(n_samples, i + 1 + embargo)
        train_mask[purge_start:purge_end] = False

    model.fit(X[train_mask], y[train_mask])
    scores.append(model.score(X[test_mask], y[test_mask]))

# C(8,2) = 28 scores — a distribution, not a single number
print(f"Mean: {np.mean(scores):.3f}, Std: {np.std(scores):.3f}")
```

## Parameter Selection

| n_groups | n_test_groups | Combinations | Use case |
|----------|---------------|--------------|----------|
| 6 | 2 | 15 | Small datasets |
| 8 | 2 | 28 | Standard |
| 10 | 3 | 120 | Deep analysis |

- `label_horizon`: must match label construction (5-day returns = 5)
- `embargo_size`: ~10-20% of label_horizon

## Guardrails

- High variance across folds signals lack of robustness — report std alongside mean
- Verify training set size after purging is still sufficient (>60% of data)
- Combine with Deflated Sharpe Ratio (see `deflated-sharpe` skill) for statistical significance
- Never report the best fold — report the full distribution

## Production Implementation

`ml4t-diagnostic` provides a validated, sklearn-compatible splitter:

```python
from ml4t.diagnostic.splitters import CombinatorialCV

cv = CombinatorialCV(
    n_groups=8,
    n_test_groups=2,
    label_horizon=5,
    embargo_size=2,
    max_combinations=28,
    random_state=42,
)
for train_idx, test_idx in cv.split(X):
    model.fit(X[train_idx], y[train_idx])
    scores.append(model.score(X[test_idx], y[test_idx]))
```

## Checklist

- [ ] Using CPCV (not KFold or single split) for strategy evaluation
- [ ] `label_horizon` matches actual label construction
- [ ] `embargo_size` > 0 for autocorrelated features
- [ ] Reporting distribution statistics (mean, std, min), not single score
- [ ] Training set size after purging verified as sufficient
