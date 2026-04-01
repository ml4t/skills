---
name: ml4t-feature-selection
description: "Select informative features using IC ranking, mutual information, or RFE — always within CV folds. Use when reducing feature dimensionality before training."
when_to_use: "Use when a feature set exceeds 20 features or contains suspected noise"
dependencies: [lookahead-bias]
metadata:
  book_chapters: "7, 8"
  library: "ml4t-diagnostic"
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
---
# Feature Selection

Selecting features on the full dataset is a form of lookahead bias. The test set influences which features are kept, inflating out-of-sample performance. Feature selection must happen inside each CV fold.

## The Problem

With 50 features and a finite sample, some will correlate with forward returns by chance alone. If you rank features by IC on the full dataset and keep the top 10, those 10 are partly selected for noise. Out-of-sample, the noise component vanishes and the model underperforms expectations.

## The Pattern

### WRONG
```python
from scipy.stats import spearmanr
import numpy as np

# Feature selection on full dataset — leaks test-set information
ic_scores = {col: abs(spearmanr(X[col], y).statistic) for col in X.columns}
selected = sorted(ic_scores, key=ic_scores.get, reverse=True)[:20]
model.fit(X[selected], y)
```

### CORRECT
```python
from scipy.stats import spearmanr
from sklearn.model_selection import TimeSeriesSplit
import numpy as np

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    X_train, y_train = X[train_idx], y[train_idx]

    # Select features using ONLY training data
    ic_scores = {
        col: abs(spearmanr(X_train[:, i], y_train).statistic)
        for i, col in enumerate(feature_names)
    }
    selected = sorted(ic_scores, key=ic_scores.get, reverse=True)[:20]
    sel_idx = [feature_names.index(f) for f in selected]

    model.fit(X_train[:, sel_idx], y_train)
    preds = model.predict(X[test_idx][:, sel_idx])
```

## Selection Methods

| Method | Type | When to Use |
|--------|------|-------------|
| IC ranking | Univariate | Quick filter, large feature set |
| Mutual information | Univariate | Non-linear relationships |
| L1 regularization | Embedded | During training (Lasso, ElasticNet) |
| SHAP importance | Model-based | After training, interpretation |
| Recursive feature elimination | Wrapper | Small feature set, expensive |

## Collinearity Removal (Pre-Selection)

```python
import numpy as np

def remove_collinear(corr_matrix: np.ndarray, feature_names: list, threshold: float = 0.8) -> list:
    """Drop one feature from each highly correlated pair."""
    to_drop = set()
    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            if abs(corr_matrix[i, j]) > threshold:
                to_drop.add(feature_names[j])
    return [f for f in feature_names if f not in to_drop]
```

## Selection Stability Diagnostic

```python
# Track which features are selected across folds
from collections import Counter
fold_selections = Counter()
for train_idx, _ in tscv.split(X):
    selected = select_top_k(X[train_idx], y[train_idx], k=20)
    fold_selections.update(selected)

# Features selected in <50% of folds are unstable — likely noise
stable = [f for f, count in fold_selections.items() if count >= len(list(tscv.split(X))) // 2]
```

## Guardrails

- **Selection inside CV is non-negotiable** — any global selection is lookahead bias
- **Stability across folds matters** — a feature selected in 1/5 folds is noise
- **IC > 0.1 is suspicious** — investigate for leakage before trusting
- **Collinearity removal is safe pre-CV** — it uses only feature-feature correlation, not the target

## Production Implementation

`ml4t-diagnostic` provides a validated feature selection pipeline:

```python
from ml4t.diagnostic.selection import FeatureSelector, SelectionReport

selector = FeatureSelector(outcome_results, correlation_matrix)
selector.filter_by_ic(threshold=0.02).filter_by_correlation(threshold=0.8)
report: SelectionReport = selector.get_selection_report()
selected_features = report.final_features
```

## Checklist

- [ ] Feature selection happens inside each CV fold, never on the full dataset
- [ ] Collinearity removed first (threshold 0.7-0.8)
- [ ] Selection stability checked across folds (>50% agreement)
- [ ] No feature with IC > 0.1 accepted without leakage investigation
- [ ] Selected feature set documented and versioned
