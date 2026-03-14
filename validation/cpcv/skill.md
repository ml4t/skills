---
name: ml4t-cpcv
description: Combinatorial Purged Cross-Validation for robust backtesting
category: validation
type: operational
dependencies: [purging-embargo]
book_chapters: [10, 12]
quantlab_module: ml4t.diagnostic.splitters
---

# Combinatorial Purged CV

Generates multiple backtest paths (not just one) to detect overfitting.

## How It Works

1. Partition data into N groups
2. Generate C(N,k) combinations of test groups
3. Apply purging and embargo to each
4. Get distribution of results, not single number

## API

```python
from ml4t.diagnostic.splitters import CombinatorialPurgedCV

cv = CombinatorialPurgedCV(
    n_groups=8,              # Partition into 8 groups
    n_test_groups=2,         # 2 groups per test set → C(8,2)=28 combos
    label_horizon=5,         # Purge: labels look 5 periods forward
    embargo_size=2,          # Buffer after test set
    max_combinations=20,     # Limit for efficiency
    random_state=42
)

for train_idx, test_idx in cv.split(X):
    model.fit(X[train_idx], y[train_idx])
    score = model.score(X[test_idx], y[test_idx])
```

## Multi-Asset

```python
cv = CombinatorialPurgedCV(
    n_groups=6,
    n_test_groups=2,
    label_horizon=5,
    isolate_groups=True  # Per-asset purging
)

for train_idx, test_idx in cv.split(X, groups=symbols):
    # Purging applied independently per asset
    pass
```

## Parameter Selection

| n_groups | n_test_groups | Combinations |
|----------|---------------|--------------|
| 6 | 2 | 15 |
| 8 | 2 | 28 (standard) |
| 10 | 3 | 120 |

- `label_horizon`: Match your label construction (e.g., 5-day returns → 5)
- `embargo_size`: ~10-20% of label_horizon

## Guardrails

- Check variance across folds (high = not robust)
- Use Deflated Sharpe Ratio for statistical significance
- PBO > 50% suggests overfitting
