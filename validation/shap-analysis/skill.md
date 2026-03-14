---
name: ml4t-shap-analysis
description: Interpret model predictions with SHAP values
category: validation
type: operational
dependencies: []
book_chapters: [13, 27]
---

# SHAP Analysis

Explain model predictions with feature attributions.

## Core Concepts

| Term | Definition |
|------|------------|
| SHAP value | Feature contribution to prediction |
| Base value | Model output with no features |
| Additivity | sum(SHAP) + base = prediction |

## API

```python
import shap

# Tree-based models (fast)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# Any model (slower)
explainer = shap.KernelExplainer(model.predict, X_background)
shap_values = explainer.shap_values(X)
```

## Global Importance

```python
# Feature importance across all samples
importance = np.abs(shap_values).mean(axis=0)
sorted_idx = np.argsort(importance)[::-1]

for i in sorted_idx[:10]:
    print(f"{X.columns[i]}: {importance[i]:.4f}")
```

## Local Explanations

```python
# Explain single prediction
idx = 42
print(f"Prediction: {model.predict(X.iloc[idx:idx+1])[0]:.4f}")
print(f"Base value: {explainer.expected_value:.4f}")

for i, col in enumerate(X.columns):
    if abs(shap_values[idx, i]) > 0.01:
        print(f"  {col}: {shap_values[idx, i]:+.4f}")
```

## Monitoring Feature Drift

```python
def shap_drift(shap_baseline: np.ndarray, shap_current: np.ndarray,
               feature_names: list) -> dict:
    """Detect drift in feature importance."""
    baseline_imp = np.abs(shap_baseline).mean(axis=0)
    current_imp = np.abs(shap_current).mean(axis=0)

    drift = {}
    for i, name in enumerate(feature_names):
        change = (current_imp[i] - baseline_imp[i]) / (baseline_imp[i] + 1e-6)
        drift[name] = change

    return drift
```

## Visualization

```python
# Summary plot (all features)
shap.summary_plot(shap_values, X, feature_names=X.columns)

# Dependence plot (single feature)
shap.dependence_plot('momentum_12m', shap_values, X)

# Force plot (single prediction)
shap.force_plot(explainer.expected_value, shap_values[idx], X.iloc[idx])
```

## Guardrails

- TreeExplainer is exact for trees; use it when available
- KernelExplainer approximates; may be noisy
- SHAP values depend on background dataset choice
- Feature interactions can be complex

## Checklist

- [ ] Global importance ranked
- [ ] Top features align with hypothesis
- [ ] Local explanations spot-checked
- [ ] SHAP drift monitored in production
