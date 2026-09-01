---
name: ml4t-position-sizing
description: "Convert signals to position sizes using volatility targeting and risk budgets. Use when scaling trade size relative to conviction and portfolio risk."
when_to_use: "Use when sizing positions from model predictions or alpha signals"
dependencies: [transaction-costs]
metadata:
  book_chapters: "17"
  library: "ml4t-backtest"
paths: ["**/*portfolio*.py", "**/*position*.py", "**/*risk*.py", "**/*optim*.py", "**/*exposure*.py", "**/*kill*.py", "**/*stress*.py"]
---
# Position Sizing

Equal-weight portfolios ignore that a 1% position in a 40-vol crypto asset carries 8x the risk of a 1% position in a 5-vol bond ETF. Without volatility-aware sizing, portfolio risk is dominated by the noisiest assets.

## The Problem

Signal-based strategies produce alpha scores, but scores are not position sizes. Naively allocating equal weight to every signal treats all assets as interchangeable. The result: a few high-volatility names drive total portfolio variance, drowning out the diversified signal you worked to build. Volatility targeting fixes this by scaling each position inversely to its risk.

## The Pattern

### WRONG
```python
import numpy as np

# Equal weight: ignores that BTC vol >> SPY vol
signals = np.array([0.8, 0.6, 0.3, -0.5])
weights = signals / np.abs(signals).sum()  # [-0.36, 0.27, 0.14, -0.23]
# BTC at 40% vol gets same weight as SPY at 15% vol
```

### CORRECT
```python
import numpy as np

signals = np.array([0.8, 0.6, 0.3, -0.5])
realized_vol = np.array([0.40, 0.25, 0.15, 0.10])  # annualized
target_vol = 0.10  # 10% portfolio vol target

# Step 1: signal-proportional base weights
base = signals / np.abs(signals).sum()

# Step 2: scale each position by inverse volatility
vol_scalar = np.clip(target_vol / realized_vol, 0.5, 2.0)
raw = base * vol_scalar

# Step 3: enforce leverage constraint
max_leverage = 1.5
leverage = np.abs(raw).sum()
weights = raw * min(1.0, max_leverage / leverage)
```

## Methods at a Glance

| Method | Formula | When to Use |
|--------|---------|-------------|
| Equal weight | 1/N | Baseline only |
| Signal-proportional | signal / sum(\|signal\|) | When signals are well-calibrated |
| Vol-targeted | base * (target_vol / asset_vol) | Default for most strategies |
| Kelly | excess_return / variance | Theoretical bound; use half-Kelly |
| Risk budget | target_risk / portfolio_risk | Full portfolio vol targeting |

## Half-Kelly Sizing

```python
def half_kelly(expected_excess: float, volatility: float) -> float:
    """Half-Kelly is the practical ceiling for position size."""
    full_kelly = expected_excess / (volatility ** 2)
    return full_kelly / 2  # halve to reduce variance of growth rate
```

Full Kelly maximizes long-run growth but has extreme variance. Half-Kelly sacrifices ~25% of growth for ~50% less variance in outcomes.

## Guardrails

- Never use full Kelly in production - half or quarter Kelly reduces ruin probability dramatically
- Smooth volatility estimates with EWMA (halflife 20-60 days) - point estimates are noisy
- Cap individual position size (e.g., 10% of NAV) regardless of signal strength
- Recheck leverage after all position adjustments - constraint order matters

## Production Implementation

`ml4t-backtest` handles position sizing inside the execution loop:

```python
from ml4t.backtest import TargetWeightExecutor, RebalanceConfig

executor = TargetWeightExecutor(
    config=RebalanceConfig(
        max_single_weight=0.10,
        max_gross_leverage=1.5,
        min_weight_change=0.01,
    ),
)
orders = executor.execute(target_weights, data, broker)
```

## Checklist

- [ ] Positions scaled by inverse volatility (not equal-weighted)
- [ ] Leverage cap enforced after all sizing adjustments
- [ ] Individual position limits set (max 5-10% of NAV)
- [ ] Volatility estimates smoothed (EWMA, not point-in-time)
- [ ] Kelly fraction halved or quartered if used
