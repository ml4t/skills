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

def purged(split, horizon):
    """Drop training rows whose label window reaches into the test fold."""
    for train, test in split:
        yield train[train < test[0] - horizon], test

def oof_signal(X, y, splits):
    """Primary predictions, each from a model that never saw that row."""
    out = np.zeros(len(X))
    for train, test in splits:
        out[test] = fit_primary(X[train], y[train]).predict(X[test])
    return out

signal = np.zeros(len(X))
prob_win = np.full(len(X), np.nan)
for train, test in purged(TimeSeriesSplit(n_splits=5).split(X), horizon):
    # Inner folds first. Fitting the meta-model on primary predictions the
    # primary made in sample teaches it the primary's memorisation, not its edge.
    inner = purged(TimeSeriesSplit(n_splits=3).split(X[train]), horizon)
    fired = oof_signal(X[train], y[train], inner) != 0
    meta = GradientBoostingClassifier(n_estimators=100, max_depth=3)
    meta.fit(X[train][fired], outcomes[train][fired])  # 1=profitable, 0=not

    signal[test] = fit_primary(X[train], y[train]).predict(X[test])
    acted = test[signal[test] != 0]
    prob_win[acted] = meta.predict_proba(X[acted])[:, 1]

positions = np.where(prob_win > 0.55, signal, 0.0)   # NaN compares False
```

## Two-Stage Architecture

```
Primary Model ──→ Signal (direction + timing)
                    │
                    ▼ (only where signal fired)
Meta-Model    ──→ P(profitable) ──→ Filter / Size position
```

The meta-model receives the *same features* plus signal-specific ones: the
primary's own confidence, the current volatility regime, and its rolling hit
rate. Build them from the outer training fold only, like everything else here.

## Position Sizing

```python
# Kelly-inspired sizing: size proportional to edge. Every prob_win above is an
# out-of-fold score; refit on all of it for rows after the last fold.
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
