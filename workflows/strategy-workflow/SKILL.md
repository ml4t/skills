---
name: ml4t-strategy-workflow
description: "End-to-end strategy development lifecycle from hypothesis to live trading. Use when starting a new strategy project or onboarding to the ML4T workflow."
when_to_use: "Use when starting a new strategy or auditing an existing development process for missing stages"
dependencies: [fetch-data, compute-features, run-backtest, transaction-costs]
metadata:
  book_chapters: "1, 6, 16, 20"
  library: "ml4t-backtest"
---
# Strategy Development Workflow

Strategies fail because developers skip straight to modeling. The correct process spends most time on hypothesis and data, with modeling as a small fraction.

## The Problem

A researcher downloads data, fits a model, runs a backtest, and sees a 2.5
Sharpe ratio. They deploy, then lose money because there was no documented
hypothesis, no feature validation, no cost model, and no holdout.

## The Pattern

### WRONG

```python
# Jump straight to modeling — no hypothesis, no validation gates
import lightgbm as lgb

data = load_data()
features = data[["momentum", "volatility", "volume"]]
labels = data["next_day_return"]

model = lgb.LGBMRegressor().fit(features, labels)
predictions = model.predict(features)  # Predicting on training data!

# "Looks great, ship it"
print(f"R2: {r2_score(labels, predictions):.3f}")  # 0.95 — overfitting
```

### CORRECT

```python
# Seven stages with quality gates between each
hypothesis = {
    "mechanism": "Momentum persists due to slow institutional rebalancing",
    "signal": "12-month risk-adjusted return predicts 1-month forward return",
    "kill_criteria": "IC < 0.02 or non-monotonic quintiles",
    "capacity": "ETFs with >$50M daily volume",
}
# Commit term sheet to version control before proceeding

# Stage 2: Data  → fetch + validate
# Stage 3: Features → compute + factor research
# Stage 4: Model → CPCV + model validation
# Stage 5: Backtest → realistic costs
# Stage 6: Paper trade → live data, simulated fills
# Stage 7: Live → small size, slow ramp
```

## Quality Gates

| Gate | Condition | Fail Action |
|------|-----------|-------------|
| Hypothesis | Documented mechanism, kill criteria, capacity estimate | Do not start coding |
| Data | No gaps > 2 days, point-in-time correct, survivorship-free | Fix data pipeline |
| Features | IC > 0.02 (HAC-adjusted), stable across subperiods | Drop factor or redesign |
| Model | PBO < 50%, deflated Sharpe significant | Simplify model or revisit features |
| Backtest | Sharpe > 0.5 net of costs, max DD < 20% | Revise sizing or cost assumptions |
| Paper trade | Fills within expected slippage, no execution anomalies | Fix execution logic |

## Guardrails

- If Sharpe > 2.0 on daily equity data, assume lookahead bias or selection bias until proven otherwise — inspect with `ml4t-lookahead-bias` and `ml4t-deflated-sharpe`
- If in-sample and out-of-sample performance match closely, suspect data leakage
- If the strategy requires > 20% annual turnover to work, verify cost assumptions with `ml4t-transaction-costs`
- If no documented hypothesis exists, stop and write one before any other work

## Production Implementation

```python
import asyncio

from ml4t.backtest import Strategy, run_backtest, BacktestConfig
from ml4t.live import LiveEngine, AlpacaBroker, AlpacaDataFeed

results = run_backtest(
    prices=prices, signals=signals, strategy=MyStrategy(), config=BacktestConfig()
)

async def trade_live():
    broker = AlpacaBroker(api_key, secret_key, paper=True)
    feed = AlpacaDataFeed(api_key, secret_key, symbols=["SPY"])
    engine = LiveEngine(MyStrategy(), broker, feed)
    await engine.connect()
    await engine.run()

asyncio.run(trade_live())
```

## Checklist

- [ ] Hypothesis documented in term sheet before any code
- [ ] Data validated for gaps, survivorship bias, point-in-time correctness
- [ ] Features pass IC significance test with HAC standard errors
- [ ] Model validated via CPCV with PBO < 50%
- [ ] Backtest includes realistic transaction costs
- [ ] Deflated Sharpe ratio computed across all trials
- [ ] Paper trading completed for minimum 4 weeks
- [ ] Kill criteria defined and monitoring configured before going live
