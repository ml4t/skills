---
name: ml4t-cost-model
description: "Commission, slippage, and market-impact cost models for realistic strategy simulation. Use when backtesting to ensure P&L accounts for transaction costs."
when_to_use: "Use when wiring realistic execution costs into a simulation after a strategy has already cleared basic cost-feasibility screening"
dependencies: [transaction-costs]
metadata:
  book_chapters: "18"
  library: "ml4t-backtest"
paths: ["**/*backtest*.py", "**/*strategy*.py", "**/*engine*.py", "**/*broker*.py", "**/*cost*.py", "**/*regime*.py", "**/*tearsheet*.py"]
---
# Backtest Cost Model

Once a strategy passes the feasibility screen, the backtest engine still needs explicit cost settings. If commission, slippage, and impact are left at optimistic defaults, the simulation is still fiction.

## The Problem

Most mistakes at this stage are implementation mistakes: missing volume in the feed, flat slippage for every asset, or no participation cap on large orders. The result is a backtest that claims to include costs while still materially understating them.

## The Pattern

### WRONG
```python
import numpy as np

# Zero-cost backtest - fiction
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
    # Capacity is limited by market impact scaling - not a fixed formula
    return f"Gross alpha ~{alpha_bps:.1f} bps/day, cost drag ~{cost_drag:.1f} bps/day"
```

## Cost Components

| Component | Typical Range | Scales With |
|-----------|--------------|-------------|
| Commission | 0.5 - 10 bps | Trade count |
| Spread | 1 - 50 bps | Asset liquidity |
| Slippage | 1 - 20 bps | Order urgency |
| Market impact | 5 - 100+ bps | Order size / ADV |
| Financing | 25 - 300+ bps/yr | Short positions, leverage |

**Impact model**: $\text{impact} = \eta \cdot \sigma \cdot \sqrt{\frac{Q}{\text{ADV}}}$ where $Q$ is order size, $\sigma$ is daily volatility, $\eta$ is a calibration constant (typically 0.05-0.3).

## Guardrails

- Feed volume is required for volume-based slippage and participation limits
- Impact grows with the square root of participation rate - doubling AUM does not double cost
- Use asset-class appropriate estimates: crypto spread is 5-50 bps, US large-cap is 1-3 bps
- Short-side strategies must include borrow fees and financing - these can dominate total costs
- Validate cost assumptions against actual fill data (TCA) when available

## Production Implementation

`ml4t-backtest` provides composable cost models:

```python
from ml4t.backtest import BacktestConfig, CommissionType, DataFeed, Engine
from ml4t.backtest.config import SlippageType
from ml4t.backtest.execution.impact import SquareRootImpact
from ml4t.backtest.execution.limits import VolumeParticipationLimit

config = BacktestConfig(
    commission_type=CommissionType.PERCENTAGE,
    commission_rate=0.001,        # 10 bps
    slippage_type=SlippageType.VOLUME_BASED,
    slippage_rate=0.001,
)
engine = Engine(
    DataFeed(prices_df=prices),
    strategy,
    config,
    market_impact_model=SquareRootImpact(volatility=0.02),
    execution_limits=VolumeParticipationLimit(max_participation=0.10),
)
```

## Checklist

- [ ] Feed includes volume so impact and participation limits are meaningful
- [ ] Market impact modeled for order sizes > 1% ADV
- [ ] Cost assumptions match asset class (not a single number for everything)
- [ ] Zero-cost and cost-aware runs compared to quantify implementation drag
- [ ] TCA or broker fill data used to calibrate rates when available
