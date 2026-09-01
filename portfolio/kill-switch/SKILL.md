---
name: ml4t-kill-switch
description: "Automated risk limits that halt trading when thresholds are breached. Use when deploying live strategies that need drawdown or loss-limit protection."
when_to_use: "Use when building live trading systems or production risk management"
dependencies: [risk-metrics]
metadata:
  book_chapters: "19, 25"
  library: "ml4t-live"
paths: ["**/*portfolio*.py", "**/*position*.py", "**/*risk*.py", "**/*optim*.py", "**/*exposure*.py", "**/*kill*.py", "**/*stress*.py"]
---
# Kill Switch

A human monitoring a dashboard will not react fast enough to a flash crash. By the time you see the loss and decide to act, the drawdown has compounded. Automated kill switches are the last line of defense - they must be hard-coded, not ML-based, and not overridable without explicit manual intervention.

## The Problem

Live trading systems face risks that backtests never encounter: data feed failures, exchange outages, runaway algorithms, and flash crashes. A strategy producing 100 orders per second during a data glitch can lose more in minutes than it earned in months. Manual monitoring fails because: (1) humans are slow, (2) losses compound nonlinearly, and (3) the worst events happen when attention is lowest. Kill switches must trigger automatically, flatten positions immediately, and require human approval to resume.

## The Pattern

### WRONG
```python
# "I'll watch the dashboard and close positions if things go wrong"
import time

while True:
    pnl = get_daily_pnl()
    if pnl < -10000:
        print("WARNING: large loss")  # prints to a log nobody reads at 3am
        send_email("Loss alert")      # email arrives 5 min later
    time.sleep(60)
# Meanwhile, the algo keeps trading during the 60s sleep
```

### CORRECT
```python
class KillSwitch:
    """Hard-coded risk limits. Automatic trigger, manual reset only."""

    THRESHOLDS = {
        "max_daily_loss": -0.03,     # -3% daily P&L
        "max_drawdown": -0.15,       # -15% from peak
        "max_gross_leverage": 2.0,   # 200% gross
        "max_position_pct": 0.15,    # 15% in single name
    }

    def __init__(self, reset_code):
        self.triggered = False
        self.trigger_reason = None
        self.reset_code = reset_code  # from your secret store, not from source

    def check(self, daily_pnl, drawdown, gross_lev, max_pos, reducing=False):
        """Called BEFORE every order. False = block. Reducing risk still passes."""
        if self.triggered:
            return reducing  # latched: nothing but reset() clears this
        checks = {
            "max_daily_loss": daily_pnl > self.THRESHOLDS["max_daily_loss"],
            "max_drawdown": drawdown > self.THRESHOLDS["max_drawdown"],
            "max_gross_leverage": gross_lev < self.THRESHOLDS["max_gross_leverage"],
            "max_position_pct": max_pos < self.THRESHOLDS["max_position_pct"],
        }
        for name, passed in checks.items():
            if not passed:
                self.triggered = True
                self.trigger_reason = f"{name}: threshold breached"
                return reducing  # block new risk, still allow flattening
        return True  # safe to proceed

    def reset(self, manual_approval_code: str):
        """Require explicit human approval to resume."""
        if manual_approval_code == self.reset_code:
            self.triggered = False
            self.trigger_reason = None
```

## Graduated Response

Not every breach requires full shutdown. Scale down gracefully with risk levels:

```python
def risk_level(drawdown, realized_vol, target_vol=0.10):
    vol_ratio = realized_vol / target_vol
    if drawdown < -0.20 or vol_ratio > 3.0: return "halt"    # flatten all
    if drawdown < -0.15 or vol_ratio > 2.0: return "red"     # 25% size
    if drawdown < -0.10 or vol_ratio > 1.5: return "yellow"  # 50% size
    return "green"                                             # full size
```

## Guardrails

- Thresholds must be set BEFORE deployment, not adjusted during a drawdown
- Checks run BEFORE order submission, and a trigger latches until manual reset
- A latched switch must still pass risk-reducing orders, or you cannot flatten
- Data feed failure is a trigger - no data means no trading, not "use stale prices"

## Production Implementation

`ml4t-live` wraps any broker with pre-trade risk checks:

```python
from ml4t.live import SafeBroker, LiveRiskConfig, AlpacaBroker

config = LiveRiskConfig(
    execution_mode="shadow",   # required: "shadow", "paper" or "live"
    max_daily_loss=5_000.0,
    max_drawdown_pct=0.15,     # positive fraction below the high-water mark
    max_position_value=50_000.0,
)
broker = SafeBroker(AlpacaBroker(api_key, secret_key), config)
# A breach latches the switch and blocks risk-increasing orders. Flattening is
# a separate call: await broker.close_all_positions()
```

## Checklist

- [ ] All thresholds defined and documented before deployment
- [ ] Kill switch runs pre-trade (before every order submission)
- [ ] Automatic trigger, manual-only reset with approval code
- [ ] Data feed failure triggers halt (not stale-price trading)
- [ ] Monthly fire drill: simulate a breach and verify the system flattens
