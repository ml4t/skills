---
name: ml4t-lookahead-bias
description: Detect and prevent future information leaking into features, labels, and evaluation. Use when computing features, creating labels, preprocessing data, or setting up cross-validation for time-series models.
dependencies: []
metadata:
  book_chapters: "6, 7"
  library: "ml4t-diagnostic"
---

# Lookahead Bias

The most common ML4T failure. A model uses future information during training — normalization with full-sample statistics, labels from future thresholds, standard k-fold CV on time series — producing a great backtest that fails immediately in production.

## The Problem

Lookahead bias means using information that would not have been available at the time of the prediction. It inflates backtest Sharpe ratios by 0.5-2.0 and is the #1 reason strategies fail in live trading. The bias is insidious because the code runs without errors and the results look plausible. Common sources: normalizing with full-sample mean/std, computing label thresholds from the entire dataset, fitting a scaler on train+test, and using shuffled k-fold CV on time series.

## The Pattern

### WRONG

```python
import numpy as np
from sklearn.preprocessing import StandardScaler

# Normalize features using full dataset statistics (future leak)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # mean/std computed on ALL data including test

# Label threshold from full history (future leak)
threshold = returns.quantile(0.75)  # Uses future returns to set threshold
y = (forward_returns > threshold).astype(int)

# Shuffled k-fold on time series (future leak)
from sklearn.model_selection import KFold
cv = KFold(n_splits=5, shuffle=True)  # Training on 2024 data, testing on 2020
```

### CORRECT

```python
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Expanding-window normalization: only past data
X_normalized = (X - X.expanding().mean().shift(1)) / X.expanding().std().shift(1)

# Expanding threshold: only past returns
threshold = returns.expanding().quantile(0.75).shift(1)
y = (forward_returns > threshold).astype(int)

# Time-series CV with purging and embargo
from ml4t.diagnostic.splitters import CombinatorialCV
cv = CombinatorialCV(n_groups=8, n_test_groups=2, embargo_pct=0.01)
```

## Preprocessing Pipeline

Scikit-learn pipelines prevent the most common leak — fitting the scaler on the full dataset:

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

# WRONG: fit scaler on all data, then split
scaler = StandardScaler().fit(X)
X_train, X_test = X_scaled[:split], X_scaled[split:]

# CORRECT: scaler inside pipeline, fit only on train folds
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", Ridge()),
])
# cross_val_predict calls fit (including scaler) only on training folds
```

## Detection

Suspect lookahead bias when:

- In-sample and out-of-sample performance are suspiciously similar (gap < 5%)
- Sharpe ratio > 2.0 on daily data with a simple model
- Feature values change when you recompute with more recent data appended
- Performance degrades sharply when switching from k-fold to walk-forward CV

## Guardrails

- All rolling/expanding statistics must use `.shift(1)` to exclude the current observation
- `fit_transform()` must never touch test data — use `Pipeline` or manual train/test splits
- Cross-validation must respect temporal order — no `shuffle=True` on time series
- Label thresholds must be computed from past data only (expanding window)
- Point-in-time fundamentals: use report dates, not period dates

## Production Implementation

`ml4t-diagnostic` provides leakage-safe cross-validation and evaluation:

```python
from ml4t.diagnostic.splitters import CombinatorialCV, WalkForwardCV
from ml4t.engineer import create_dataset_builder

# Leakage-safe dataset builder
builder = create_dataset_builder(features, labels, embargo_days=5)
X_train, y_train = builder.get_train(fold=0)

# Combinatorial Purged CV — correct temporal splitting
cv = CombinatorialCV(n_groups=8, n_test_groups=2, embargo_pct=0.01)
```

## Checklist

- [ ] All normalizations use expanding window with `.shift(1)`, not full-sample stats
- [ ] `fit_transform()` only on training data (use `Pipeline` or explicit split)
- [ ] Time-series CV with purging and embargo (not shuffled k-fold)
- [ ] Labels do not use future thresholds or statistics
- [ ] Point-in-time data: report dates used, not period-end dates
- [ ] Suspicious results investigated: Sharpe > 2, IS/OOS gap < 5%
