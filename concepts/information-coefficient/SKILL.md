---
name: ml4t-information-coefficient
description: "Measure predictive signal quality with IC, Rank IC, and IC_IR. Use when evaluating whether a feature has predictive power for returns."
when_to_use: "Use when evaluating alpha signals, comparing features, or connecting signal strength to portfolio performance via the Fundamental Law"
dependencies: []
metadata:
  book_chapters: "7, 8"
  library: "ml4t-diagnostic"
---
# Information Coefficient

IC is the correlation between a predicted signal and realized returns. It is the primary metric for judging whether a signal has predictive power before building a full backtest.

## The Problem

Reporting a single IC value (or worse, the best IC from many trials) tells you almost nothing. IC varies over time and across market regimes. A signal with mean IC = 0.04 and std = 0.02 (IC_IR = 2.0) is far more valuable than one with mean IC = 0.08 and std = 0.10 (IC_IR = 0.8). Without time-series statistics and proper standard errors, you cannot distinguish a real signal from noise.

## The Pattern

### WRONG

```python
from scipy.stats import spearmanr

# Single pooled IC -- hides time variation, inflates significance
ic, pval = spearmanr(all_predictions.flatten(), all_returns.flatten())
print(f"IC = {ic:.4f}, p = {pval:.4f}")
```

### CORRECT

```python
import numpy as np
from scipy.stats import spearmanr
from statsmodels.stats.stattools import durbin_watson

# Cross-sectional IC per period
ic_series = []
for t in timestamps:
    mask = dates == t
    if mask.sum() >= 10:
        ic, _ = spearmanr(predictions[mask], returns[mask])
        ic_series.append(ic)

ic_series = np.array(ic_series)
ic_mean = ic_series.mean()
ic_std = ic_series.std()
ic_ir = ic_mean / ic_std

# Newey-West HAC standard error for significance
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
ols = OLS(ic_series, add_constant(np.ones(len(ic_series)))).fit(
    cov_type="HAC", cov_kwds={"maxlags": 5}
)
t_stat = ols.tvalues[0]

print(f"IC: {ic_mean:.4f}, IC_IR: {ic_ir:.2f}, t(HAC): {t_stat:.2f}")
```

## IC Interpretation

| IC range | Quality | Notes |
|----------|---------|-------|
| > 0.10 | Excellent | Rare; verify no leakage |
| 0.05 -- 0.10 | Good | Typical for strong factors |
| 0.02 -- 0.05 | Moderate | Profitable with enough breadth |
| < 0.02 | Weak | Needs very high capacity to matter |

## The Fundamental Law of Active Management

$$IR \approx IC \times \sqrt{BR}$$

Where IR is the information ratio and BR is breadth (independent bets per year). IC = 0.03 across 500 stocks rebalanced monthly: IR ≈ 0.03 × √6000 ≈ 2.3. Low IC is profitable with enough breadth.

## Overlap Inflation

Overlapping return labels (e.g., 21-day forward returns sampled daily) reduce effective sample size to ~N/H and inflate IC. A "significant" IC on 1,000 daily observations with H=21 overlap has only ~48 independent points. Always report IC_IR from non-overlapping periods or adjust standard errors for overlap.

## Guardrails

- Always use Rank IC (Spearman) for cross-sectional signals -- Pearson is sensitive to outliers.
- Report IC_IR (mean/std), not just mean IC -- consistency matters more than magnitude.
- Use HAC (Newey-West) standard errors, not naive t-tests -- IC series are autocorrelated.
- Plot IC over time: a decaying IC trend means the signal is crowding or the regime has changed.

## Production Implementation

`ml4t-diagnostic` provides IC computation with proper statistical testing:

```python
from ml4t.diagnostic.api import compute_ic_hac_stats, compute_ic_series

ic = compute_ic_series(
    predictions,
    returns,
    pred_col="prediction",
    ret_col="forward_return",
    date_col="date",
    entity_col="symbol",
    method="spearman",
)
stats = compute_ic_hac_stats(ic, maxlags=5)
# stats["mean_ic"], stats["t_stat"], stats["p_value"]
```

## Checklist

- [ ] IC computed per cross-section (not pooled across all dates)
- [ ] Rank IC (Spearman) used for cross-sectional signals
- [ ] IC_IR reported alongside mean IC
- [ ] Statistical significance tested with HAC standard errors (not naive t-test)
- [ ] IC decay by horizon plotted to confirm signal persistence
