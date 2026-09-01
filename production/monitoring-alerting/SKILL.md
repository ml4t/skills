---
name: ml4t-monitoring-alerting
description: "Real-time monitoring and alerting for live trading systems. Use when building observability for data pipelines, model drift, or execution quality."
when_to_use: "Use when running strategies in production and need automated health checks, performance tracking, and incident detection"
dependencies: [kill-switch, drift-detection, risk-metrics]
metadata:
  book_chapters: "25, 26"
  library: "ml4t-live"
paths: ["**/*live*.py", "**/*deploy*.py", "**/*monitor*.py", "**/*govern*.py", "**/*mlops*.py", "**/*pipeline*.py"]
---
# Monitoring and Alerting

Checking performance at end-of-day is too late. A stuck data feed, a rejected order, or a flash crash can cause irreversible losses in minutes. Automated real-time monitoring catches problems when they are still small.

## The Problem

A strategy runs in production. The data feed silently stalls at 10:15 AM - the strategy stops generating signals but nobody notices until 4 PM. By then, the portfolio has drifted and missed the day's best opportunities. Worse: a position limit was breached because a partial fill was not tracked, and the strategy doubled down. End-of-day review catches the problem 6 hours too late.

## The Pattern

### WRONG
```python
# End-of-day check - too late for anything but damage assessment
def daily_report():
    pnl = portfolio.value() - portfolio.start_of_day_value()
    if pnl < -10_000:
        send_email("Bad day", f"Lost ${abs(pnl):,.0f}")
# Run at 4:30 PM - 6+ hours after problems started
schedule.every().day.at("16:30").do(daily_report)
```

### CORRECT
```python
import time
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger("monitor")

@dataclass
class AlertThresholds:
    max_drawdown: float = 0.05         # 5% intraday drawdown
    max_daily_loss: float = 0.02       # 2% daily loss
    max_position_pct: float = 0.10     # 10% in single name
    data_stale_seconds: int = 120      # 2 minutes without new data
    fill_rate_floor: float = 0.80      # 80% of orders must fill

def monitor_loop(portfolio, data_feed, thresholds: AlertThresholds):
    """Continuous monitoring with immediate alerting."""
    while True:
        now = datetime.now(UTC)

        last = data_feed.last_timestamp()
        if last.tzinfo is None:      # naive: subtracting from `now` raises
            last = last.replace(tzinfo=UTC)
        # .seconds is the sub-day part, so a 24h stall would read as fresh
        stale = (now - last).total_seconds()
        if stale > thresholds.data_stale_seconds:
            alert("DATA_STALE", f"No data for {stale:.0f}s")

        # Drawdown
        dd = portfolio.current_drawdown()
        if dd > thresholds.max_drawdown:
            alert("DRAWDOWN", f"Intraday DD: {dd:.1%}")

        # Position concentration
        for sym, weight in portfolio.weights().items():
            if abs(weight) > thresholds.max_position_pct:
                alert("CONCENTRATION", f"{sym}: {weight:.1%}")

        # Fill rate
        fill_rate = portfolio.fill_rate(window_minutes=30)
        if fill_rate < thresholds.fill_rate_floor:
            alert("LOW_FILLS", f"Fill rate: {fill_rate:.0%}")

        time.sleep(10)  # Check every 10 seconds
```

## What to Monitor

Five categories: **P&L** (intraday drawdown > 5%, daily loss > 2%), **Positions** (single-name > 10%, gross leverage > 2x), **Execution** (fill rate < 80%, slippage > 2x model), **Data** (bar age > 2x interval, stale prices), **System** (latency > 500ms, memory > 80%).

## Alert Escalation

Four levels: **INFO** (log only), **WARNING** (Slack), **CRITICAL** (page on-call), **HALT** (trigger kill switch). Debounce noisy metrics - trigger only if the condition persists for N consecutive checks to avoid alert fatigue.

## Guardrails

- Monitor loop must run independently from the trading process - if trading crashes, monitoring must still work
- Data staleness check must use wall clock, not data timestamps (which stop updating when the feed dies)
- Test the alerting path end-to-end: trigger a fake alert and verify it reaches the right person

## Production Implementation

`ml4t-live` provides monitoring hooks integrated with the trading engine:

```python
from ml4t.live import SafeBroker, LiveRiskConfig

config = LiveRiskConfig(
    execution_mode="shadow",   # required: "shadow", "paper" or "live"
    max_drawdown_pct=0.05,     # positive fraction below the high-water mark
    max_daily_loss=5_000.0,
    max_data_staleness_seconds=120.0,
)
broker = SafeBroker(inner_broker, config)
# A breach raises RiskLimitError in the TRADING process and latches the switch.
# The monitor above runs separately and never sees that exception - the trading
# process has to record the incident somewhere the monitor reads.
```

## Checklist

- [ ] Monitoring loop runs independently from trading process
- [ ] Data staleness detected within 2x expected bar interval
- [ ] Drawdown and daily loss alerts configured and tested
- [ ] Position concentration limits enforced
- [ ] Fill rate tracked with 30-minute rolling window
- [ ] Alert escalation tested end-to-end; all thresholds documented before go-live
