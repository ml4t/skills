---
name: ml4t-transaction-costs
description: Model trading costs (spread, slippage, impact) for realistic backtests
category: concepts
type: conceptual
dependencies: []
book_chapters: [11, 17]
quantlab_module: ml4t.backtest.costs
---

# Transaction Costs

Trading costs determine whether a strategy works in practice.

## Cost Stack

| Component | Type | Typical Size |
|-----------|------|--------------|
| Commission | Explicit | 0-5 bps |
| Bid-ask spread | Implicit | 1-50 bps |
| Slippage | Implicit | 1-10 bps |
| Market impact | Implicit | 5-100+ bps |
| Funding/borrow | Explicit | Variable |

## Models

```python
from ml4t.backtest.costs import CostModel

# Simple: fixed percentage
costs = CostModel(
    commission_bps=1,
    spread_bps=5,
    slippage_bps=2
)

# Volume-dependent impact
costs = CostModel(
    commission_bps=1,
    spread_bps=5,
    impact_model='square_root',  # impact ∝ sqrt(volume/ADV)
    impact_coefficient=0.1
)
```

## Impact Models

| Model | Formula | Use Case |
|-------|---------|----------|
| Linear | impact = k * (size / ADV) | Small orders |
| Square-root | impact = k * sqrt(size / ADV) | Standard |
| 3/2 power | impact = k * (size / ADV)^1.5 | Large orders |

## Safety Margin

```python
# Gross alpha must exceed costs by margin
gross_alpha_bps = 50
round_trip_cost = 20  # bps
safety_margin = gross_alpha_bps / round_trip_cost

# Target: safety_margin >= 2.5x
```

## Rules

```python
# WRONG: Ignore costs
returns = positions.shift(1) * forward_returns

# WRONG: Assume fixed costs
costs = 0.001 * abs(position_changes)

# CORRECT: Volume-dependent impact
turnover = abs(position_changes)
adv = volume.rolling(20).mean()
impact = 0.1 * np.sqrt(turnover / adv) * volatility
costs = spread + slippage + impact
```

## Capacity

```python
# Maximum AUM before impact destroys alpha
# Rule of thumb: trade < 5% of ADV
max_aum = 0.05 * universe_adv.sum() * (1 / turnover_rate)
```

## Guardrails

- Always include spread (minimum cost)
- Use volume-dependent impact for realistic simulation
- Higher turnover = higher sensitivity to cost assumptions
- Validate cost model with TCA data when available

## Checklist

- [ ] All cost components modeled
- [ ] Impact scales with volume
- [ ] Safety margin >= 2.5x documented
- [ ] Capacity constraints calculated
- [ ] Sensitivity analysis on cost assumptions
