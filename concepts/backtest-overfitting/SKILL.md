---
name: ml4t-backtest-overfitting
description: Detect and prevent overfitting to historical data via multiple testing corrections and pre-registration. Use when evaluating strategy backtests, tuning hyperparameters, or comparing multiple strategies.
dependencies: [lookahead-bias]
metadata:
  book_chapters: "7, 16"
  library: "ml4t-diagnostic"
---

# Backtest Overfitting

Testing many strategies on the same data guarantees finding one that looks profitable by chance. With 100 independent trials at p < 0.05, you expect five false positives.

## The Problem

Every parameter you tune, every feature you try, and every universe filter you adjust is an implicit trial. A researcher who reports a Sharpe ratio of 2.0 after exploring 200 configurations has not found alpha -- they have found the luckiest draw from a noise distribution. The Deflated Sharpe Ratio corrects for this by penalizing for the number of trials conducted. Without it, most published backtests are statistically meaningless.

## The Pattern

### WRONG

```python
# Tune until something looks good
best_sharpe = 0
for lookback in [5, 10, 21, 63, 126, 252]:
    for top_k in [5, 10, 20, 50]:
        result = backtest(lookback=lookback, top_k=top_k)
        if result.sharpe > best_sharpe:
            best_sharpe = result.sharpe
            best_params = (lookback, top_k)

print(f"Best Sharpe: {best_sharpe:.2f}")  # meaningless without correction
```

### CORRECT

```python
import numpy as np
from scipy.stats import norm

results = []
for lookback in [5, 10, 21, 63, 126, 252]:
    for top_k in [5, 10, 20, 50]:
        result = backtest(lookback=lookback, top_k=top_k)
        results.append(result.sharpe)

# Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2014)
n_trials = len(results)
best_sharpe = max(results)
sharpe_std = np.std(results)
expected_max = sharpe_std * (
    (1 - np.euler_gamma) * norm.ppf(1 - 1 / n_trials)
    + np.euler_gamma * norm.ppf(1 - 1 / (n_trials * np.e))
)
deflated_sharpe = best_sharpe - expected_max
print(f"Observed: {best_sharpe:.2f}, Deflated: {deflated_sharpe:.2f}, Trials: {n_trials}")
```

## Probability of Backtest Overfitting (PBO)

PBO uses combinatorial cross-validation to estimate the chance that the best in-sample strategy underperforms out-of-sample:

```python
from sklearn.model_selection import TimeSeriesSplit
import numpy as np

# Simplified PBO: rank correlation between IS and OOS Sharpe across folds
is_ranks, oos_ranks = [], []
tscv = TimeSeriesSplit(n_splits=8)
for train_idx, test_idx in tscv.split(data):
    is_sharpe = [backtest(p, data[train_idx]).sharpe for p in param_grid]
    oos_sharpe = [backtest(p, data[test_idx]).sharpe for p in param_grid]
    is_ranks.append(np.argsort(is_sharpe))
    oos_ranks.append(np.argsort(oos_sharpe))

# PBO > 0.5 = best IS strategy is more likely to underperform OOS
```

## Red Flags

| Signal | Concern |
|--------|---------|
| Sharpe > 2.0 on daily data | Almost certainly overfit or leakage |
| OOS matches IS within 5% | Data leakage, not genuine alpha |
| Complex model barely beats simple | Extra parameters fit noise |
| Performance cliff after 2020 | Regime-specific overfitting |

## Guardrails

- Document the total number of configurations tested -- each is a trial.
- Pre-register the hypothesis and success threshold in version control before running any backtest.
- Reserve a true holdout set that is touched exactly once, at the very end.
- Minimum backtest length: 5 years of daily data (roughly 1,250 observations) for Sharpe estimation.
- If deflated Sharpe is negative, the strategy has no statistical evidence of alpha.

## Production Implementation

`ml4t-diagnostic` provides validated implementations of both corrections:

```python
from ml4t.diagnostic.evaluation.stats import compute_pbo, benjamini_hochberg_fdr
from ml4t.diagnostic.splitters import CombinatorialCV

cpcv = CombinatorialCV(n_groups=8, n_test_groups=2, embargo_size=5)
pbo = compute_pbo(sharpe_matrix)               # from CPCV fold results
rejected = benjamini_hochberg_fdr(p_values, alpha=0.05)
```

## Checklist

- [ ] Strategy hypothesis written and committed to git BEFORE any backtest
- [ ] Total number of trials documented (including informal exploration)
- [ ] Deflated Sharpe Ratio computed and reported alongside observed Sharpe
- [ ] PBO calculated from combinatorial CV folds (PBO < 0.50 required)
- [ ] True holdout set preserved and used exactly once
