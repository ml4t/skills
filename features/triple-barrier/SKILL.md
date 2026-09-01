---
name: ml4t-triple-barrier
description: "Label trades using profit-target, stop-loss, and time barriers with volatility-adaptive thresholds. Use when creating supervised labels for financial time series."
when_to_use: "Use when building labels for supervised learning on trade outcomes"
dependencies: [lookahead-bias]
metadata:
  book_chapters: "7"
  library: "ml4t-engineer"
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
---
# Triple-Barrier Labeling

Fixed return thresholds ignore volatility - a 2% move is noise in crypto but a signal in treasuries. Triple-barrier labels adapt to the asset's current regime.

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

def triple_barrier_labels(
    prices: np.ndarray,
    upper_mult: float = 2.0,
    lower_mult: float = 1.5,
    atr_period: int = 14,
    max_holding: int = 10,
) -> np.ndarray:
    """Label each bar: +1 profit hit, -1 stop hit, 0 time expiry."""
    # Volatility-adaptive barriers via a TRAILING mean of absolute price changes.
    # mode="same" would centre the window and let atr[i] see bars after i.
    abs_changes = np.abs(np.diff(prices, prepend=prices[0]))
    atr = np.convolve(abs_changes, np.ones(atr_period) / atr_period)[: len(prices)]

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

The ATR multiplier controls barrier width relative to current volatility. Typical ranges: upper 1.5-3.0x, lower 1.0-2.0x. De Prado's original uses EWMA daily vol; ATR is a practical alternative that captures intraday range.

**MFE/MAE diagnostics**: Plot Maximum Favorable Excursion (best unrealized P&L) and Maximum Adverse Excursion (worst drawdown) for each trade to calibrate barriers empirically - barriers should sit at natural break points in the MFE/MAE distributions.

## Guardrails

- **Purging required**: CV must purge `max_holding_period` bars around test boundaries to prevent leakage
- **Label overlap**: labels with overlapping holding periods are not IID - effective sample size is ~N/H where H is holding period. Use sample uniqueness weighting or sequential bootstrap
- **Class balance**: check label distribution - use class weights if imbalanced beyond 3:1
- **ATR lookback**: must use only past data; `atr[i]` must not include bar `i+1`
- **Tie-breaking**: when both barriers are crossed in the same bar, define a resolution rule (e.g., stop-loss takes priority)

## Production Implementation

`ml4t-engineer` provides a validated, vectorized implementation:

```python
from ml4t.engineer.config import LabelingConfig
from ml4t.engineer.labeling import atr_triple_barrier_labels

config = LabelingConfig.atr_barrier(
    atr_tp_multiple=2.0,
    atr_sl_multiple=1.5,
    atr_period=14,
    max_holding_period=10,
)
labels = atr_triple_barrier_labels(
    df,
    config=config,
    price_col="close",
    timestamp_col="timestamp",
)
# Returns: label, label_time, label_bars, label_return
```

## Checklist

- [ ] Barriers are volatility-adaptive (ATR or realized vol), not fixed thresholds
- [ ] `max_holding_period` matches CV purge window (`label_horizon`)
- [ ] Label distribution checked - no single class >80%
- [ ] ATR computed from past data only (no lookahead)
- [ ] Short-side labels handled correctly if strategy is long/short
