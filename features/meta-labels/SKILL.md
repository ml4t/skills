---
name: ml4t-meta-labels
description: "Secondary model predicts whether a primary signal will be profitable. Use when sizing positions or filtering low-conviction trades from a base alpha model."
when_to_use: "Use when a signal has decent recall but too many false positives"
dependencies: [triple-barrier]
metadata:
  book_chapters: "7"
  library: "ml4t-engineer"
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
---
# Meta-Labels

A momentum signal fires 1,000 times per year but only 40% are profitable. Instead of discarding the signal, train a second model to predict *which* of those 1,000 trades will work.

## The Problem

Raw trading signals typically have acceptable recall (they catch most real moves) but poor precision (many false positives). Tuning the primary model to improve precision degrades recall. Meta-labeling decouples the two: the primary model generates candidates, the meta-model filters them.

## The Pattern

### WRONG
```python
from sklearn.ensemble import GradientBoostingClassifier

# Use raw signal directly - many false positives passed through
signal = primary_model.predict(X)  # 1=buy, -1=sell, 0=hold
positions = signal  # Every signal becomes a trade
```

### CORRECT
```python
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit

# Stage 1: primary signal (direction). These have to BE out-of-fold predictions
# already - a primary fitted on X leaks its training rows into the meta-model.
signal = primary_model.predict(X)  # 1=buy, -1=sell, 0=hold

# Stage 2: Meta-model filters which signals to act on
fired = np.flatnonzero(signal != 0)
X_meta, y_meta = X[fired], outcomes[fired]  # outcomes: 1=profitable, 0=not

# The meta-model has to score rows it did not fit. Fitting and predicting on
# the same samples grades the filter on its own training set.
prob_win = np.full(len(fired), np.nan)
for train, test in TimeSeriesSplit(n_splits=5).split(X_meta):  # purge: ml4t-purging-embargo
    meta_model = GradientBoostingClassifier(n_estimators=100, max_depth=3)
    meta_model.fit(X_meta[train], y_meta[train])
    prob_win[test] = meta_model.predict_proba(X_meta[test])[:, 1]

positions = np.zeros(len(X))
positions[fired] = signal[fired] * (prob_win > 0.55)  # NaN compares False
```

## Two-Stage Architecture

```
Primary Model ──→ Signal (direction + timing)
                    │
                    ▼ (only where signal fired)
Meta-Model    ──→ P(profitable) ──→ Filter / Size position
```

The meta-model receives the *same features* plus signal-specific features:

```python
# Additional features for the meta-model
meta_features = np.column_stack([
    X[fired],                           # Original features
    np.abs(signal_score[fired]),        # Primary model confidence
    volatility[fired],                  # Current vol regime
    recent_win_rate[fired],             # Rolling hit rate of primary
])
```

## Position Sizing

Meta-label probabilities naturally map to position sizes:

```python
# Kelly-inspired sizing: size proportional to edge. Size history from the
# out-of-fold prob_win above; the last fold's model is for future rows only.
edge = 2 * np.nan_to_num(prob_win, nan=0.5) - 1  # unscored rows get zero size
position_size = base_size * np.clip(edge, 0, 1)
```

## Guardrails

- **Meta-model never overrides direction** - it only decides whether to act, and how much
- **Separate CV for primary and meta** - meta-model must not see primary's test data
- **Requires sufficient primary signals** - if primary fires <100 times, meta-model will overfit

## Production Implementation

`ml4t-engineer` provides integrated meta-labeling with triple-barrier outcomes:

```python
from ml4t.engineer.config import LabelingConfig
from ml4t.engineer.labeling import atr_triple_barrier_labels, meta_labels

config = LabelingConfig.atr_barrier(
    atr_tp_multiple=2.0,
    atr_sl_multiple=1.5,
    atr_period=14,
    max_holding_period=10,
)
labeled = atr_triple_barrier_labels(df, config=config, price_col="close")
labeled = labeled.with_columns(primary_signal.alias("signal"))
meta = meta_labels(labeled, signal_col="signal", return_col="label_return")
# Returns: original signal plus binary meta_label for trade filtering/sizing
```

## Checklist

- [ ] Primary model has persistent, fold-stable IC (check worst-fold, not just mean)
- [ ] Meta-model trained only on samples where primary signal fired
- [ ] CV is nested: primary and meta models use separate folds
- [ ] Meta-model probability used for position sizing or filtering
- [ ] Sufficient signal count (>200) to train meta-model reliably
