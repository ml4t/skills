---
name: ml4t-production-readiness
description: "Pre-deployment checklist covering data pipelines, risk limits, monitoring, and governance. Use when preparing to go live with a new strategy or model."
when_to_use: "Use when a validated strategy is being prepared for live capital"
dependencies: [kill-switch, drift-detection, cost-model, risk-metrics]
metadata:
  book_chapters: "25, 26"
  library: "ml4t-live"
---
# Production Readiness

A validated backtest is not a production system. The gap between "model works" and "strategy can run unattended with real money" requires infrastructure that most teams skip until the first incident.

## The Problem

A team deploys a model that passed validation. On day three, the data vendor has an outage. The model receives stale prices, generates signals, and the execution system submits orders on bad data. There is no kill switch, no staleness check, no alert. By the time someone notices, the strategy has lost two months of expected returns in a single session. Every production failure traces back to missing infrastructure, not bad models.

## The Pattern

### WRONG

```python
# Model works in backtest — deploy directly
import pickle
from broker_api import submit_orders

model = pickle.load(open("best_model.pkl", "rb"))
data = fetch_latest_data()
signals = model.predict(data)
orders = signals_to_orders(signals)
for order in orders:
    submit_orders(order)  # No limits, no monitoring, no kill switch
```

### CORRECT

```python
# Five infrastructure layers before any live order
import datetime as dt

# Layer 1: DATA PIPELINE — validate freshness and integrity
latest_ts = data_store.get_latest_timestamp()
staleness = dt.datetime.now(dt.timezone.utc) - latest_ts
assert staleness < dt.timedelta(hours=2), f"Data stale: {staleness}"
assert data_store.validate_schema(), "Schema mismatch — pipeline broken"

# Layer 2: MODEL VERSIONING — reproducibility and audit trail
model_hash = compute_model_hash(model_path)
assert model_hash == registry.get_deployed_hash(), "Model hash mismatch"
assert registry.get_training_date(model_hash) > dt.date(2025, 6, 1), "Model too old"

# Layer 3: RISK LIMITS — hard limits that cannot be overridden by signals
risk_config = {
    "max_position_pct": 0.05,       # No single position > 5% of portfolio
    "max_sector_pct": 0.25,         # No sector > 25%
    "max_daily_turnover": 0.20,     # Max 20% daily turnover
    "max_drawdown_halt": 0.10,      # Halt trading at 10% drawdown
    "max_gross_leverage": 1.5,      # Hard leverage cap
}

# Layer 4: MONITORING — detect problems before they compound
# → Use ml4t-drift-detection for feature/prediction distribution shifts
# → Use ml4t-risk-metrics for rolling drawdown and exposure tracking
# Alerts fire on: data staleness, drift PSI > 0.25, drawdown > threshold

# Layer 5: KILL SWITCH — automated and manual halt capability
# → Use ml4t-kill-switch for implementation
# Kill switch triggers: max drawdown, data staleness, model drift, manual override
# Kill switch action: flatten all positions, cancel open orders, alert team
```

## Five Readiness Layers

| Layer | What It Covers | Failure Without It |
|-------|---------------|-------------------|
| Data pipeline | Freshness, schema validation, fallback sources | Trading on stale or corrupted data |
| Model versioning | Hash verification, training metadata, feature config | Deploying wrong model, irreproducible results |
| Risk limits | Position, sector, leverage, drawdown hard limits | Unbounded loss from signal errors |
| Monitoring | Drift detection, performance tracking, alerting | Problems compound for hours/days before detection |
| Kill switch | Automated halt + manual override + flatten capability | Cannot stop bleeding when something breaks |

## Paper Trading Gate

No strategy goes live without minimum 4 weeks of paper trading covering at least one rebalance cycle. Paper trading validates order generation, fill assumptions, data pipeline reliability, and monitoring/alerting behavior.

## Guardrails

- If you cannot explain exactly which model version is running, do not trade live
- If the kill switch has not been tested (triggered and verified), it does not work
- If data fallback has not been tested by simulating a source outage, assume it will fail
- If drawdown limits exist only in code you can override, they are not real limits
- If there is no on-call rotation or incident playbook, the first production issue will be chaotic

## Production Implementation

`ml4t-live` provides the infrastructure for safe live deployment:

```python
from ml4t.backtest import Strategy  # Same Strategy class as backtest
from ml4t.live import LiveEngine, AlpacaBroker, LiveRiskConfig, SafeBroker

risk = LiveRiskConfig(
    max_position_value=50_000.0, max_drawdown_pct=0.10, max_total_exposure=200_000.0
)
broker = SafeBroker(AlpacaBroker(), risk)  # Wraps with limits
engine = LiveEngine(strategy=MyStrategy(), broker=broker)
engine.run()  # Includes built-in monitoring and kill switch
```

## Checklist

- [ ] Data pipeline validates freshness (staleness < threshold) and schema on every run
- [ ] Fallback data source tested by simulating primary source failure
- [ ] Deployed model hash matches training registry entry
- [ ] Feature pipeline is identical between training and production (no train/serve skew)
- [ ] Hard risk limits configured: position size, sector exposure, leverage, drawdown
- [ ] Kill switch tested: triggers correctly, flattens positions, sends alerts
- [ ] Monitoring dashboards operational with alerts for drift, drawdown, staleness
- [ ] Paper trading completed for minimum 4 weeks with no execution anomalies
- [ ] Incident playbook and governance sign-off completed before go-live
