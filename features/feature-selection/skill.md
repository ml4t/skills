---
name: ml4t-feature-selection
description: Select relevant features and reduce dimensionality
category: features
type: operational
dependencies: [information-coefficient]
book_chapters: [9]
---

# Feature Selection

Reduce features to those with genuine predictive power.

## Methods

| Method | Type | Use Case |
|--------|------|----------|
| IC ranking | Univariate | Quick filtering |
| Mutual information | Univariate | Non-linear |
| RFE | Wrapper | Model-specific |
| L1 regularization | Embedded | During training |
| SHAP importance | Model-agnostic | Interpretation |

## IC-Based Selection

```python
from ml4t.diagnostic.metrics import information_coefficient

# Calculate IC for each feature
ic_scores = {}
for col in feature_cols:
    ic = information_coefficient(X[col], y)
    ic_scores[col] = ic.mean()

# Select top features
selected = sorted(ic_scores, key=ic_scores.get, reverse=True)[:20]
```

## SHAP-Based Selection

```python
import shap

# Fit model
model.fit(X_train, y_train)

# Calculate SHAP values
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Feature importance
importance = np.abs(shap_values).mean(axis=0)
top_features = X.columns[np.argsort(importance)[-20:]]
```

## Collinearity Removal

```python
def remove_collinear(X: pl.DataFrame, threshold: float = 0.8) -> list:
    """Remove highly correlated features."""
    corr = X.corr()
    to_drop = set()

    for i, col in enumerate(corr.columns):
        for j in range(i + 1, len(corr.columns)):
            if abs(corr[i, j]) > threshold:
                # Drop feature with lower IC
                to_drop.add(corr.columns[j])

    return [c for c in X.columns if c not in to_drop]
```

## Walk-Forward Selection

```python
# WRONG: Select features on full dataset
selected = select_features(X, y)  # Leakage

# CORRECT: Select features only on training data
for train_idx, test_idx in cv.split(X):
    selected = select_features(X[train_idx], y[train_idx])
    model.fit(X[train_idx][selected], y[train_idx])
```

## Guardrails

- Feature selection must be inside CV loop
- IC-based selection can overfit to noise
- Start with more features, regularize
- Stability of selection across folds is informative

## Checklist

- [ ] Selection inside cross-validation
- [ ] Collinearity checked
- [ ] Multiple methods compared
- [ ] Selection stability assessed
