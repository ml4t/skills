---
name: ml4t-live-trading
description: Transition from backtest to live trading with zero code changes. Use when deploying a validated strategy to paper or live markets.
dependencies: [run-backtest, kill-switch]
metadata:
  book_chapters: "26"
  library: "ml4t-live"
---

# Backtest-to-Live Deployment

Rewriting strategy logic for live trading introduces bugs and invalidates your backtest. The correct pattern is to reuse the exact Strategy class from backtesting — zero code changes between simulation and production.

## The Problem

Teams build a strategy in a backtest framework, validate it, then rewrite the logic in a separate live trading system. The rewrite introduces subtle differences: rounding, order timing, position tracking. The live system silently diverges from the validated backtest. Performance degrades and nobody can tell if it is the market or the code.

## The Pattern

### WRONG
```python
# Separate live strategy — rewrites logic, diverges from backtest
class LiveMomentumTrader:
    def __init__(self, api_key):
        self.api = BrokerAPI(api_key)

    def run(self):
        while True:
            prices = self.api.get_latest_bars(100)
            signal = prices["close"].pct_change(20).iloc[-1]
            if signal > 0:
                self.api.market_buy("SPY", 100)  # Different sizing logic
            elif signal < 0:
                self.api.market_sell("SPY", 100)  # No cost model
            time.sleep(60)
```

### CORRECT
```python
from abc import ABC, abstractmethod

class Strategy(ABC):
    """Single strategy class used for BOTH backtest and live."""

    @abstractmethod
    def on_data(self, timestamp, data, context, broker):
        ...

class Momentum(Strategy):
    def on_data(self, timestamp, data, context, broker):
        for sym, bar in data.items():
            mom = bar.get("momentum_20d", 0)
            pos = broker.get_position(sym)
            if mom > 0 and not pos:
                size = int(broker.get_cash() * 0.05 / bar["close"])
                broker.submit_order(sym, size)
            elif mom <= 0 and pos:
                broker.close_position(sym)

# Backtest: Engine(config).run(Momentum(), DataFeed(prices))
# Live:     LiveEngine(config).run(Momentum(), LiveDataFeed(...))
# Same class. Same logic. Different engine.
```

## Deployment Sequence

1. **Backtest** — validate with historical data, realistic costs
2. **Paper trade** (minimum 4 weeks) — same code, live data, simulated fills
3. **Shadow mode** — generate orders but don't execute; compare to paper
4. **Live with limits** — small size, tight kill switch, full monitoring
5. **Scale up** — increase size only after live metrics match paper

Never skip paper trading. If paper results diverge from backtest by more than one standard deviation, diagnose before going live.

## Data Feed Differences

| Property | Backtest | Live |
|----------|----------|------|
| Data arrival | Instant, complete | Streaming, may lag |
| Bars | All present | Build incrementally |
| Fills | Simulated, next-bar | Real, partial, rejected |
| Clock | Jump bar to bar | Real-time wall clock |

Handle partial fills: the broker may fill 80 of 100 shares. Your strategy must track actual vs intended position.

## Guardrails

- Identical Strategy class for backtest and live — if you change one, you broke the link
- Paper trade period is mandatory, not optional — 4 weeks minimum for daily strategies
- Kill switch must be active before any live order: max drawdown, max position, daily loss limit
- Log every order submission, fill, and rejection — you will need the audit trail
- Data staleness check: if last bar is older than 2x expected frequency, halt trading

## Production Implementation

`ml4t-live` reuses Strategy from `ml4t-backtest` with zero changes:

```python
from ml4t.backtest import Strategy
from ml4t.live import LiveEngine, AlpacaBroker, AlpacaDataFeed, SafeBroker, LiveRiskConfig

# Same Momentum class from backtest — no changes
engine = LiveEngine(config)
broker = SafeBroker(
    AlpacaBroker(api_key, secret_key),
    LiveRiskConfig(max_drawdown=0.10, max_position_pct=0.05),
)
engine.run(Momentum(), AlpacaDataFeed(api_key), broker=broker)
```

## Checklist

- [ ] Strategy class is identical for backtest and live (no separate live code)
- [ ] Paper traded for minimum 4 weeks with live data
- [ ] Kill switch configured with pre-approved thresholds
- [ ] Partial fill handling verified
- [ ] Data staleness detection active
- [ ] Order audit log capturing every submission, fill, and rejection
