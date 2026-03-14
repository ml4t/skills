---
name: ml4t-cost-model
description: Model all trading costs — commission, spread, slippage, market impact. Use when estimating net performance and strategy capacity.
dependencies: [run-backtest]
metadata:
  book_chapters: "18"
  library: "ml4t-backtest"
---

# Transaction Cost Modeling

A strategy with zero-cost Sharpe of 1.5 may have net Sharpe of 0.3. Trading costs are not a detail — they are the primary constraint on whether alpha survives. Every backtest must include commission, spread, slippage, and (for larger size) market impact.

## The Problem

Zero-cost backtests overstate performance by the full round-trip cost times turnover. A strategy trading 200% annual turnover at 20 bps round-trip loses 40 bps/year to costs alone. For high-frequency or small-cap strategies, costs can exceed gross alpha entirely. Without a cost model, you cannot estimate capacity — the AUM where costs eat all profit.

## The Pattern

### WRONG
```python
import numpy as np

# Zero-cost backtest — fiction
positions = compute_positions(signals)
gross_returns = positions * asset_returns
sharpe = gross_returns.mean() / gross_returns.std() * np.sqrt(252)  # overstated
```

### CORRECT
```python
import numpy as np

def net_returns_with_costs(
    positions: np.ndarray,
    asset_returns: np.ndarray,
    prices: np.ndarray,
    volume: np.ndarray,
    commission_bps: float = 1.0,
    spread_bps: float = 5.0,
    impact_coeff: float = 0.1,
) -> np.ndarray:
    """Compute net returns with multi-component cost model."""
    gross = positions * asset_returns
    trades = np.abs(np.diff(positions, prepend=0))

    # Fixed costs: commission + half-spread per side
    fixed_cost = trades * (commission_bps + spread_bps / 2) / 10_000

    # Market impact: square-root model, scales with participation rate
    participation = np.where(volume > 0, trades * prices / volume, 0)
    impact = impact_coeff * np.sqrt(np.clip(participation, 0, 1))

    return gross - fixed_cost - impact


# Capacity: AUM where net Sharpe = 0.5 (minimum viable)
def estimate_capacity(gross_sharpe, turnover, cost_bps_per_turn):
    """Rough capacity = AUM where costs consume alpha down to threshold."""
    alpha_bps = gross_sharpe * 100 / np.sqrt(252)  # daily alpha in bps (approx)
    cost_drag = turnover * cost_bps_per_turn / 252
    # Capacity is limited by market impact scaling — not a fixed formula
    return f"Gross alpha ~{alpha_bps:.1f} bps/day, cost drag ~{cost_drag:.1f} bps/day"
```

## Cost Components

| Component | Typical Range | Scales With |
|-----------|--------------|-------------|
| Commission | 0.5 - 10 bps | Trade count |
| Spread | 1 - 50 bps | Asset liquidity |
| Slippage | 1 - 20 bps | Order urgency |
| Market impact | 5 - 100+ bps | Order size / ADV |

**Impact model**: $\text{impact} = \eta \cdot \sigma \cdot \sqrt{\frac{Q}{\text{ADV}}}$ where $Q$ is order size, $\sigma$ is daily volatility, $\eta$ is a calibration constant (typically 0.05-0.3).

## Guardrails

- A strategy where net Sharpe < 0.5 after realistic costs is not tradeable
- Impact grows with the square root of participation rate — doubling AUM does not double cost
- Use asset-class appropriate estimates: crypto spread is 5-50 bps, US large-cap is 1-3 bps
- Validate cost assumptions against actual fill data (TCA) when available

## Production Implementation

`ml4t-backtest` provides composable cost models:

```python
from ml4t.backtest import BacktestConfig
from ml4t.backtest.models import PercentageCommission, VolumeShareSlippage

config = BacktestConfig(
    commission=PercentageCommission(0.001),       # 10 bps
    slippage=VolumeShareSlippage(0.1),            # volume-dependent
)
# Engine deducts costs per fill automatically
```

## Checklist

- [ ] Commission, spread, and slippage all included (not just one)
- [ ] Market impact modeled for order sizes > 1% ADV
- [ ] Cost assumptions match asset class (not a single number for everything)
- [ ] Net Sharpe reported alongside gross Sharpe
- [ ] Capacity estimate computed (AUM where net Sharpe drops below threshold)
