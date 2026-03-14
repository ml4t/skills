---
name: ml4t-run-backtest
description: Event-driven backtesting with realistic execution modeling
category: backtest
type: operational
dependencies: [transaction-costs]
book_chapters: [17]
quantlab_module: ml4t.backtest
---

# Run Backtest

Event-driven backtesting with execution modeling.

## Strategy Class

```python
from ml4t.backtest.strategy import Strategy

class MyStrategy(Strategy):
    def on_data(self, timestamp, data, context, broker):
        # data: {"SPY": {"open": 100, "close": 101, ...}}
        if self.should_buy(data):
            broker.submit_order("SPY", 100, OrderType.MARKET)

    def on_start(self, broker):
        pass  # Initialize

    def on_end(self, broker):
        pass  # Cleanup
```

## Broker API

```python
from ml4t.backtest import Broker
from ml4t.backtest.types import ExecutionMode, OrderType, OrderSide

broker = Broker(
    initial_cash=100_000,
    commission_model=PerShareCommission(0.01),
    slippage_model=PercentageSlippage(0.001),
    execution_mode=ExecutionMode.NEXT_BAR_OPEN,
    account_type="cash"  # or "margin"
)

# Order methods
broker.submit_order(symbol, quantity, order_type)
broker.get_position(symbol) -> Position
broker.close_position(symbol)
broker.cancel_order(order_id)
```

## Execution Modes

| Mode | Description |
|------|-------------|
| `SAME_BAR` | Fill at current bar (optimistic) |
| `NEXT_BAR_OPEN` | Fill at next bar open (realistic) |
| `NEXT_BAR_CLOSE` | Fill at next bar close |

## Commission Models

```python
from ml4t.backtest.models import (
    NoCommission,
    PerShareCommission,      # $0.01/share
    PercentageCommission,    # 0.1% of value
    TieredCommission
)
```

## Slippage Models

```python
from ml4t.backtest.models import (
    NoSlippage,
    FixedSlippage,           # Fixed $ per share
    PercentageSlippage,      # % of price
    LinearImpactSlippage     # Scales with size
)
```

## Guardrails

- Use `NEXT_BAR_OPEN` for realistic results
- Always include commission and slippage
- Verify position sizing respects buying power
- Check `broker.account.equity` for current value
