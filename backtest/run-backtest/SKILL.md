---
name: ml4t-run-backtest
description: "Event-driven backtesting with realistic order execution, position tracking, and performance measurement. Use when simulating a trading strategy on historical data."
when_to_use: "Use when simulating a strategy bar-by-bar with fills, positions, and costs"
dependencies: [cost-model]
metadata:
  book_chapters: "16"
  library: "ml4t-backtest"
paths: ["**/*backtest*.py", "**/*strategy*.py", "**/*engine*.py", "**/*broker*.py", "**/*cost*.py", "**/*regime*.py", "**/*tearsheet*.py"]
---
# Event-Driven Backtesting

Vectorized backtests hide execution reality. Event-driven simulation processes each bar sequentially, submitting orders that fill at future prices - the only way to model what actually happens when you trade.

## The Problem

Vectorized `positions * returns` backtests assume instant fills at known prices. In reality, you decide to trade on bar _t_ but fill at bar _t+1_. Ignoring this inflates Sharpe by 0.3-0.5 or more for daily strategies. The faster the signal, the larger the gap.

## The Pattern

### WRONG
```python
# Vectorized: signal and fill use the SAME bar's price
signals = compute_signal(prices)          # uses close[t]
positions = np.where(signals > 0, 1, 0)  # no shift!
returns = prices.pct_change()
strategy_returns = positions * returns    # lookahead: traded at price used to decide
sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
```

### CORRECT
```python
import numpy as np

def event_backtest(prices: np.ndarray, signal_fn, cost_bps: float = 10):
    """Minimal event-driven backtest: decide on bar t, fill on bar t+1."""
    n = len(prices)
    cash, shares = 100_000.0, 0
    equity = np.zeros(n)

    for t in range(1, n):
        # Fill yesterday's order at today's open
        target = signal_fn(prices[:t])  # can only see past
        current_shares = shares
        trade = target - current_shares
        if trade != 0:
            fill_price = prices[t]  # next bar (simulating open)
            cost = abs(trade * fill_price) * cost_bps / 10_000
            cash -= trade * fill_price + cost
            shares += trade
        equity[t] = cash + shares * prices[t]

    returns = np.diff(equity[1:]) / equity[1:-1]
    sharpe = returns.mean() / returns.std() * np.sqrt(252)
    return equity, sharpe
```

## Key Execution Rules

1. **Signal on bar _t_, fill on bar _t+1_** - never fill at the price you used to decide
2. **Track cash and positions explicitly** - position * price = equity, not magic
3. **Deduct costs per trade** - commission + spread + slippage on every fill
4. **No fractional knowledge** - `signal_fn(prices[:t])` sees only past bars

## Guardrails

- Fill at `SAME_BAR` close is optimistic - prefer next-bar open for daily strategies (close-to-open gap is 50-100 bps on equities)
- Any Sharpe above 2.0 on daily data warrants checking for fill-timing bugs
- Position sizing must respect available cash (no implicit margin)
- Watch for survivorship bias in the universe - delisted symbols vanish from data

## Production Implementation

`ml4t-backtest` provides a validated event-driven engine:

```python
from ml4t.backtest import (
    Strategy, Engine, DataFeed, BacktestConfig,
)

class Momentum(Strategy):
    def on_data(self, timestamp, data, context, broker):
        for sym, bar in data.items():
            if bar["signals"].get("momentum", 0) > 0 and not broker.get_position(sym):
                size = int(broker.get_cash() * 0.1 / bar["close"])
                broker.submit_order(sym, size)

feed = DataFeed(prices_df=prices, signals_df=signals)
config = BacktestConfig(commission_rate=0.001, slippage_rate=0.001)
result = Engine(feed, Momentum(), config).run()
print(f"Sharpe: {result.metrics['sharpe']:.2f}  MaxDD: {result.metrics['max_drawdown']:.1%}")
```

## Checklist

- [ ] Orders fill at a future bar, not the decision bar
- [ ] Signal function sees only past data (`prices[:t]`)
- [ ] Commission and slippage deducted on every fill
- [ ] Cash balance tracked - no implicit leverage
- [ ] Sharpe < 2.0 on daily data (or justified)
