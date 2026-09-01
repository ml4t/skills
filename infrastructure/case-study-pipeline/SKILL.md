---
name: ml4t-case-study-pipeline
description: "Filesystem and artifact-contract pattern for reproducible case studies. Use when organizing a research project for reproducibility and collaboration."
when_to_use: "Use when refactoring notebooks into deterministic stages with stable inputs, outputs, and rerun boundaries"
dependencies: [fetch-data, triple-barrier, compute-features, run-backtest, registry-system]
metadata:
  book_chapters: "6, 7, 8, 11"
  library: ""
paths: ["**/*schema*.py", "**/*registry*.py", "**/*pipeline*.py", "**/*polars*.py", "**/*case_study*.py"]
---
# Case Study Artifact Pipeline

Ad-hoc notebooks that load data, compute features, train models, and backtest in one file are impossible to debug, reproduce, or extend. This skill is about artifact boundaries and rerun rules, not about whether the research thesis is good.

## The Problem

A quant writes a 500-line notebook that downloads data, engineers features, trains a model, and runs a backtest. It works once. Then: the data source changes, a feature is added, the model is retrained with different parameters, and the backtest uses stale predictions from the old model. Nobody can tell which outputs correspond to which inputs. The notebook becomes untouchable - too risky to change, too opaque to trust.

## The Pattern

### WRONG
```python
# Monolithic notebook - everything in one file, no artifact boundaries
import polars as pl
from sklearn.linear_model import Ridge

prices = pl.read_parquet("prices.parquet")
prices = prices.with_columns(
    fwd_ret=pl.col("close").pct_change(21).shift(-21).over("symbol"),
    momentum=pl.col("close").pct_change(63).over("symbol"),
    volatility=pl.col("close").pct_change().rolling_std(21).over("symbol"),
)
prices = prices.drop_nulls()
X = prices.select(["momentum", "volatility"]).to_numpy()
y = prices["fwd_ret"].to_numpy()
model = Ridge().fit(X, y)               # No train/test split
preds = model.predict(X)                # Predicting on training data
sharpe = (preds * y).mean() / (preds * y).std()  # Meaningless metric
```

### CORRECT
```python
# Each stage reads from upstream artifacts and writes to a known location
from pathlib import Path
import polars as pl
import yaml

CASE_DIR = Path("case_studies/etfs")
config = yaml.safe_load((CASE_DIR / "config" / "setup.yaml").read_text())

# Labels notebook (stage 2) - writes to data/labels/
def create_labels(config: dict):
    prices = pl.read_parquet(CASE_DIR / "data" / "prices.parquet")
    horizon = config["label"]["horizon_days"]
    labels = prices.with_columns(
        fwd_ret=pl.col("close").pct_change(horizon).shift(-horizon).over("symbol"),
    ).select(["timestamp", "symbol", "fwd_ret"]).drop_nulls()
    labels.write_parquet(CASE_DIR / "data" / "labels" / f"fwd_ret_{horizon}d.parquet")

# Features notebook (stage 3) - writes to data/features/
def create_features(config: dict):
    prices = pl.read_parquet(CASE_DIR / "data" / "prices.parquet")
    features = prices.with_columns(
        momentum=pl.col("close").pct_change(63).over("symbol"),
        volatility=pl.col("close").pct_change().rolling_std(21).over("symbol"),
    ).select(["timestamp", "symbol", "momentum", "volatility"]).drop_nulls()
    features.write_parquet(CASE_DIR / "data" / "features" / "financial.parquet")
```

## Pipeline Stages

```
[1. Setup]     setup.yaml: universe, dates, label horizon, CV folds
     |
[2. Labels]    prices -> forward returns, triple-barrier labels
     |
[3. Features]  prices -> momentum, volatility, carry, microstructure
     |
[4. Evaluate]  features + labels -> IC, feature importance, stability
     |
[5. Models]    features + labels + CV -> predictions per fold
     |
[6. Backtest]  predictions -> portfolio weights -> P&L, Sharpe, drawdown
     |
[7. Synthesis] all results -> comparison, selection, final report
```

Each stage reads only from its declared inputs and writes only to its declared outputs. If stage 3 changes, stages 4-7 must re-run. Stages 1-2 are unaffected.

## Artifact Contracts

| Stage | Reads From | Writes To |
|-------|-----------|-----------|
| Setup | Raw data | `config/setup.yaml`, `data/prices.parquet` |
| Labels | `data/prices.parquet` | `data/labels/*.parquet` |
| Features | `data/prices.parquet` | `data/features/*.parquet` |
| Models | `data/features/`, `data/labels/` | `run_log/models/{hash}/` |
| Backtest | `run_log/models/{hash}/predictions.parquet` | `run_log/strategy/{hash}/` |

## Config-Driven Design

One `setup.yaml` file defines the entire case study: dataset, universe filters, label type and horizon, feature list, and CV method with fold counts and embargo. Every notebook reads this config and derives parameters from it. Use `ml4t-case-study-development` for stage-gate decisions; this skill owns the artifact skeleton.

## Guardrails

- Each stage must be runnable independently given its upstream artifacts exist
- Never read raw data in a model notebook - always read from the features stage output
- Stage gates are quantitative: Features pass if IC_IR > 0.5 and worst-fold IC same sign as mean; Models pass if OOS Sharpe > 0 on ≥60% of walk-forward folds
- Config changes require re-running all downstream stages, not just the changed one
- Predictions must include fold identifiers - without them, you cannot reconstruct out-of-sample performance
- Artifact paths use content-addressed hashes for model outputs, not sequential names

## Checklist

- [ ] Pipeline has a single `setup.yaml` defining universe, labels, features, and CV
- [ ] Each stage reads declared inputs and writes declared outputs (no side channels)
- [ ] Labels, features, and predictions are stored as separate artifacts (not one giant DataFrame)
- [ ] Model predictions include fold/split identifiers
- [ ] Re-running a stage with the same config produces the same output (deterministic)
- [ ] Upstream artifact existence is checked before each stage runs
