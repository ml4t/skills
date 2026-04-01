---
name: ml4t-dl-time-series
description: "Deep learning for financial time series — LSTM, Transformers, and when they lose to simpler models. Use when evaluating whether DL adds value over tabular baselines."
when_to_use: "Use when considering LSTM, Transformer, or other DL architectures for return forecasting"
dependencies: [compute-features, walk-forward-cv]
paths: ["**/*agent*.py", "**/*rl*.py", "**/*rag*.py", "**/*graph*.py", "**/*knowledge*.py", "**/*orchestrat*.py"]
metadata:
  book_chapters: "13"
  library: ""
---
# Deep Learning for Time Series

An LSTM trained on 5 years of daily returns underperforms LightGBM in 6 of 7 asset classes. Deep learning adds value for financial time series only under specific conditions — high frequency, strong sequential structure, and sufficient data.

## The Problem

DL architectures promise to learn temporal dependencies automatically. In practice, engineered features (momentum, volatility, carry) already encode the temporal structure that matters for returns. The DL model learns a noisy approximation of what a feature pipeline provides directly. Worse, Transformers' permutation-invariance means they largely ignore temporal order — shuffling the input sequence barely degrades performance on many financial datasets.

## The Pattern

### WRONG
```python
import torch
import torch.nn as nn

# Jump straight to LSTM without establishing baselines
class ReturnPredictor(nn.Module):
    def __init__(self, n_features, hidden=128, n_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, n_layers, batch_first=True)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x):
        _, (h, _) = self.lstm(x)
        return self.fc(h[-1])

# Train on raw returns without comparing to Ridge or GBM
model = ReturnPredictor(n_features=20)
# ... training loop ...
print(f"Test IC: {test_ic:.4f}")  # Is this better than a linear model?
```

### CORRECT
```python
import numpy as np
from sklearn.linear_model import Ridge
from lightgbm import LGBMRegressor

# Step 1: Establish baselines FIRST
baselines = {
    "ridge": Ridge(alpha=1.0),
    "lgbm": LGBMRegressor(n_estimators=200, max_depth=4, learning_rate=0.05),
}

for name, model in baselines.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    ic = np.corrcoef(pred, y_test)[0, 1]
    print(f"{name}: IC={ic:.4f}")

# Step 2: DL only if baselines leave room AND you have:
#   - >10K samples per fold
#   - Sub-daily frequency OR strong sequential structure
#   - Computational budget for proper hyperparameter search
# Step 3: Compare DL to baselines on SAME walk-forward folds
```

## When DL Adds Value

| Condition | DL Advantage | Example |
|-----------|-------------|---------|
| High frequency (intraday+) | Learns microstructure patterns | Order flow, LOB features |
| Strong sequential dependence | Captures path-dependent signals | Crypto funding rates |
| Multi-modal inputs | Fuses text + price + fundamentals | Earnings call + returns |
| Large sample size (>50K) | Enough data to learn non-linear interactions | Cross-sectional panels |

DL rarely beats GBM on: daily equity returns, monthly factor models, or small-universe strategies.

## Baseline Ladder

Always compare DL against this progression:

1. **Naive** — predict zero (establishes noise floor)
2. **Linear** — Ridge regression on engineered features
3. **GBM** — LightGBM with early stopping on validation IC
4. **D-Linear** — simple linear model on decomposed trend + seasonal
5. **LSTM / Transformer** — only if steps 1-4 leave clear room

## Guardrails

- **Baseline first**: never report DL results without Ridge + GBM comparison on same folds
- **Walk-forward only**: DL models must use temporal CV — no random train/test splits
- **Fold-local scaling**: fit StandardScaler per fold on training data only, never globally
- **Early stopping on validation IC**: not training loss — training loss misleads for return prediction
- **Reproducibility**: fix random seeds, report mean +/- std across 5+ seeds

## Production Implementation

No ml4t-* library provides DL models. Use PyTorch with walk-forward discipline:

```python
import torch
from sklearn.preprocessing import StandardScaler
from ml4t.diagnostic.splitters import WalkForwardCV

cv = WalkForwardCV(n_splits=5, expanding=True, label_horizon=5, embargo_size=2)
for train_idx, test_idx in cv.split(X):
    # Fold-local scaling
    scaler = StandardScaler().fit(X[train_idx])
    X_tr = torch.tensor(scaler.transform(X[train_idx]), dtype=torch.float32)
    X_te = torch.tensor(scaler.transform(X[test_idx]), dtype=torch.float32)
    # Train DL model with early stopping on validation IC
```

## Checklist

- [ ] Ridge and GBM baselines established on same walk-forward folds
- [ ] DL justified: high frequency, sequential structure, or sufficient data; scaling per fold
- [ ] Early stopping uses validation IC, not training loss
- [ ] Results reported as mean +/- std across multiple seeds
