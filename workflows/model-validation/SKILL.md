---
name: ml4t-model-validation
description: "Multi-gate model validation from cross-validation through stress testing to deployment sign-off. Use when qualifying a model for production use."
when_to_use: "Use when a model is being considered for backtesting or live deployment"
dependencies: [cpcv, purging-embargo, deflated-sharpe, shap-analysis, backtest-overfitting]
metadata:
  book_chapters: "7, 12"
  library: "ml4t-diagnostic"
---
# Model Validation Workflow

A model that passes a single train/test split proves nothing. Rigorous validation requires combinatorial CV, overfitting probability, deflated statistics, feature attribution, and out-of-time holdout - all before any backtest.

## The Problem

A researcher splits data 80/20, trains a model, sees good test-set performance, and runs a backtest. The backtest looks promising. They deploy. The strategy loses money immediately. The cause: the single split was lucky, the model memorized regime-specific patterns, and hyperparameter tuning leaked information across the boundary. Without multiple validation gates, a model that looks good on one split can be arbitrarily overfit.

## The Pattern

### WRONG

```python
# Single train/test split, no overfitting checks, straight to deployment
from sklearn.model_selection import train_test_split
import lightgbm as lgb

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=True  # Shuffling time series!
)
model = lgb.LGBMRegressor().fit(X_train, y_train)
score = model.score(X_test, y_test)
print(f"R2: {score:.3f}")  # 0.15 - good enough, deploy
```

### CORRECT

```python
# Five-gate validation: CPCV → PBO → Deflated Sharpe → SHAP → OOS holdout
import numpy as np
import lightgbm as lgb
from scipy.stats import norm

# Gate 1: CPCV - multiple train/test paths, not one split (see ml4t-cpcv)
cv_sharpes = []
for train_idx, test_idx in time_aware_cv_splits:  # C(10,2) = 45 paths
    model = lgb.LGBMRegressor(n_estimators=100, random_state=42)
    model.fit(X[train_idx], y[train_idx])
    preds = model.predict(X[test_idx])
    sharpe = np.mean(preds * y[test_idx]) / np.std(preds * y[test_idx]) * np.sqrt(252)
    cv_sharpes.append(sharpe)

# Gate 2: fraction of paths that lose money. This is NOT PBO, which ranks the
# in-sample winner out of sample across splits (see ml4t-backtest-overfitting).
loss_rate = np.mean([s < 0 for s in cv_sharpes])
assert loss_rate < 0.50, f"{loss_rate:.0%} of paths negative - likely overfit"

# Gate 3: deflate the best path for the number of trials, in the same units as
# cv_sharpes (see ml4t-deflated-sharpe for the full probability form)
n = len(cv_sharpes)
expected_max = np.std(cv_sharpes) * (
    (1 - np.euler_gamma) * norm.ppf(1 - 1 / n)
    + np.euler_gamma * norm.ppf(1 - 1 / (n * np.e))
)
assert max(cv_sharpes) > expected_max, "best path is inside the selection bound"

# Gate 4: SHAP - verify features match hypothesis (see ml4t-shap-analysis)
import shap
shap_values = shap.TreeExplainer(model).shap_values(X[test_idx])

# Gate 5: OOS holdout - data never seen in any CV fold
oos_sharpe = (np.mean(model.predict(X_holdout) * y_holdout)
              / np.std(model.predict(X_holdout) * y_holdout) * np.sqrt(252))
degradation = (np.mean(cv_sharpes) - oos_sharpe) / np.mean(cv_sharpes)
assert degradation < 0.30, f"OOS degradation {degradation:.0%} - too high"
```

## Gate Summary

| # | Gate | Pass Condition | Fail Action |
|---|------|---------------|-------------|
| 1 | CPCV | Median path Sharpe > 0 | Simplify model or revisit features |
| 2 | PBO | < 50% of paths have negative Sharpe | Reduce model complexity |
| 3 | Deflated Sharpe | Significant after trial adjustment | Fewer hyperparameter trials |
| 4 | SHAP | Top features match economic hypothesis | Remove noise features |
| 5 | OOS holdout | Degradation < 30% from in-sample | Model memorized regime - redesign |

Gates are sequential. Do not skip to Gate 5 hoping a good holdout compensates for a bad PBO.

## Guardrails

- If PBO > 50%, adding more features or complexity will make it worse, not better
- If SHAP shows the model relies on a single feature for > 40% of predictions, the model is fragile
- If OOS degradation is < 5%, be suspicious - it often means data leakage, not a great model
- If CV Sharpe variance across folds is > 1.0, the signal is unstable across regimes

## Production Implementation

`ml4t-diagnostic` provides validated CPCV splitting with fold-level Sharpe
tracking and built-in DSR evaluation:

```python
from ml4t.diagnostic.api import ValidatedCrossValidation
from ml4t.diagnostic.config import ValidatedCrossValidationConfig

config = ValidatedCrossValidationConfig(n_groups=10, n_test_groups=2, embargo_pct=0.01)
vcv = ValidatedCrossValidation(config)
result = vcv.fit_evaluate(X, y, model, times=timestamps)
print(result.summary())
fold_sharpes = [fold.sharpe_ratio for fold in result.fold_results]
```

## Checklist

- [ ] Cross-validation uses CPCV with purging and embargo, not random splits
- [ ] PBO computed and < 50%
- [ ] Deflated Sharpe ratio significant after adjusting for number of trials
- [ ] SHAP feature importance aligns with economic hypothesis
- [ ] True out-of-time holdout tested (data never used in any CV fold)
- [ ] OOS performance degradation < 30% from in-sample
- [ ] All five gates passed before proceeding to backtest
