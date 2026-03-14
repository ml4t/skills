---
name: ml4t-strategy-workflow
description: End-to-end strategy development lifecycle from hypothesis to live trading. Use when starting a new strategy or auditing an existing development process for missing stages.
dependencies: [strategy-term-sheet, fetch-data, compute-features, run-backtest, transaction-costs]
metadata:
  book_chapters: "1, 6, 16, 20"
  library: "ml4t-backtest"
---

# Strategy Development Workflow

Strategies fail because developers skip straight to modeling. The correct process spends most time on hypothesis and data, with modeling as a small fraction.

## The Problem

A researcher downloads data, fits a gradient boosting model, runs a backtest, and sees a 2.5 Sharpe ratio. They deploy. Within weeks the strategy bleeds money. The failure mode is always the same: no documented hypothesis, no feature validation, no cost model, no out-of-sample hold-out. Modeling was the first step instead of the last.

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
# Stage 1: HYPOTHESIS — document before writing code
hypothesis = {
    "mechanism": "Momentum persists due to slow institutional rebalancing",
    "signal": "12-month risk-adjusted return predicts 1-month forward return",
    "kill_criteria": "IC < 0.02 or non-monotonic quintiles",
    "capacity": "ETFs with >$50M daily volume",
}
# Commit term sheet to version control before proceeding

# Stage 2: DATA — validate before feature engineering
# → Use ml4t-fetch-data skill for sourcing and validation

# Stage 3: FEATURES — evaluate before modeling
# → Use ml4t-compute-features skill
# → Use ml4t-factor-research workflow for IC, decay, stability

# Stage 4: MODEL — proper CV, not train/test split
# → Use ml4t-cpcv skill for combinatorial purged CV
# → Use ml4t-model-validation workflow for full gate sequence

# Stage 5: BACKTEST — with realistic costs
# → Use ml4t-run-backtest skill
# → Use ml4t-transaction-costs skill for cost modeling

# Stage 6: PAPER TRADE — live data, simulated execution (weeks)
# Stage 7: LIVE — small size, ramp up over months
```

## Quality Gates

Each stage has a gate that must pass before proceeding:

| Gate | Condition | Fail Action |
|------|-----------|-------------|
| Hypothesis | Documented mechanism, kill criteria, capacity estimate | Do not start coding |
| Data | No gaps > 2 days, point-in-time correct, survivorship-free | Fix data pipeline |
| Features | IC > 0.02 (HAC-adjusted), stable across subperiods | Drop factor or redesign |
| Model | PBO < 50%, deflated Sharpe significant | Simplify model or revisit features |
| Backtest | Sharpe > 0.5 net of costs, max DD < 20% | Revise sizing or cost assumptions |
| Paper trade | Fills within expected slippage, no execution anomalies | Fix execution logic |

## Where Time Should Go

Most effort belongs in the early stages — 60% hypothesis and data, 25% features and validation, 15% modeling and backtest. If you spend more time tuning hyperparameters than understanding your data, the process is inverted.

## Guardrails

- If Sharpe > 2.0 on daily data, assume lookahead bias until proven otherwise (see `ml4t-lookahead-bias`)
- If in-sample and out-of-sample performance match closely, suspect data leakage
- If the strategy requires > 20% annual turnover to work, verify cost assumptions with `ml4t-transaction-costs`
- If no documented hypothesis exists, stop and write one before any other work

## Production Implementation

`ml4t-backtest` and `ml4t-live` share the same `Strategy` interface, enabling zero-code-change deployment:

```python
from ml4t.backtest import Strategy, run_backtest, BacktestConfig
from ml4t.live import LiveEngine, AlpacaBroker

# Same Strategy class works in backtest and live
results = run_backtest(strategy=MyStrategy(), config=BacktestConfig(...))

# When ready for live (after paper trading)
engine = LiveEngine(strategy=MyStrategy(), broker=AlpacaBroker())
engine.run()
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
