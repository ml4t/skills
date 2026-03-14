---
name: ml4t-model-validation
description: Comprehensive model validation before deployment
category: workflows
type: workflow
dependencies: [cpcv, deflated-sharpe, shap-analysis, regime-backtest, sensitivity-analysis]
book_chapters: [12, 17]
---

# Model Validation Workflow

Rigorous validation before production deployment.

## Stage Overview

```
1. Cross-Validation → 2. Backtest → 3. Stress Test → 4. Sensitivity → 5. Sign-off
```

## Stage 1: Cross-Validation

```python
from ml4t.diagnostic.splitters import CombinatorialPurgedCV
from ml4t.diagnostic.metrics import probability_of_backtest_overfitting

cv = CombinatorialPurgedCV(n_groups=10, n_test_groups=2, purge_gap=5)

cv_results = []
for train_idx, test_idx in cv.split(X):
    model.fit(X[train_idx], y[train_idx])
    pred = model.predict(X[test_idx])
    sharpe = calculate_sharpe(pred, y[test_idx])
    cv_results.append(sharpe)

pbo = probability_of_backtest_overfitting(cv_results)
print(f"PBO: {pbo:.1%}")  # Should be < 50%
```

## Stage 2: Out-of-Sample Backtest

```python
# True holdout (never touched during development)
holdout_start = '2022-01-01'
holdout_end = '2024-12-31'

holdout_results = run_backtest(
    strategy=Strategy(model),
    data=data.filter(pl.col('date') >= holdout_start),
    costs=realistic_costs
)

# Compare to in-sample
is_sharpe = np.mean(cv_results)
oos_sharpe = holdout_results.sharpe
degradation = (is_sharpe - oos_sharpe) / is_sharpe
print(f"OOS degradation: {degradation:.1%}")  # Should be < 30%
```

## Stage 3: Stress Testing

```python
from ml4t.portfolio.stress import stress_test_report

stress_results = stress_test_report(
    weights=final_weights,
    scenarios=HISTORICAL_SCENARIOS
)

# Check survival
max_stress_loss = stress_results['loss'].min()
print(f"Worst scenario loss: {max_stress_loss:.1%}")
assert max_stress_loss > -0.30, "Would not survive historical stress"
```

## Stage 4: Sensitivity Analysis

```python
from ml4t.backtest.sensitivity import parameter_sweep

sensitivity = parameter_sweep(
    strategy_fn=strategy_with_params,
    param_grid={
        'lookback': [20, 40, 60, 80],
        'threshold': [0.5, 1.0, 1.5, 2.0]
    }
)

robustness = (sensitivity['sharpe'] > 0).mean()
print(f"Robustness: {robustness:.1%}")  # Should be > 70%
```

## Stage 5: Sign-off Checklist

```python
validation_results = {
    'pbo': pbo,
    'oos_sharpe': oos_sharpe,
    'oos_degradation': degradation,
    'max_stress_loss': max_stress_loss,
    'robustness_score': robustness
}

THRESHOLDS = {
    'pbo': (lambda x: x < 0.50, "PBO must be < 50%"),
    'oos_sharpe': (lambda x: x > 0.5, "OOS Sharpe must be > 0.5"),
    'oos_degradation': (lambda x: x < 0.30, "Degradation must be < 30%"),
    'max_stress_loss': (lambda x: x > -0.30, "Stress loss must be > -30%"),
    'robustness_score': (lambda x: x > 0.70, "Robustness must be > 70%")
}

for metric, (check, msg) in THRESHOLDS.items():
    passed = check(validation_results[metric])
    print(f"{'✓' if passed else '✗'} {msg}: {validation_results[metric]:.2f}")
```

## Checkpoints

- [ ] CPCV with purging and embargo
- [ ] PBO < 50%
- [ ] True holdout backtested
- [ ] OOS degradation < 30%
- [ ] Stress tests passed
- [ ] Parameter sensitivity checked
- [ ] All sign-off criteria met
