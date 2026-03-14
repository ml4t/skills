---
name: ml4t-kill-switch
description: Automated risk limits and circuit breakers
category: portfolio
type: operational
dependencies: [risk-metrics]
book_chapters: [20, 26]
---

# Kill Switch

Automated risk controls that halt or reduce trading.

## Trigger Types

| Type | Measure | Example Threshold |
|------|---------|-------------------|
| Drawdown | Current DD | > 15% |
| Daily loss | Single day P&L | > 3% |
| Volatility | Realized vol | > 2x target |
| Exposure | Gross leverage | > 2.0 |
| Correlation | Rolling pairwise | > 0.8 |

## Kill Switch Implementation

```python
class KillSwitch:
    def __init__(self, thresholds: dict):
        self.thresholds = thresholds
        self.active = False
        self.trigger_reason = None

    def check(self, metrics: dict) -> bool:
        """Check if kill switch should trigger."""
        for metric, threshold in self.thresholds.items():
            if metrics[metric] > threshold:
                self.active = True
                self.trigger_reason = f"{metric}: {metrics[metric]:.2%} > {threshold:.2%}"
                return True
        return False

    def action(self, positions: np.ndarray) -> np.ndarray:
        """Return target positions when triggered."""
        if self.active:
            return np.zeros_like(positions)  # Flatten
        return positions
```

## Graduated Response

```python
RISK_LEVELS = {
    'green': {'max_position': 1.0, 'leverage': 2.0},
    'yellow': {'max_position': 0.5, 'leverage': 1.0},
    'red': {'max_position': 0.2, 'leverage': 0.5},
    'halt': {'max_position': 0.0, 'leverage': 0.0}
}

def get_risk_level(drawdown: float, volatility: float) -> str:
    """Determine current risk level."""
    if drawdown > 0.20 or volatility > 0.50:
        return 'halt'
    elif drawdown > 0.15 or volatility > 0.35:
        return 'red'
    elif drawdown > 0.10 or volatility > 0.25:
        return 'yellow'
    return 'green'
```

## Monitoring Loop

```python
def monitor_and_control(
    portfolio: Portfolio,
    kill_switch: KillSwitch,
    check_interval: int = 60  # seconds
):
    """Continuous monitoring loop."""
    while True:
        metrics = {
            'drawdown': portfolio.current_drawdown(),
            'daily_pnl': portfolio.daily_pnl(),
            'volatility': portfolio.realized_vol(window=20),
            'gross_exposure': portfolio.gross_exposure()
        }

        if kill_switch.check(metrics):
            logger.critical(f"KILL SWITCH: {kill_switch.trigger_reason}")
            portfolio.flatten_all()
            alert_team(kill_switch.trigger_reason)

        time.sleep(check_interval)
```

## Recovery Protocol

```python
def recovery_check(
    portfolio: Portfolio,
    cooldown_hours: int = 24
) -> bool:
    """Check if safe to resume trading."""
    checks = {
        'cooldown_elapsed': hours_since_trigger() > cooldown_hours,
        'drawdown_recovered': portfolio.current_drawdown() < 0.10,
        'volatility_normal': portfolio.realized_vol() < 0.25,
        'manual_approval': get_manual_approval()
    }
    return all(checks.values())
```

## Guardrails

- Thresholds must be pre-defined, not reactive
- Automatic triggers; manual resets
- Log all trigger events
- Test kill switch periodically

## Checklist

- [ ] Thresholds documented and approved
- [ ] Automated monitoring active
- [ ] Alert system configured
- [ ] Recovery protocol defined
- [ ] Regular testing of kill switch
