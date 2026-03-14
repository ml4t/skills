---
name: ml4t-transaction-costs
description: Model spread, slippage, and market impact for realistic strategy simulation. Use when building backtests, sizing positions, or estimating strategy capacity.
dependencies: []
metadata:
  book_chapters: "6, 18"
  library: "ml4t-backtest"
---

# Transaction Costs

A strategy that ignores trading costs can show positive alpha that disappears entirely when realistic friction is applied. Costs are the single largest gap between backtested and live performance.

## The Problem

The full cost of a trade has three layers: explicit costs (commissions, fees), implicit costs (half the bid-ask spread paid on every execution), and market impact (your own order moving the price against you). Most amateur backtests model only commissions or use a flat basis-point assumption. This misses the volume-dependent nature of market impact, which is the dominant cost for any strategy trading more than trivial size.

A strategy with 50 bps gross alpha and 30 bps round-trip costs has a safety margin of only 1.7x -- too thin to survive estimation error.

## The Pattern

### WRONG

```python
import numpy as np

# Flat cost assumption -- ignores volume dependence
weights = compute_target_weights(signals)
turnover = np.abs(weights - prev_weights).sum()
costs = turnover * 0.001  # 10 bps flat -- wrong for large trades
net_return = gross_return - costs
```

### CORRECT

```python
import numpy as np

weights = compute_target_weights(signals)
turnover = np.abs(weights - prev_weights)

# Volume-dependent square-root impact model
adv = volume_20d_mean                       # 20-day average daily volume ($)
participation = (turnover * portfolio_aum) / adv
spread_cost = half_spread                   # ~2-5 bps for liquid equities
impact_cost = 0.1 * np.sqrt(participation)  # Almgren-Chriss square-root model
total_cost = spread_cost + impact_cost      # per-asset, per-rebalance

net_return = gross_return - (turnover * total_cost).sum()
```

## Cost Stack

| Component | Type | Typical range | Scales with |
|-----------|------|---------------|-------------|
| Commission | Explicit | 0--5 bps | Trade count |
| Bid-ask spread | Implicit | 1--50 bps | Asset liquidity |
| Slippage | Implicit | 1--10 bps | Order urgency |
| Market impact | Implicit | 5--100+ bps | Trade size / ADV |
| Funding / borrow | Explicit | Variable | Short position size |

## Safety Margin Rule

```python
gross_alpha_bps = 50
round_trip_cost_bps = 20
safety_margin = gross_alpha_bps / round_trip_cost_bps  # 2.5x

# Target: safety_margin >= 2.5x
# Below 2.0x: strategy is fragile to cost estimation error
# Below 1.5x: likely unprofitable in practice
```

## Capacity Estimation

```python
import numpy as np

# Maximum AUM before impact erodes alpha
universe_adv = adv_per_asset.sum()      # total $ ADV across universe
turnover_rate = 0.20                     # 20% monthly turnover
max_participation = 0.05                 # trade < 5% of ADV

capacity = max_participation * universe_adv / turnover_rate
print(f"Estimated capacity: ${capacity/1e6:.0f}M")
```

## Guardrails

- Never backtest without at least spread costs -- it is the irreducible minimum.
- Flat bps assumptions are only valid for very small portfolios trading liquid names.
- Higher turnover amplifies cost sensitivity -- a 2x turnover increase can 4x the impact cost (square-root model).
- Validate cost model against Transaction Cost Analysis (TCA) data when available.
- Crypto and options have much wider spreads than equities -- use asset-class-specific estimates.

## Production Implementation

`ml4t-backtest` provides composable commission and slippage models:

```python
from ml4t.backtest import BacktestConfig, run_backtest
from ml4t.backtest.models import PercentageCommission, VolumeShareSlippage

config = BacktestConfig(
    commission=PercentageCommission(rate=0.0001),  # 1 bp
    slippage=VolumeShareSlippage(impact_factor=0.1),
)
result = run_backtest(strategy, data, config=config)
```

## Checklist

- [ ] All three cost layers modeled (commission, spread, impact)
- [ ] Market impact scales with trade size relative to ADV (not flat bps)
- [ ] Safety margin >= 2.5x documented (gross alpha / costs)
- [ ] Strategy capacity estimated with participation rate constraint
- [ ] Sensitivity analysis: results reported at 1x, 2x, and 3x base cost assumptions
