---
name: ml4t-case-study-development
description: End-to-end case study development from trading setup through models to backtest results. Use when building a new case study for a dataset/asset class or auditing an existing pipeline for missing stages or broken artifact chains.
dependencies: [strategy-term-sheet, triple-barrier, compute-features, cpcv, run-backtest, evaluate-factor]
metadata:
  book_chapters: "6, 7, 8, 11, 16, 20"
  library: "ml4t-backtest"
---

# Case Study Development

A case study is a multi-stage pipeline where each stage produces artifacts consumed by the next. Breaking the chain — by skipping a stage, hardcoding paths, or running everything in one notebook — produces results that cannot be reproduced or extended.

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
# → Use ml4t-strategy-term-sheet skill
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

## The Artifact Chain

| Stage | Reads | Writes | Registry |
|-------|-------|--------|----------|
| Setup | Raw data | `config/setup.yaml` | -- |
| Labels | Config, prices | `data/labels/*.parquet` | -- |
| Features | Config, prices | `data/features/*.parquet` | -- |
| Models | Labels, features, CV config | `run_log/models/{hash}/` | `training_runs`, `prediction_sets` |
| Backtest | Predictions, cost model | `run_log/strategy/{hash}/` | `backtest_runs`, `backtest_metrics` |
| Synthesis | Registry queries | `results/*.json` | -- |

If any stage reads from a hardcoded path instead of the canonical location, config changes will not propagate and results silently go stale. `setup.yaml` is the SSOT — every notebook reads it for universe, label horizon, cost model, and CV scheme. No notebook defines these values locally.

## Guardrails

- If a notebook defines `horizon = 21` locally instead of reading from `setup.yaml`, the pipeline will silently diverge when the config changes
- If model training runs without a registry entry, downstream stages cannot trace which config produced which predictions
- If backtest Sharpe > 2.0 on daily data, suspect lookahead in the artifact chain (see `ml4t-lookahead-bias`)
- If features and labels have different row counts, a join mismatch has corrupted the pipeline

## Production Implementation

`ml4t-backtest` provides the strategy simulation layer and `ml4t-engineer` handles feature computation:

```python
from ml4t.backtest import run_backtest, BacktestConfig, DataFeed
from ml4t.engineer import compute_features

features = compute_features(data, "configs/features.yaml")
backtest_config = BacktestConfig.from_yaml("configs/backtest.yaml")
results = run_backtest(prices=prices, signals=signals, strategy=strategy, config=backtest_config)
```

## Checklist

- [ ] `setup.yaml` exists and defines universe, frequency, label, cost model, CV scheme
- [ ] Labels notebook reads horizon from config, not hardcoded
- [ ] Features notebook writes to `data/features/`, not ad-hoc paths
- [ ] Feature IC validated with HAC t-stat > 2.0 before modeling
- [ ] Every model config registered in `run_log/registry.db` with hash
- [ ] Backtest uses cost model from `setup.yaml`, not zero-cost default
- [ ] Results JSON includes provenance (registry hashes, config snapshot)
- [ ] Changing `setup.yaml` and re-running produces consistent end-to-end results
