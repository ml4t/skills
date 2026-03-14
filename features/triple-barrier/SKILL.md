---
name: ml4t-triple-barrier
description: Label trades using profit-target, stop-loss, and time barriers with volatility-adaptive thresholds. Use when building labels for supervised learning on trade outcomes.
dependencies: [lookahead-bias]
metadata:
  book_chapters: "7"
  library: "ml4t-engineer"
---

# Triple-Barrier Labeling

Fixed return thresholds ignore volatility — a 2% move is noise in crypto but a signal in treasuries. Triple-barrier labels adapt to the asset's current regime.

## The Problem

Naive binary labels (`return > 0`) are noisy and ignore position management. A trade that gains 5% then gives back 8% is labeled "winning" if you only check the endpoint. Triple-barrier labeling mirrors real trading: you exit when you hit a profit target, a stop loss, or time runs out.

## The Pattern

### WRONG
```python
import numpy as np

# Fixed threshold ignores volatility regime
labels = np.where(fwd_returns > 0.02, 1, np.where(fwd_returns < -0.01, -1, 0))
```

### CORRECT
```python
import numpy as np
import polars as pl

def triple_barrier_labels(
    prices: np.ndarray,
    upper_mult: float = 2.0,
    lower_mult: float = 1.5,
    atr_period: int = 14,
    max_holding: int = 10,
) -> np.ndarray:
    """Label each bar: +1 profit hit, -1 stop hit, 0 time expiry."""
    # Volatility-adaptive barriers via ATR
    high_low = np.abs(np.diff(prices, prepend=prices[0]))
    atr = np.convolve(high_low, np.ones(atr_period) / atr_period, mode="same")

    labels = np.zeros(len(prices))
    for i in range(len(prices) - max_holding):
        upper = prices[i] + atr[i] * upper_mult
        lower = prices[i] - atr[i] * lower_mult
        for j in range(1, max_holding + 1):
            if prices[i + j] >= upper:
                labels[i] = 1; break
            elif prices[i + j] <= lower:
                labels[i] = -1; break
        # else: labels[i] stays 0 (time expiry)
    return labels
```

## Barrier Calibration

| Symptom | Cause | Fix |
|---------|-------|-----|
| 90%+ stops hit | Barriers too tight | Widen lower_mult |
| 90%+ time expiry | Barriers too wide | Tighten multipliers or shorten max_holding |
| Label imbalance >3:1 | Asymmetric barriers | Adjust upper/lower ratio |

The ATR multiplier controls barrier width relative to current volatility. Typical ranges: upper 1.5-3.0x, lower 1.0-2.0x.

## Guardrails

- **Purging required**: CV must purge `max_holding_period` bars around test boundaries to prevent leakage
- **Class balance**: check label distribution — use class weights if imbalanced beyond 3:1
- **ATR lookback**: must use only past data; `atr[i]` must not include bar `i+1`

## Production Implementation

`ml4t-engineer` provides a validated, vectorized implementation:

```python
from ml4t.engineer.labeling import triple_barrier
from ml4t.engineer.labeling.barriers import ATRBarrierConfig

config = ATRBarrierConfig(
    upper_multiplier=2.0, lower_multiplier=1.5,
    atr_period=14, max_holding_period=10,
)
labels = triple_barrier(prices=df, config=config, price_col="close")
# Returns: label, exit_time, holding_period, return
```

## Checklist

- [ ] Barriers are volatility-adaptive (ATR or realized vol), not fixed thresholds
- [ ] `max_holding_period` matches CV purge window (`label_horizon`)
- [ ] Label distribution checked — no single class >80%
- [ ] ATR computed from past data only (no lookahead)
- [ ] Short-side labels handled correctly if strategy is long/short
