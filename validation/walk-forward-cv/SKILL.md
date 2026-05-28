---
name: ml4t-walk-forward-cv
description: "Rolling or expanding window CV that preserves temporal order. Use when evaluating ML models on time-series data where standard k-fold causes temporal leakage."
when_to_use: "Use when evaluating model stability across market regimes or comparing expanding vs rolling training"
dependencies: [purging-embargo]
metadata:
  book_chapters: "6, 7"
  library: "ml4t-diagnostic"
paths: ["**/*cv*.py", "**/*valid*.py", "**/*eval*.py", "**/*drift*.py", "**/*sharpe*.py", "**/*shap*.py", "**/*stationar*.py", "**/*purge*.py", "**/*embargo*.py", "**/*walk_forward*.py"]
---
# Walk-Forward Cross-Validation

A single train/test split tells you nothing about how a model adapts over time. Walk-forward CV slides a window through the data, training and testing sequentially, revealing how performance evolves across market regimes.

## The Problem

A single 80/20 train/test split produces one score from one market period. The model may excel in bull markets but fail in drawdowns — you cannot tell. Standard k-fold shuffles time, leaking future data. You need sequential evaluation that mirrors live deployment: train on the past, predict the future, advance, repeat. This exposes regime sensitivity and stationarity failures.

## The Pattern

### WRONG

```python
from sklearn.model_selection import train_test_split

# Single split — one market regime, no adaptation signal
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=True  # Shuffling leaks future
)
model.fit(X_train, y_train)
print(f"Score: {model.score(X_test, y_test):.3f}")  # One number
```

### CORRECT

```python
import numpy as np
from sklearn.model_selection import TimeSeriesSplit

# Walk-forward with gap for label horizon
n_splits = 5
gap = 5  # Purge gap matching label horizon
tscv = TimeSeriesSplit(n_splits=n_splits, gap=gap)

scores = []
for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
    model.fit(X[train_idx], y[train_idx])
    score = model.score(X[test_idx], y[test_idx])
    scores.append(score)
    print(f"Fold {fold}: train={len(train_idx)}, "
          f"test={len(test_idx)}, score={score:.3f}")

# Performance trajectory across time
print(f"Mean: {np.mean(scores):.3f}, Std: {np.std(scores):.3f}")
```

## Expanding vs Rolling

```
Expanding:  [-------train-------][test]  (more data, slower adaptation)
Rolling:         [----train----][test]   (fixed window, faster adaptation)
```

**Expanding** is the default with `TimeSeriesSplit`. For rolling, limit training size:

```python
# Rolling window: keep only most recent 504 training samples
max_train = 504  # ~2 years daily
for train_idx, test_idx in tscv.split(X):
    if len(train_idx) > max_train:
        train_idx = train_idx[-max_train:]
    model.fit(X[train_idx], y[train_idx])
```

## When to Use Each

| Variant | Best for | Trade-off |
|---|---|---|
| Expanding | Stable relationships, large feature sets | Slow to adapt to regime changes |
| Rolling | Regime-sensitive strategies, non-stationary data | Less data per fold, higher variance |

## Guardrails

- Never shuffle time-series data in any CV scheme
- When using `label_horizon`, purging is automatic; `gap` adds an extra buffer on top
- Test folds should span different market conditions (bull, bear, sideways)
- Expanding window scores should be compared to rolling — divergence signals non-stationarity
- More splits = more variance in estimates; fewer splits = more bias
- Evaluate at three levels: model diagnostics (loss, R²), signal diagnostics (IC, turnover), strategy outcomes (Sharpe) — divergence across levels reveals translation failures

## Production Implementation

`ml4t-diagnostic` provides `WalkForwardCV` with built-in purging and embargo:

```python
from ml4t.diagnostic.splitters import WalkForwardCV

cv = WalkForwardCV(
    n_splits=5,
    expanding=True,       # False for rolling window
    label_horizon=5,      # Automatic purge gap
    embargo_size=2,
)
for train_idx, test_idx in cv.split(X):
    model.fit(X[train_idx], y[train_idx])
    pred = model.predict(X[test_idx])
```

## Checklist

- [ ] Temporal order preserved — no shuffling
- [ ] Gap/purge >= label horizon between train and test
- [ ] Embargo applied for autocorrelated features
- [ ] Both expanding and rolling variants compared
- [ ] Performance trajectory inspected across folds (not just mean)
