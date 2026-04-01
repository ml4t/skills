---
name: ml4t-agent-risk-controls
description: "Safety controls and guardrails for autonomous trading agents. Use when deploying AI agents that can place orders or modify positions."
when_to_use: "Use when deploying agents that can place real orders, to enforce position limits, drawdown limits, and fail-safe defaults"
dependencies: [kill-switch, risk-metrics]
metadata:
  book_chapters: "24, 25"
  library: "ml4t-live"
paths: ["**/*agent*.py", "**/*rl*.py", "**/*rag*.py", "**/*graph*.py", "**/*knowledge*.py", "**/*orchestrat*.py"]
---
# Agent Risk Controls

An autonomous agent without layered risk controls is a loaded weapon. One model bug, one data feed glitch, or one misinterpreted signal can wipe out months of returns in minutes.

## The Problem

Knight Capital lost $440M in 45 minutes from a deployment bug — no kill switch, no rate limiter, no anomaly detection. Every autonomous system needs defense-in-depth: multiple independent layers so no single failure bypasses all controls.

## The Pattern

Wrap the execution path with composable risk checks. Each check can block or reduce an order. The default on any failure is to reduce exposure, never increase it.

### WRONG

```python
class TradingAgent:
    def on_signal(self, signal):
        shares = int(signal.strength * 10000)
        self.broker.submit_order(signal.symbol, shares)  # No limits
        # Bug in signal.strength → 100x intended size
        # No drawdown check → keeps buying into a crash
```

### CORRECT

```python
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

@dataclass
class RiskLimits:
    max_position_pct: float = 0.05    # 5% per name
    max_daily_trades: int = 100       # Trade rate limit
    max_drawdown_pct: float = 0.10    # 10% drawdown → halt
    max_order_value: float = 100_000  # Single order cap
    min_order_interval_sec: int = 5   # Rate limit

class RiskGate:
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.daily_trades = 0
        self.last_order_time = datetime.min
        self.peak_equity, self.halted = 0.0, False

    def check(self, symbol: str, shares: int, price: float,
              portfolio: dict) -> tuple[bool, str]:
        if self.halted:
            return False, "HALTED: drawdown limit breached"
        elapsed = (datetime.utcnow() - self.last_order_time).total_seconds()
        if elapsed < self.limits.min_order_interval_sec:
            return False, "rate_limited"
        if self.daily_trades >= self.limits.max_daily_trades:
            return False, "daily_trade_limit"
        order_val = abs(shares * price)
        if order_val > self.limits.max_order_value:
            return False, f"order_too_large: ${order_val:,.0f}"
        equity = portfolio.get("equity", 1)
        pos_val = abs(portfolio.get("positions", {}).get(symbol, 0) * price)
        if (pos_val + order_val) / equity > self.limits.max_position_pct:
            return False, "position_limit_exceeded"
        return True, "approved"

    def update_equity(self, equity: float):
        self.peak_equity = max(self.peak_equity, equity)
        if self.peak_equity > 0:
            dd = (self.peak_equity - equity) / self.peak_equity
            if dd > self.limits.max_drawdown_pct:
                self.halted = True  # Irreversible within session

    def record_trade(self):
        self.daily_trades += 1
        self.last_order_time = datetime.utcnow()
```

## Fail-Safe Principle

Stack risk checks as decorators on `submit_order()` — structurally impossible to bypass. On any uncertainty, reduce exposure, never increase it.

## Guardrails

- **Risk checks independent of signal path** — signal bugs must not bypass risk layer
- **Drawdown halt irreversible within session** — only human restart clears it
- **Rate limits catch runaway loops** — 1000 signals/sec caught by trade-rate limit
- **Test with adversarial inputs** — extreme sizes, negative prices, NaN must all be blocked
- **Log every rejection** — blocked orders as important as executed ones for audit

## Production Implementation

`ml4t-live` provides `SafeBroker` with production-grade risk controls:

```python
from ml4t.live import AlpacaBroker, SafeBroker, LiveRiskConfig

risk_config = LiveRiskConfig(
    max_position_value=50_000.0, max_drawdown_pct=0.10,
    max_orders_per_minute=10, max_order_value=100_000.0,
)
broker = SafeBroker(AlpacaBroker(api_key="...", secret_key="..."), risk_config)
# Wraps every submit_order() with risk checks; drawdown halt is irreversible
```

## Checklist

- [ ] Risk gate is independent of signal generation (separate module)
- [ ] Position limits enforced per-name and per-sector
- [ ] Drawdown halt is irreversible within session (requires human restart)
- [ ] Trade rate limit prevents runaway order loops
- [ ] Every blocked order logged with reason and full context
- [ ] Fail-safe default is reduce exposure; tested with adversarial inputs (extreme sizes, NaN)
