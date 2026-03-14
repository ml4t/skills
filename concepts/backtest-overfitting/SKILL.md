---
name: ml4t-backtest-overfitting
description: Detect and prevent overfitting to historical data
category: concepts
type: conceptual
dependencies: [cpcv, deflated-sharpe]
book_chapters: [2, 17]
---

# Backtest Overfitting

Testing many strategies guarantees finding one that "worked" by chance.

## The Problem

Test 100 random strategies → ~5 will show p < 0.05 by chance alone.

```python
# The more you search, the more false positives
n_strategies_tested = 100
expected_false_positives = n_strategies_tested * 0.05  # = 5
```

## Probability of Backtest Overfitting (PBO)

```python
from ml4t.diagnostic.metrics import probability_of_backtest_overfitting

# From CPCV results
sharpe_ratios = [...]  # Sharpe from each CPCV fold
pbo = probability_of_backtest_overfitting(sharpe_ratios)

# PBO > 50% = likely overfit
```

## Deflated Sharpe Ratio

Adjusts Sharpe for multiple testing:

```python
from ml4t.diagnostic.metrics import deflated_sharpe_ratio

dsr = deflated_sharpe_ratio(
    observed_sharpe=1.5,
    n_trials=100,           # Strategies tested
    variance_of_sharpes=0.3,
    t_observations=252 * 5  # 5 years daily
)
# DSR < observed Sharpe (penalty for search)
```

## Red Flags

| Signal | Concern |
|--------|---------|
| Sharpe > 2.0 daily | Almost certainly overfit |
| OOS matches IS exactly | Data leakage likely |
| Complex model beats simple | Overfitting to noise |
| Performance degrades over time | Regime change or overfit |
| Many parameters tuned | Each is an implicit test |

## Prevention

### 1. Pre-Registration
```python
# Document BEFORE testing:
# - Hypothesis
# - Universe
# - Features
# - Validation method
# - Success criteria
# Commit to git, then test
```

### 2. Holdout Discipline
```python
# Split data ONCE at project start
train = data[:'2020']
validation = data['2020':'2022']
test = data['2022':]  # Touch ONCE at the end

# Never optimize on test set
```

### 3. Minimum Backtest Length
```python
# Rule of thumb: need sqrt(n) independent observations
# For Sharpe 1.0 with 95% confidence:
min_years = 5  # ~1250 daily observations
```

## Rules

```python
# WRONG: Tune until it works
for params in param_grid:
    if backtest(params).sharpe > 2:
        return params  # Found one!

# CORRECT: Pre-specify, report all trials
results = [backtest(p) for p in param_grid]
best = max(results, key=lambda x: x.sharpe)
dsr = deflated_sharpe_ratio(best.sharpe, n_trials=len(param_grid))
```

## Checklist

- [ ] Strategy hypothesis written BEFORE coding
- [ ] Number of strategies tested documented
- [ ] Using Deflated Sharpe Ratio
- [ ] PBO calculated from CPCV
- [ ] True holdout preserved until final test
