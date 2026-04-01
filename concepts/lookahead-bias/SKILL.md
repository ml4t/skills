---
name: ml4t-lookahead-bias
description: "Detect future information leaking into features, labels, or evaluation. Use when any pipeline step might expose data not yet available at prediction time."
when_to_use: "Use when computing features, creating labels, preprocessing data, or setting up cross-validation for time-series models"
dependencies: []
metadata:
  book_chapters: "6, 7"
  library: "ml4t-diagnostic"
---
# Lookahead Bias

The most common ML4T failure. A model uses future information during training — normalization with full-sample statistics, labels from future thresholds, standard k-fold CV on time series — producing a great backtest that fails immediately in production.

## The Problem

Lookahead bias means using information that would not have been available at
prediction time. It inflates backtest Sharpe and is the #1 reason strategies
fail live. Common sources: full-sample normalization, future-based thresholds,
train+test preprocessing, and shuffled CV on time series.

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

# Time-series CV that preserves order
from sklearn.model_selection import TimeSeriesSplit
cv = TimeSeriesSplit(n_splits=5)
```

## Preprocessing Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

# Pipeline ensures scaler is fit on train only, even inside CV
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", Ridge()),
])
pipe.fit(X_train, y_train)       # scaler sees only training data
pipe.predict(X_test)             # test data transformed with train stats
```

## Detection

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

```python
from ml4t.diagnostic.splitters import CombinatorialCV
from ml4t.engineer import create_dataset_builder

builder = create_dataset_builder(features, labels, dates=timestamps, scaler="standard")
cv = CombinatorialCV(n_groups=8, n_test_groups=2, embargo_pct=0.01)
fold = next(builder.split(cv))
X_train, y_train = fold.X_train, fold.y_train
X_test, y_test = fold.X_test, fold.y_test
```

## Checklist

- [ ] All normalizations use expanding window with `.shift(1)`, not full-sample stats
- [ ] `fit_transform()` only on training data (use `Pipeline` or explicit split)
- [ ] Time-series CV with purging and embargo (not shuffled k-fold)
- [ ] Labels do not use future thresholds or statistics
- [ ] Point-in-time data: report dates used, not period-end dates
- [ ] Suspicious results investigated: Sharpe > 2, IS/OOS gap < 5%
