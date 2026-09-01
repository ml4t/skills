---
name: ml4t-purging-embargo
description: "Remove training samples whose labels overlap the test period and add an embargo buffer. Use when performing time-series CV to prevent leakage between folds."
when_to_use: "Use when constructing any time-series cross-validation split with forward-looking labels"
dependencies: [lookahead-bias]
metadata:
  book_chapters: "6, 7"
  library: "ml4t-diagnostic"
paths: ["**/*cv*.py", "**/*valid*.py", "**/*eval*.py", "**/*drift*.py", "**/*sharpe*.py", "**/*shap*.py", "**/*stationar*.py", "**/*purge*.py", "**/*embargo*.py", "**/*walk_forward*.py"]
---
# Purging and Embargo

Standard train/test splits on time series leak information when labels span multiple periods. Purging removes contaminated training samples; embargo adds an extra buffer for feature autocorrelation.

## The Problem

A 5-day forward return label at day 98 uses prices from days 98-103. If the test set starts at day 100, training sample 98 contains information about test-period prices. Without purging, the model sees future test data through overlapping labels. Without embargo, autocorrelated features near the boundary still carry test-period signal. Both inflate CV scores and produce unreliable strategy evaluation.

## The Pattern

### WRONG

```python
from sklearn.model_selection import TimeSeriesSplit

# No gap between train and test - labels leak across boundary
cv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in cv.split(X):
    model.fit(X[train_idx], y[train_idx])  # Train includes leaked samples
    score = model.score(X[test_idx], y[test_idx])
```

### CORRECT

```python
import numpy as np

def purged_split(n_samples, train_end, test_start, test_end,
                 label_horizon=5, embargo_size=2):
    """Create a single purged train/test split with embargo."""
    # Sample i is safe only if its label closes before the test opens:
    # i + label_horizon < test_start. The +1 form kept i = test_start - horizon,
    # whose label lands exactly on the first test bar.
    train_idx = np.arange(0, test_start - label_horizon)  # Purge
    test_idx = np.arange(test_start, test_end)

    # Embargo: also exclude samples right after test end
    embargo_end = min(n_samples, test_end + embargo_size)
    post_test_train = np.arange(embargo_end, n_samples)
    train_idx = np.concatenate([train_idx, post_test_train])

    return train_idx, test_idx

# Timeline: [==TRAIN==][PURGE][==TEST==][EMBARGO][==TRAIN==]
# Samples:     0-94     95-99  100-110   111-112    113+
train_idx, test_idx = purged_split(
    n_samples=500, train_end=100, test_start=100,
    test_end=111, label_horizon=5, embargo_size=2
)
```

## How It Works

```
label_horizon = 5, embargo_size = 2

Timeline:  [====TRAIN====][PURGE][====TEST====][EMBARGO][====TRAIN====]
Indices:       0 ... 94    95-99   100 ... 110   111-112   113 ... N

Purge:   Sample 96 has label using prices 96-101 → overlaps test → REMOVE
Embargo: Sample 111 has features correlated with test period → REMOVE
```

## Parameter Guide

| Label Type | label_horizon | embargo_size |
|---|---|---|
| 1-day return | 1 | 1 |
| 5-day return | 5 | 1-2 |
| 10-day return | 10 | 2-3 |
| Triple-barrier 20d | 20 | 3-5 |

Rule of thumb: `embargo_size` = 10-20% of `label_horizon`.

## Guardrails

- `label_horizon` MUST match actual label construction - a mismatch voids the purge
- Verify training set retains enough samples after purging (especially with large horizons)
- For multi-asset panels, purge within each asset independently
- ACF analysis of features informs embargo sizing (higher autocorrelation → larger embargo)

## Production Implementation

`ml4t-diagnostic` handles purging and embargo automatically in its CV splitters:

```python
from ml4t.diagnostic.splitters import CombinatorialCV

cv = CombinatorialCV(
    n_groups=8,
    n_test_groups=2,
    label_horizon=10,   # Must match: y = returns.shift(-10)
    embargo_size=2,
)
for train_idx, test_idx in cv.split(X):
    # Purging and embargo applied automatically
    model.fit(X[train_idx], y[train_idx])
```

## Checklist

- [ ] `label_horizon` matches actual label construction exactly
- [ ] `embargo_size` > 0 for autocorrelated features (most financial data)
- [ ] Training set size after purging verified as sufficient (>50% of data)
- [ ] Multi-asset data uses per-asset purging, not global
- [ ] No samples within `label_horizon` of test boundary appear in training
