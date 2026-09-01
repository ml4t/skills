---
name: ml4t-deflated-sharpe
description: "Adjust the Sharpe ratio for multiple testing bias when selecting from many trials. Use when reporting strategy performance after parameter or model search."
when_to_use: "Use when reporting strategy performance after evaluating multiple configurations or signals"
dependencies: [cpcv]
metadata:
  book_chapters: "7, 16"
  library: "ml4t-diagnostic"
paths: ["**/*cv*.py", "**/*valid*.py", "**/*eval*.py", "**/*drift*.py", "**/*sharpe*.py", "**/*shap*.py", "**/*stationar*.py", "**/*purge*.py", "**/*embargo*.py", "**/*walk_forward*.py"]
---
# Deflated Sharpe Ratio

Reporting the best Sharpe ratio from N trials is misleading. The Deflated Sharpe Ratio corrects for the number of trials, non-normal returns, and sample size to test whether observed performance reflects genuine skill.

## The Problem

If you test 100 strategy variants and report the best Sharpe, you are performing selection bias. Under the null of zero skill, the expected maximum Sharpe across N trials grows with `sqrt(2 * log(N))`, measured in units of the spread of Sharpes across those trials: at 100 trials the best result is about 2.5 spreads above zero before any alpha exists. Without correction, most "discovered" strategies are artifacts that fail out of sample.

## The Pattern

### WRONG

```python
import numpy as np

# Test 50 parameter combos, report the best
sharpes = []
for params in param_grid:  # 50 configurations
    returns = run_backtest(params)
    sr = returns.mean() / returns.std() * np.sqrt(252)
    sharpes.append(sr)

best = max(sharpes)
print(f"Strategy Sharpe: {best:.2f}")  # Inflated by selection
```

### CORRECT

```python
import numpy as np
from scipy import stats

def deflated_sharpe_ratio(observed_sr, n_trials, sr_std, n_obs,
                          skew=0.0, kurtosis=3.0):
    """Deflate a per-period (not annualised) Sharpe (Bailey & de Prado)."""
    # Expected max SR under null (Euler-Mascheroni approximation)
    euler_mascheroni = 0.5772
    e_max_sr = sr_std * (
        (1 - euler_mascheroni) * stats.norm.ppf(1 - 1 / n_trials)
        + euler_mascheroni * stats.norm.ppf(1 - 1 / (n_trials * np.e))
    )
    # SR standard error with non-normal correction
    sr_se = np.sqrt(
        (1 - skew * observed_sr + (kurtosis - 1) / 4 * observed_sr**2)
        / (n_obs - 1)
    )
    # Test statistic: is observed SR significantly above expected max?
    test_stat = (observed_sr - e_max_sr) / sr_se
    return stats.norm.cdf(test_stat)  # probability the skill is real

# sr_se is the standard error of a PER-PERIOD Sharpe. Passing annualised values
# shrinks it by sqrt(252) and saturates DSR at 0.00 or 1.00 instead of measuring.
per_period = np.array(sharpes) / np.sqrt(252)
dsr = deflated_sharpe_ratio(
    observed_sr=per_period.max(),
    n_trials=len(per_period),
    sr_std=per_period.std(),
    n_obs=252 * 5,  # 5 years daily
)
print(f"Best of {len(sharpes)} trials: {max(sharpes):.2f} annualised")
print(f"DSR: {dsr:.3f}")  # a probability, not a p-value: high is good
```

## Interpretation

| DSR | Meaning |
|---|---|
| > 0.95 | Strong evidence of genuine skill |
| 0.80-0.95 | Moderate evidence, worth investigating |
| < 0.80 | Likely noise - do not deploy |

## Expected Sharpe Inflation

| Trials | E[max Sharpe] under the null, in units of `sr_std` |
|---|---|
| 10 | 1.6 |
| 50 | 2.3 |
| 100 | 2.5 |
| 500 | 3.1 |

## Guardrails

- Always count ALL trials tested, including abandoned or failed ones
- DSR assumes approximately independent trials - correlated strategies understate the correction
- Non-normal returns (fat tails, skew) make the correction larger via the kurtosis/skew terms
- Combine with Probability of Backtest Overfitting (PBO) for a complete picture

## Production Implementation

`ml4t-diagnostic` provides a direct deflated Sharpe implementation:

```python
from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio

# Single strategy -> PSR
single = deflated_sharpe_ratio(strategy_returns, frequency="daily")

# Multiple strategies -> DSR with multiple-testing correction
search = deflated_sharpe_ratio(candidate_return_series, frequency="daily")
print(f"PSR probability: {single.probability:.3f}")
print(f"DSR probability: {search.probability:.3f}")
print(f"Deflated Sharpe: {search.deflated_sharpe:.3f}")
```

## Checklist

- [ ] Total number of trials documented (including failures)
- [ ] DSR computed and reported alongside observed Sharpe
- [ ] DSR > 0.95 before declaring viable; non-normality (skew, kurtosis) included
- [ ] Variance of Sharpe estimates sourced from CPCV folds when available
