---
name: ml4t-data-leakage
description: Prevent train-test contamination, target leakage, and temporal leakage in ML pipelines. Use when building features, fitting transformers, or splitting data for cross-validation.
dependencies: [lookahead-bias]
metadata:
  book_chapters: "2, 7, 8"
  library: "ml4t-diagnostic"
---

# Data Leakage

Leakage lets test-set information influence training, producing models that look good in development but fail in production.

## The Problem

Three distinct failure modes inflate backtest performance:

1. **Target leakage** -- features computed from the target variable (e.g., future returns embedded in a "sentiment score" that was derived from price changes).
2. **Train-test contamination** -- fitting a scaler, encoder, or selector on the full dataset before splitting, so test statistics leak into training transforms.
3. **Temporal leakage** -- using future data in features (overlaps with lookahead bias, but here the mechanism is the train/test split itself, not the feature formula).

A pipeline that fits a `StandardScaler` on the full matrix before splitting commonly inflates Sharpe by 0.2--0.5 on daily data. The model learns the test set's distribution.

## The Pattern

### WRONG

```python
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)          # fit on ALL data (leaks test stats)

X_train, X_test = X_scaled[:split], X_scaled[split:]
y_train, y_test = y[:split], y[split:]

model = Ridge().fit(X_train, y_train)
print(model.score(X_test, y_test))           # inflated R^2
```

### CORRECT

```python
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge

X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

pipe = Pipeline([
    ("scaler", StandardScaler()),             # fit on train only
    ("model", Ridge()),
])
pipe.fit(X_train, y_train)
print(pipe.score(X_test, y_test))             # honest R^2
```

## Detection Heuristics

| Red flag | Likely cause |
|----------|--------------|
| `fit_transform(X)` before any split | Train-test contamination |
| Feature-target Pearson > 0.5 | Target leakage |
| OOS performance matches IS within 1% | Information bleeding through |
| Accuracy > 55% on daily return direction | Verify no leakage before celebrating |

## Guardrails

- Search codebase for `fit_transform` calls that precede `train_test_split` -- each one is a leak candidate.
- Compute feature-target correlation on the training fold only; correlation > 0.3 warrants investigation.
- Any `SelectKBest` or `mutual_info_classif` call on the full dataset is leakage -- wrap in a pipeline.
- Time-series splits must respect temporal order: no shuffled k-fold on sequential data.

## Production Implementation

`ml4t-engineer` provides a leakage-safe dataset builder that enforces correct split ordering:

```python
from ml4t.engineer import create_dataset_builder
from ml4t.diagnostic.splitters import WalkForwardCV

builder = create_dataset_builder(
    features=feature_frame,
    labels=label_series,
    dates=feature_frame["timestamp"],
    scaler="standard",
)
cv = WalkForwardCV(n_splits=8, test_size=63, embargo_size=5)
for fold in builder.split(cv):
    X_train, y_train = fold.X_train, fold.y_train
    X_test, y_test = fold.X_test, fold.y_test  # scaler fit on train only
```

## Checklist

- [ ] All `fit()` / `fit_transform()` calls happen on training data only
- [ ] Feature selection wrapped inside the CV loop (not before splitting)
- [ ] No shuffled k-fold on time-series data
- [ ] Feature-target correlations reviewed for target leakage
- [ ] Pipeline used to chain scaler + model (prevents ordering mistakes)
