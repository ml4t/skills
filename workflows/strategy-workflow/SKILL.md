---
name: ml4t-strategy-workflow
description: End-to-end strategy development workflow
category: workflows
type: workflow
dependencies: [strategy-term-sheet, fetch-data, compute-features, triple-barrier, cpcv, run-backtest, tearsheet]
book_chapters: [1, 2, 17]
---

# Strategy Workflow

Complete workflow from hypothesis to validated strategy.

## Stage Overview

```
1. Hypothesis → 2. Data → 3. Features → 4. Labels → 5. Model → 6. Backtest → 7. Validate
```

## Stage 1: Hypothesis

```yaml
# Document in term sheet BEFORE coding
hypothesis:
  mechanism: "Why does this work?"
  metric: "What predicts what?"
  outcome: "Success criteria (pre-defined)"
  durability: "Why will it persist?"

# Commit to git
git commit -m "Pre-registered hypothesis"
```

## Stage 2: Data

```python
from ml4t_code.loaders import load_etf_universe

# Load and validate
data = load_etf_universe()
validate_data(data)
align_to_calendar(data, 'XNYS')
```

## Stage 3: Features

```python
from ml4t.engineer.features import compute_features

features = compute_features(
    data,
    feature_list=['momentum_12m', 'volatility_20d', 'value_pb']
)
validate_features(features)
```

## Stage 4: Labels

```python
from ml4t.engineer.labels import triple_barrier

labels = triple_barrier(
    prices=data['close'],
    config=BarrierConfig(
        profit_take=0.02,
        stop_loss=-0.02,
        max_holding=5
    )
)
```

## Stage 5: Model

```python
from ml4t.diagnostic.splitters import CombinatorialPurgedCV

cv = CombinatorialPurgedCV(n_groups=10, n_test_groups=2, purge_gap=5)

for train_idx, test_idx in cv.split(features):
    model.fit(features[train_idx], labels[train_idx])
    preds = model.predict(features[test_idx])
```

## Stage 6: Backtest

```python
from ml4t.backtest import run_backtest

results = run_backtest(
    strategy=MyStrategy(model),
    data=data,
    costs=CostModel(commission_bps=1, spread_bps=5)
)
```

## Stage 7: Validate

```python
from ml4t.diagnostic.metrics import (
    deflated_sharpe_ratio,
    probability_of_backtest_overfitting
)

dsr = deflated_sharpe_ratio(results.sharpe, n_trials=10)
pbo = probability_of_backtest_overfitting(cv_sharpes)

print(f"DSR: {dsr:.2f}, PBO: {pbo:.1%}")
# Proceed only if DSR > 0.5 and PBO < 50%
```

## Checkpoints

- [ ] Hypothesis documented and committed
- [ ] Data validated, calendar-aligned
- [ ] Features stationarity-tested
- [ ] Labels use triple-barrier
- [ ] CV uses purging and embargo
- [ ] Costs included in backtest
- [ ] DSR and PBO calculated
