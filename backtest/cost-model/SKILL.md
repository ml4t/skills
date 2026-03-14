---
name: ml4t-cost-model
description: Configure realistic transaction cost models
category: backtest
type: operational
dependencies: [transaction-costs, run-backtest]
book_chapters: [11, 17]
quantlab_module: ml4t.backtest.costs
---

# Cost Model

Realistic transaction cost modeling for backtests.

## API

```python
from ml4t.backtest.costs import CostModel, ImpactModel

# Simple fixed costs
costs = CostModel(
    commission_bps=1.0,
    spread_bps=5.0,
    slippage_bps=2.0
)

# Volume-dependent impact
costs = CostModel(
    commission_bps=1.0,
    spread_bps=5.0,
    impact=ImpactModel(
        model='square_root',
        coefficient=0.1,
        volatility_scaling=True
    )
)
```

## Impact Models

```python
class ImpactModel:
    """Market impact as function of order size."""

    def calculate(self, size: float, adv: float, volatility: float) -> float:
        participation = size / adv

        if self.model == 'linear':
            impact = self.coefficient * participation
        elif self.model == 'square_root':
            impact = self.coefficient * np.sqrt(participation)
        elif self.model == 'power':
            impact = self.coefficient * participation ** 1.5

        if self.volatility_scaling:
            impact *= volatility / 0.01  # Normalize to 1% daily vol

        return impact
```

## Cost Configuration by Asset

```python
COST_PRESETS = {
    'us_large_cap': CostModel(
        commission_bps=0.5,
        spread_bps=2.0,
        impact=ImpactModel('square_root', 0.1)
    ),
    'us_small_cap': CostModel(
        commission_bps=1.0,
        spread_bps=10.0,
        impact=ImpactModel('square_root', 0.3)
    ),
    'crypto_spot': CostModel(
        commission_bps=10.0,  # Maker fee
        spread_bps=5.0,
        impact=ImpactModel('square_root', 0.2)
    ),
    'futures': CostModel(
        commission_bps=0.5,
        spread_bps=0.5,
        impact=ImpactModel('linear', 0.05)
    )
}
```

## Per-Trade Cost

```python
def trade_cost(
    order_value: float,
    adv: float,
    volatility: float,
    model: CostModel
) -> float:
    """Calculate total cost for a trade."""
    # Fixed costs
    fixed = (model.commission_bps + model.spread_bps) / 10000

    # Variable impact
    impact = model.impact.calculate(
        size=order_value,
        adv=adv,
        volatility=volatility
    )

    return order_value * (fixed + impact)
```

## Guardrails

- Use asset-class appropriate presets
- Impact scales with order size relative to ADV
- Higher volatility = higher impact
- Always validate with TCA when available

## Checklist

- [ ] Asset-class specific costs
- [ ] Impact model configured
- [ ] ADV and volatility inputs available
- [ ] Costs validated vs actual fills (if available)
