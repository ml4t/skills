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
schedule.every().day.at("16:30").do(daily_report)  # 6+ hours after it started
```

### CORRECT
```python
import time
from dataclasses import dataclass
from datetime import UTC, datetime

@dataclass
class AlertThresholds:
    max_drawdown: float = 0.05         # 5% intraday drawdown
    max_daily_loss: float = 0.02       # 2% daily loss
    max_position_pct: float = 0.10     # 10% in single name
    data_stale_seconds: int = 120      # 2 minutes without new data
    fill_rate_floor: float = 0.80      # 80% of orders must fill

def monitor_loop(portfolio, data_feed, thresholds: AlertThresholds, debounce=3):
    """Continuous monitoring with immediate alerting."""
    streak = {}

    def check(name, breached, message):
        # One bad sample is noise; `debounce` of them in a row is an incident.
        streak[name] = streak.get(name, 0) + 1 if breached else 0
        if streak[name] == debounce:
            alert(name, message)

    while True:
        now = datetime.now(UTC)
        last = data_feed.last_timestamp()
        if last.tzinfo is None:      # naive: subtracting from `now` raises
            last = last.replace(tzinfo=UTC)
        # .seconds is the sub-day part, so a 24h stall would read as fresh
        stale = (now - last).total_seconds()
        check("DATA_STALE", stale > thresholds.data_stale_seconds, f"Stale {stale:.0f}s")

        dd = portfolio.current_drawdown()
        check("DRAWDOWN", dd > thresholds.max_drawdown, f"Intraday DD: {dd:.1%}")
        loss = -portfolio.daily_return()  # the threshold was defined and never read
        check("DAILY_LOSS", loss > thresholds.max_daily_loss, f"Daily loss: {loss:.1%}")

        for sym, weight in portfolio.weights().items():
            check(f"CONCENTRATION:{sym}", abs(weight) > thresholds.max_position_pct,
                  f"{sym}: {weight:.1%}")

        fill_rate = portfolio.fill_rate(window_minutes=30)
        check("LOW_FILLS", fill_rate < thresholds.fill_rate_floor, f"Fills {fill_rate:.0%}")
        time.sleep(10)  # every 10s, so a 3-sample debounce alerts after 30s
```

## What to Monitor

Five categories: **P&L** (intraday drawdown > 5%, daily loss > 2%), **Positions** (single-name > 10%, gross leverage > 2x), **Execution** (fill rate < 80%, slippage > 2x model), **Data** (bar age > 2x interval, stale prices), **System** (latency > 500ms, memory > 80%).

## Alert Escalation

Four levels: **INFO** (log only), **WARNING** (Slack), **CRITICAL** (page on-call), **HALT** (trigger kill switch). Route by name from `check` above; the debounce there is what keeps a single bad sample off the pager.

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
