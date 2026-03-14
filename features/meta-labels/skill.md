---
name: ml4t-meta-labels
description: Secondary model for bet sizing and filtering
category: features
type: operational
dependencies: [triple-barrier]
book_chapters: [7, 9]
quantlab_module: ml4t.engineer.labels
---

# Meta-Labels

Train a secondary model to size bets from a primary signal.

## Concept

```
Primary Model → Binary signal (buy/sell)
Meta Model   → Probability of success (0-1)

Position Size ∝ P(win) from meta model
```

## API

```python
from ml4t.engineer.labels import generate_meta_labels

# Step 1: Generate primary signals
primary_signal = rule_based_strategy(data)  # 1 = buy, -1 = sell, 0 = hold

# Step 2: Get outcomes for each signal
meta_labels = generate_meta_labels(
    signal=primary_signal,
    returns=forward_returns,
    barrier_config=config  # Triple barrier
)
# Returns: side (from signal), outcome (1 if profitable)
```

## Two-Stage Training

```python
# Stage 1: Primary model (direction)
primary_model.fit(X, y_direction)
primary_signal = primary_model.predict(X)

# Stage 2: Meta model (win probability)
# Only train on samples where primary fired
mask = primary_signal != 0
meta_model.fit(X[mask], y_outcome[mask])

# Position sizing
prob_win = meta_model.predict_proba(X)[:, 1]
position_size = prob_win * base_position
```

## Meta Features

```python
# Features for meta model can include:
meta_features = [
    'primary_model_probability',  # Confidence of primary
    'signal_strength',            # Magnitude of primary signal
    'regime_indicator',           # Market condition
    'volatility',                 # Current vol
    'recent_hit_rate',            # Rolling accuracy
]
```

## Guardrails

- Meta model only trains on triggered signals
- Separate CV for primary and meta models
- Meta model filters/sizes, doesn't override direction
- High meta probability = larger position

## Checklist

- [ ] Primary signal defined (rule or model)
- [ ] Meta labels use triple-barrier outcomes
- [ ] Meta model trained only on fired signals
- [ ] Position sizing uses meta probability
