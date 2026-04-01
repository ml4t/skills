---
name: ml4t-live-trading
description: "Transition from backtest to live trading with zero code changes. Use when deploying a validated strategy to paper or live trading via broker APIs."
when_to_use: "Use when deploying a validated strategy to paper or live markets"
dependencies: [run-backtest, kill-switch]
metadata:
  book_chapters: "25"
  library: "ml4t-live"
paths: ["**/*live*.py", "**/*deploy*.py", "**/*monitor*.py", "**/*govern*.py", "**/*mlops*.py", "**/*pipeline*.py"]
---
# Backtest-to-Live Deployment

Rewriting strategy logic for live trading introduces bugs and invalidates your backtest. The correct pattern is to reuse the exact Strategy class from backtesting — zero code changes between simulation and production.

## The Problem

Teams often validate a strategy in backtest, then rewrite it for live trading.
That rewrite changes rounding, timing, or position tracking and silently breaks
the link to the validated backtest.

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

# Backtest: Engine(feed, Momentum(), config).run()
# Live:     await LiveEngine(Momentum(), broker, feed).run()
# Same class. Same logic. Different engine.
```

## Deployment Sequence

1. **Backtest** — validate with historical data, realistic costs
2. **Paper trade** (minimum 4 weeks) — same code, live data, simulated fills
3. **Shadow mode** — generate orders but don't execute; compare to paper
4. **Live with limits** — small size, tight kill switch, full monitoring
5. **Scale up** — increase size only after live metrics match paper

Never skip paper trading. If paper diverges materially from backtest, diagnose before going live.

## Data Feed Differences

| Property | Backtest | Live |
|----------|----------|------|
| Data arrival | Instant, complete | Streaming, may lag |
| Bars | All present | Build incrementally |
| Fills | Simulated, next-bar | Real, partial, rejected |
| Clock | Jump bar to bar | Real-time wall clock |

## Guardrails

- Identical Strategy class for backtest and live — if you change one, you broke the link
- Paper trade period is mandatory, not optional — 4 weeks minimum for daily strategies
- Kill switch must be active before any live order: max drawdown, max position, daily loss limit
- Log every order submission, fill, and rejection — you will need the audit trail
- Data staleness check: if last bar is older than 2x expected frequency, halt trading

## Production Implementation

```python
import asyncio

from ml4t.backtest import Strategy
from ml4t.live import LiveEngine, AlpacaBroker, AlpacaDataFeed, SafeBroker, LiveRiskConfig

broker = SafeBroker(AlpacaBroker(api_key, secret_key), LiveRiskConfig(max_drawdown_pct=0.10))
feed = AlpacaDataFeed(api_key, secret_key, symbols=["SPY"])

async def trade_live():
    engine = LiveEngine(Momentum(), broker, feed)
    await engine.connect()
    await engine.run()

asyncio.run(trade_live())
```

## Checklist

- [ ] Strategy class is identical for backtest and live (no separate live code)
- [ ] Paper traded for minimum 4 weeks with live data
- [ ] Kill switch configured with pre-approved thresholds
- [ ] Partial fill handling verified
- [ ] Data staleness detection active; order audit log captures every submission and fill
