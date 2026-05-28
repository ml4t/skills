---
name: ml4t-case-study-development
description: "Stage-gated research workflow from hypothesis through data prep, feature engineering, modeling, and backtest. Use when developing a trading strategy end-to-end with disciplined gate checks."
when_to_use: "Use when deciding what a case study should test next, which gate failed, or whether the study is ready to advance"
dependencies: [case-study-pipeline, triple-barrier, compute-features, cpcv, run-backtest, evaluate-factor]
metadata:
  book_chapters: "6, 7, 8, 11, 16, 20"
  library: "ml4t-backtest"
---
# Case Study Development Workflow

A case study is not just a pipeline; it is a sequence of research decisions. Clean artifacts are necessary, but the real question is whether each stage earned the right to move to the next one.

## The Problem

A researcher puts data loading, feature engineering, model training, and backtesting in a single notebook. It runs once and produces a Sharpe ratio. Later, they change the label horizon and must re-run everything. The model section silently reads stale features. The backtest uses predictions from a previous run. Nobody knows which config produced the final result. The pipeline is unreproducible and the results are untrustworthy.

## The Pattern

### WRONG

```python
# Everything in one notebook — no artifact boundaries, no config
data = pl.read_parquet("etf_data.parquet")
features = data.select(["momentum_12m", "volatility_20d"])
labels = data["close"].pct_change(21).shift(-21)

model = lgb.LGBMRegressor().fit(features, labels)  # Full-sample train!
predictions = model.predict(features)

# Backtest on training predictions with no cost model
cumulative_return = (predictions * labels).cumsum()
print(f"Sharpe: {sharpe(cumulative_return):.2f}")  # Meaningless number
```

### CORRECT

```python
# Seven-stage pipeline — each stage reads upstream artifacts, writes downstream
# All config lives in setup.yaml (SSOT), not scattered across notebooks

# Stage 1: SETUP (Ch6) — define universe, frequency, costs, evaluation protocol
# → Document hypothesis, kill criteria, and capacity estimate in setup.yaml
# → Output: setup.yaml with universe, frequency, cost_model, cv_config

# Stage 2: LABELS (Ch7) — forward returns and/or triple-barrier labels
# → Use ml4t-triple-barrier skill for event-driven labels
# → Output: data/labels/fwd_ret_{horizon}.parquet

# Stage 3: FEATURES (Ch8) — financial and model-based features
# → Use ml4t-compute-features skill
# → Output: data/features/financial.parquet, data/features/model_based.parquet

# Stage 4: EVALUATE FEATURES (Ch7-8) — IC, stability, redundancy
# → Use ml4t-evaluate-factor skill for IC significance and decay
# → Gate: drop features with IC t-stat < 2.0 or sign flip across subperiods

# Stage 5: TRAIN MODELS (Ch11+) — across CV folds, register each run
# → Use ml4t-cpcv skill for combinatorial purged cross-validation
# → Output: run_log/models/{hash}/predictions.parquet per config
# → Register: training_run → prediction_set entries in registry

# Stage 6: BACKTEST (Ch16) — combine predictions, simulate trading
# → Use ml4t-run-backtest skill with realistic cost model
# → Output: run_log/strategy/{hash}/ with equity curve, metrics

# Stage 7: SYNTHESIZE (Ch20) — compare models, report best config
# → Output: results/*.json with provenance back to registry
```

## Stage Gates

| Gate | Core question | Advance only if |
|------|---------------|-----------------|
| Setup | Is the hypothesis falsifiable? | Universe, costs, and success criteria are explicit |
| Labels | Is the target economically meaningful? | Horizon and label logic match holding period |
| Features | Do the signals survive diagnostics? | IC is stable, joins are clean, leakage checks pass |
| Models | Is validation credible? | CPCV or holdout beats a baseline without leakage |
| Backtest | Does the economics survive friction? | Costs, turnover, and capacity remain acceptable |
| Synthesis | Is there a decision? | Best config and rejection reasons are documented |

Artifact contracts still matter; use `ml4t-case-study-pipeline` to define them. This skill governs whether the study should advance.

## Guardrails

- If the hypothesis changes materially, restart at Setup instead of patching downstream results
- If model training runs without a registry entry, downstream conclusions are not auditable
- If backtest Sharpe > 2.0 on daily data, suspect leakage before celebrating
- If a gate fails, record the rejection reason instead of quietly continuing

## Production Implementation

`ml4t-engineer` and `ml4t-backtest` cover the feature and simulation handoff:

```python
from ml4t.backtest import BacktestConfig, run_backtest
from ml4t.engineer import compute_features

features = compute_features(data, "configs/features.yaml")
backtest_config = BacktestConfig.from_yaml("configs/backtest.yaml")
results = run_backtest(prices=prices, signals=signals, strategy=strategy, config=backtest_config)
```

## Checklist

- [ ] Setup gate defines universe, horizon, costs, and success criteria
- [ ] Feature gate passes IC, stability, and leakage checks before modeling
- [ ] Model gate beats a baseline on CPCV or holdout, not one lucky split
- [ ] Backtest gate survives realistic costs and turnover constraints
- [ ] Final synthesis records the chosen configuration and rejected alternatives
