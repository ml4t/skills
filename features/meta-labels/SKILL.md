---
name: ml4t-meta-labels
description: Two-stage labeling where a secondary model predicts whether a primary signal will be profitable. Use when a signal has decent recall but too many false positives.
dependencies: [triple-barrier]
metadata:
  book_chapters: "7"
  library: "ml4t-engineer"
---

# Meta-Labels

A momentum signal fires 1,000 times per year but only 40% are profitable. Instead of discarding the signal, train a second model to predict *which* of those 1,000 trades will work.

## The Problem

Raw trading signals typically have acceptable recall (they catch most real moves) but poor precision (many false positives). Tuning the primary model to improve precision degrades recall. Meta-labeling decouples the two: the primary model generates candidates, the meta-model filters them.

## The Pattern

### WRONG
```python
from sklearn.ensemble import GradientBoostingClassifier

# Use raw signal directly — many false positives passed through
signal = primary_model.predict(X)  # 1=buy, -1=sell, 0=hold
positions = signal  # Every signal becomes a trade
```

### CORRECT
```python
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

# Stage 1: Primary signal (direction)
signal = primary_model.predict(X)  # 1=buy, -1=sell, 0=hold

# Stage 2: Meta-model filters which signals to act on
fired = signal != 0
X_meta, y_meta = X[fired], outcomes[fired]  # outcomes: 1=profitable, 0=not

meta_model = GradientBoostingClassifier(n_estimators=100, max_depth=3)
meta_model.fit(X_meta, y_meta)

# Only trade when meta-model agrees
prob_win = meta_model.predict_proba(X[fired])[:, 1]
positions = np.zeros(len(X))
positions[fired] = signal[fired] * (prob_win > 0.55)  # Filter low-confidence
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
# Kelly-inspired sizing: size proportional to edge
prob = meta_model.predict_proba(X_meta)[:, 1]
edge = 2 * prob - 1  # Maps [0.5, 1.0] → [0, 1]
position_size = base_size * np.clip(edge, 0, 1)
```

## Guardrails

- **Train meta-model only on triggered signals** — never on the full dataset
- **Separate CV for primary and meta** — meta-model must not see primary's test data
- **Meta-model never overrides direction** — it only decides whether to act and how much
- **Requires sufficient primary signals** — if primary fires <100 times, meta-model will overfit

## Production Implementation

`ml4t-engineer` provides integrated meta-labeling with triple-barrier outcomes:

```python
from ml4t.engineer.labeling import generate_meta_labels, triple_barrier
from ml4t.engineer.labeling.barriers import ATRBarrierConfig

config = ATRBarrierConfig(upper_multiplier=2.0, lower_multiplier=1.5, atr_period=14)
meta_labels = generate_meta_labels(
    signal=primary_signal, returns=forward_returns, barrier_config=config,
)
# Returns: side (from signal), outcome (1 if profitable, 0 if not)
```

## Checklist

- [ ] Primary model generates directional signals with adequate recall
- [ ] Meta-model trained only on samples where primary signal fired
- [ ] CV is nested: primary and meta models use separate folds
- [ ] Meta-model probability used for position sizing or filtering
- [ ] Sufficient signal count (>200) to train meta-model reliably
