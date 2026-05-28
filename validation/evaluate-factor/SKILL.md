---
name: ml4t-evaluate-factor
description: "Evaluate alpha factor quality with IC analysis, quantile spreads, turnover, and decay. Use when deciding whether a signal has enough predictive power to trade."
when_to_use: "Use when assessing whether a predictive signal is worth trading"
dependencies: []
metadata:
  book_chapters: "7, 8"
  library: "ml4t-diagnostic"
paths: ["**/*cv*.py", "**/*valid*.py", "**/*eval*.py", "**/*drift*.py", "**/*sharpe*.py", "**/*shap*.py", "**/*stationar*.py", "**/*purge*.py", "**/*embargo*.py", "**/*walk_forward*.py"]
---
# Factor Evaluation

A factor that looks predictive may be untradeable due to high turnover, rapid decay, or non-monotonic quantile spreads. Comprehensive evaluation before portfolio integration prevents costly live failures.

## The Problem

Reporting a single backtest Sharpe ratio conflates signal quality with portfolio construction. A factor with IC 0.03 and low turnover can be more valuable than one with IC 0.05 and 80% daily turnover — whether IC is sufficient depends on breadth, turnover costs, and regime stability. Without decomposing signal quality into IC, quantile monotonicity, turnover, and decay, you cannot diagnose why a strategy fails or how to improve it.

## The Pattern

### WRONG

```python
# Evaluate only via backtest Sharpe — hides factor-level issues
returns = run_backtest(signal)
sharpe = returns.mean() / returns.std() * np.sqrt(252)
print(f"Sharpe: {sharpe:.2f}")  # No idea why it works or doesn't
```

### CORRECT

```python
import numpy as np
from scipy import stats

# 1. Information Coefficient: rank correlation with forward returns
def compute_ic_series(signal, forward_returns, timestamps):
    """Per-period rank IC between signal and forward returns."""
    ic_by_period = []
    for t in np.unique(timestamps):
        mask = timestamps == t
        if mask.sum() < 10:
            continue
        ic, _ = stats.spearmanr(signal[mask], forward_returns[mask])
        ic_by_period.append(ic)
    return np.array(ic_by_period)

ic_series = compute_ic_series(signal, fwd_ret, dates)
print(f"IC Mean: {np.mean(ic_series):.4f}")
print(f"IC Std:  {np.std(ic_series):.4f}")
print(f"IC IR:   {np.mean(ic_series) / np.std(ic_series):.3f}")
print(f"IC t-stat: {np.mean(ic_series) / (np.std(ic_series) / np.sqrt(len(ic_series))):.2f}")

# 2. Quantile spreads: returns by signal quintile
n_quantiles = 5
quantile_labels = np.ceil(stats.rankdata(signal) / len(signal) * n_quantiles)
for q in range(1, n_quantiles + 1):
    q_ret = fwd_ret[quantile_labels == q].mean()
    print(f"  Q{q}: {q_ret:.4f}")
# Good factor: monotonic Q1 < Q2 < ... < Q5 (or reverse)

# 3. Turnover: how often positions change
quantiles_today = np.ceil(stats.rankdata(signal_today) / len(signal_today) * 5)
quantiles_yesterday = np.ceil(stats.rankdata(signal_yesterday) / len(signal_yesterday) * 5)
turnover = (quantiles_today != quantiles_yesterday).mean()
print(f"Turnover: {turnover:.1%}")
```

## IC Decay Analysis

Signal power fades over time. Measure IC at multiple horizons to find optimal rebalance frequency:

```python
for horizon in [1, 5, 10, 21, 63]:
    fwd = returns.shift(-horizon)
    ic = stats.spearmanr(signal[~np.isnan(fwd)], fwd[~np.isnan(fwd)])[0]
    print(f"  {horizon:>3}d IC: {ic:.4f}")
# IC peaks at the natural signal horizon; decays beyond it
```

## Guardrails

- IC alone is insufficient — a factor with high IC but non-monotonic quintiles is unreliable
- High turnover (>30% daily) signals that transaction costs may consume the alpha
- Always compute t-statistics with HAC (Newey-West) standard errors for autocorrelated IC series
- Decay analysis determines rebalance frequency — rebalancing faster than the peak-IC horizon wastes costs
- IC is a learnability screen, not a strategy — a positive IC only means the signal has information; tradability requires checking turnover, costs, and capacity

## Production Implementation

`ml4t-diagnostic` provides validated IC computation with HAC corrections:

```python
from ml4t.diagnostic.api import compute_ic_hac_stats, cross_sectional_ic_series

ic_series = cross_sectional_ic_series(
    signal_frame,
    return_frame,
    pred_col="signal",
    ret_col="forward_return",
    date_col="date",
    entity_col="symbol",
)
ic_stats = compute_ic_hac_stats(ic_series)  # Newey-West corrected
print(f"IC: {ic_stats['mean_ic']:.4f} (t={ic_stats['t_stat']:.2f})")
```

## Checklist

- [ ] IC mean, IC IR, and worst-fold IC computed (IC IR > 0.5; worst-fold IC same sign as mean)
- [ ] Quantile returns checked for monotonicity
- [ ] Turnover estimated and compared against cost model
- [ ] Decay analysis performed to determine rebalance frequency
- [ ] t-statistics use HAC standard errors, not naive SE
