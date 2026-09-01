---
name: ml4t-horizon-design
description: "Choose prediction horizon by analyzing IC decay, turnover cost, and feature-horizon alignment. Use when determining the optimal lookahead window for labels."
when_to_use: "Use when designing labels or deciding rebalancing frequency for a trading strategy"
dependencies: [triple-barrier]
metadata:
  book_chapters: "7"
  library: "ml4t-diagnostic"
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
---
# Horizon Design

An arbitrary 1-day horizon forces daily rebalancing, which costs 2-5% annually in transaction costs. If the signal's IC peaks at 20 days, you are paying for turnover that destroys the edge.

## The Problem

The prediction horizon determines everything downstream: label construction, feature relevance, turnover, and whether transaction costs leave any alpha. Choosing it arbitrarily - or defaulting to "1 day because that is what everyone uses" - misaligns the model with the actual signal dynamics.

## The Pattern

### WRONG
```python
import numpy as np

# Arbitrary 1-day horizon - no evidence this matches the signal
labels = np.roll(returns, -1)  # forward 1-day return as label
# Result: high turnover, transaction costs eat the edge
```

### CORRECT
```python
from scipy.stats import spearmanr
import numpy as np

def find_optimal_horizon(
    signal: np.ndarray, returns: np.ndarray, horizons: list[int] = None,
) -> dict:
    """Analyze IC decay to find the horizon where the signal is strongest."""
    if horizons is None:
        horizons = [1, 2, 5, 10, 20, 40, 60]

    results = {}
    for h in horizons:
        fwd_ret = np.full_like(returns, np.nan)
        fwd_ret[:-h] = np.sum(
            [np.roll(returns, -i) for i in range(1, h + 1)], axis=0
        )[:-h]
        valid = ~np.isnan(signal) & ~np.isnan(fwd_ret)
        ic, _ = spearmanr(signal[valid], fwd_ret[valid])
        results[h] = ic

    optimal = max(results, key=lambda k: abs(results[k]))
    return {"ic_by_horizon": results, "optimal_horizon": optimal}
```

## IC Decay Profile

| Horizon | Typical IC | Interpretation |
|---------|-----------|----------------|
| 1d | 0.01 | Too noisy, costs dominate |
| 5d | 0.03 | Building strength |
| 20d | 0.05 | **Peak - optimal horizon** |
| 40d | 0.03 | Decaying |
| 60d | 0.01 | Signal exhausted |

## Transaction Cost Constraint

```python
def min_viable_horizon(cost_per_trade: float, annual_alpha: float) -> int:
    """Shortest horizon where alpha covers costs."""
    for h in [1, 2, 5, 10, 20, 40, 60]:
        trades_per_year = 252 / h
        alpha_per_trade = annual_alpha / trades_per_year
        if alpha_per_trade > cost_per_trade * 2.5:  # 2.5x safety margin
            return h
    return 60  # Default to low-frequency if costs are high
```

## Feature-Horizon Alignment

```python
# Misaligned: 5-day feature predicting 60-day returns
feature = returns_5d
label = fwd_returns_60d

# Aligned: 60-day feature predicting 60-day returns
feature = returns_60d
label = fwd_returns_60d
```

## Guardrails

- **Never default to 1-day** without IC decay analysis - most alpha signals peak at 5-20 days
- **Transaction costs are the binding constraint** - a 5-day signal with 10 bps costs beats a 1-day signal with the same IC
- **Feature lookback should match horizon** within a factor of 2-3x

## Production Implementation

```python
from ml4t.diagnostic.metrics import compute_ic_by_horizon

ic_by_horizon = compute_ic_by_horizon(
    predictions=prediction_frame,
    prices=price_frame,
    horizons=[1, 5, 10, 20, 60],
    pred_col="prediction",
    price_col="close",
    date_col="date",
    group_col="symbol",
)
print(ic_by_horizon)
```

## Checklist

- [ ] IC decay analysis run across at least 5 horizons (1d, 5d, 10d, 20d, 60d)
- [ ] Optimal horizon identified as the peak of |IC| vs horizon
- [ ] Transaction costs modeled - alpha per trade exceeds cost by at least 2.5x
- [ ] Feature lookback windows aligned with chosen horizon
- [ ] Rebalancing frequency matches horizon (not more frequent)
