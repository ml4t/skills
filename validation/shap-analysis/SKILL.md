---
name: ml4t-shap-analysis
description: Explain model predictions with SHAP values instead of biased built-in feature importance. Use when interpreting gradient boosting or black-box model behavior for trading decisions.
dependencies: []
metadata:
  book_chapters: "12, 15"
  library: "ml4t-diagnostic"
---

# SHAP Analysis

Built-in `feature_importances_` in tree models is biased toward high-cardinality and correlated features. SHAP values provide additive, consistent feature attributions grounded in game theory.

## The Problem

LightGBM's `feature_importances_` (gain or split-based) systematically overweights features with more unique values and features that are correlated with other predictors. Two features with identical predictive power but different cardinality will show different importance. This leads to incorrect feature selection, misleading model narratives, and poor decisions about which signals to keep or discard. SHAP values are the only feature attribution method that satisfies both local accuracy (attributions sum to prediction) and consistency (a feature that contributes more never gets lower attribution).

## The Pattern

### WRONG

```python
import lightgbm as lgb

model = lgb.LGBMRegressor().fit(X_train, y_train)

# Built-in importance — biased toward high-cardinality features
importance = model.feature_importances_
for name, imp in sorted(zip(feature_names, importance), key=lambda x: -x[1])[:5]:
    print(f"{name}: {imp}")
# A noisy ID-like feature may rank #1 due to many split points
```

### CORRECT

```python
import numpy as np
import shap

model = lgb.LGBMRegressor().fit(X_train, y_train)

# TreeSHAP — exact, fast for tree-based models
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Global importance: mean |SHAP| per feature
importance = np.abs(shap_values).mean(axis=0)
sorted_idx = np.argsort(importance)[::-1]
for i in sorted_idx[:10]:
    print(f"{feature_names[i]:>25}: {importance[i]:.4f}")

# Verify additivity: base_value + sum(SHAP) = prediction
pred = model.predict(X_test[:1])[0]
shap_sum = explainer.expected_value + shap_values[0].sum()
assert abs(pred - shap_sum) < 1e-6, "SHAP values must sum to prediction"
```

## Local Explanations

Understand why the model made a specific prediction:

```python
# Explain a single high-conviction prediction
idx = np.argmax(np.abs(model.predict(X_test)))
print(f"Prediction: {model.predict(X_test[idx:idx+1])[0]:.4f}")
print(f"Base value: {explainer.expected_value:.4f}")
for i in np.argsort(np.abs(shap_values[idx]))[::-1][:5]:
    print(f"  {feature_names[i]:>25}: {shap_values[idx, i]:+.4f}")
```

## SHAP for Feature Selection

```python
# Keep features with mean |SHAP| above threshold
mean_shap = np.abs(shap_values).mean(axis=0)
threshold = np.percentile(mean_shap, 50)  # Keep top 50%
selected = [f for f, s in zip(feature_names, mean_shap) if s >= threshold]
print(f"Selected {len(selected)} / {len(feature_names)} features")
```

## Guardrails

- Use `TreeExplainer` for tree models (exact, O(TLD) per sample) — `KernelExplainer` is approximate and slow
- SHAP values depend on the background dataset — use the training set, not a random sample
- Feature interactions can mask individual SHAP values — check `shap.dependence_plot` for interaction effects
- SHAP importance across folds should be stable — high variance signals model instability, not feature importance
- For time-series models, compute SHAP on each walk-forward fold separately

## Production Implementation

`ml4t-diagnostic` provides SHAP-based importance with cross-validated stability:

```python
from ml4t.diagnostic.evaluation.metrics import compute_shap_importance
from ml4t.diagnostic.evaluation import TradeShapAnalyzer

# Cross-validated SHAP importance with stability metrics
shap_report = compute_shap_importance(
    model, X_test, feature_names=feature_names
)
# Returns dict with sorted feature_names, importances, shap_values, and base_value
top_features = list(zip(shap_report["feature_names"][:10], shap_report["importances"][:10]))

# For post-trade debugging, TradeShapAnalyzer links SHAP values to bad trades
trade_analyzer = TradeShapAnalyzer(model, features_df)
```

## Checklist

- [ ] Using SHAP values (not built-in `feature_importances_`) for interpretation
- [ ] `TreeExplainer` used for tree-based models, `KernelExplainer` only for black-box
- [ ] Additivity verified: `base_value + sum(shap_values) == prediction`
- [ ] Top features checked against domain knowledge (momentum, volatility, etc.)
- [ ] SHAP stability verified across walk-forward folds
