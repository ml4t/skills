---
name: ml4t-deflated-sharpe
description: Adjust Sharpe ratio for multiple testing bias
category: validation
type: operational
dependencies: [backtest-overfitting, cpcv]
book_chapters: [17]
quantlab_module: ml4t.diagnostic.metrics
---

# Deflated Sharpe Ratio

Sharpe ratio adjusted for the number of strategies tested.

## Why Deflate?

Observed Sharpe is biased upward when selecting the best from many trials.

```
Test 1 strategy:    E[max SR] ≈ true SR
Test 10 strategies: E[max SR] ≈ true SR + 0.5
Test 100 strategies: E[max SR] ≈ true SR + 1.0
```

## API

```python
from ml4t.diagnostic.metrics import deflated_sharpe_ratio

dsr = deflated_sharpe_ratio(
    observed_sharpe=1.5,
    n_trials=50,              # Number of strategies tested
    variance_of_sharpes=0.3,  # Variance across trials
    t_observations=1260       # Sample size (5 years daily)
)
```

## From CPCV Results

```python
from ml4t.diagnostic.splitters import CombinatorialPurgedCV

cv = CombinatorialPurgedCV(n_groups=8, n_test_groups=2, label_horizon=5)
sharpes = []

for train_idx, test_idx in cv.split(X):
    model.fit(X[train_idx], y[train_idx])
    returns = compute_strategy_returns(model, X[test_idx], y[test_idx])
    sr = returns.mean() / returns.std() * np.sqrt(252)
    sharpes.append(sr)

# Deflate using distribution from CPCV
dsr = deflated_sharpe_ratio(
    observed_sharpe=np.mean(sharpes),
    n_trials=len(sharpes),
    variance_of_sharpes=np.var(sharpes),
    t_observations=len(X)
)
```

## Interpretation

| DSR | Interpretation |
|-----|----------------|
| > 1.0 | Strong evidence of skill |
| 0.5-1.0 | Moderate evidence |
| < 0.5 | Weak, likely noise |
| < 0 | No evidence of skill |

## Haircut Table

Expected Sharpe inflation by number of trials:

| Trials | Expected Inflation |
|--------|-------------------|
| 10 | +0.4 |
| 50 | +0.8 |
| 100 | +1.0 |
| 500 | +1.3 |

## Rules

```python
# WRONG: Report observed Sharpe
print(f"Strategy Sharpe: {observed_sharpe:.2f}")

# CORRECT: Report deflated Sharpe
print(f"Observed Sharpe: {observed_sharpe:.2f}")
print(f"Trials tested: {n_trials}")
print(f"Deflated Sharpe: {dsr:.2f}")
```

## Guardrails

- Always track number of strategies tested
- Include failed strategies in trial count
- DSR assumes independent trials (conservative if correlated)
- Combine with PBO for full picture

## Checklist

- [ ] Number of trials documented
- [ ] DSR calculated and reported
- [ ] DSR > 0.5 minimum threshold
- [ ] Variance estimated from CPCV folds
