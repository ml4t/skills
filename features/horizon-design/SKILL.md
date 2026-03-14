---
name: ml4t-horizon-design
description: Design prediction horizon aligned with strategy
category: features
type: conceptual
dependencies: [triple-barrier]
book_chapters: [7, 9]
---

# Horizon Design

Prediction horizon must match trading strategy and signal decay.

## Horizon Selection

| Horizon | Strategy Type | Turnover |
|---------|--------------|----------|
| 1-5 days | Mean-reversion | Very high |
| 5-20 days | Momentum | High |
| 20-60 days | Factor | Moderate |
| 60+ days | Value | Low |

## Feature-Horizon Alignment

```python
# WRONG: Misaligned horizons
feature = returns.rolling(5).mean()   # 5-day feature
label = returns.shift(-60)            # 60-day prediction

# CORRECT: Aligned horizons
feature = returns.rolling(60).mean()  # 60-day feature
label = returns.shift(-60)            # 60-day prediction

# Or: Multi-horizon
for horizon in [5, 20, 60]:
    labels[f'ret_{horizon}d'] = returns.shift(-horizon)
```

## Signal Decay Analysis

```python
def ic_decay_analysis(signal: pl.Series, returns: pl.DataFrame) -> dict:
    """Measure how quickly signal loses predictive power."""
    horizons = [1, 5, 10, 20, 40, 60]
    decay = {}

    for h in horizons:
        forward_ret = returns.shift(-h)
        ic = information_coefficient(signal, forward_ret).mean()
        decay[h] = ic

    return decay

# Find optimal horizon (max IC)
optimal = max(decay, key=decay.get)
```

## Transaction Cost Constraint

```python
# Shorter horizons need higher gross returns
# to cover transaction costs

min_alpha_per_trade = transaction_cost * 2.5  # Safety margin
trades_per_year = 252 / avg_holding_period

# Required annual alpha
required_alpha = min_alpha_per_trade * trades_per_year

# If horizon is too short, costs eat alpha
```

## Multi-Horizon Approach

```python
# Different models for different horizons
models = {
    'short': {'horizon': 5, 'features': microstructure_features},
    'medium': {'horizon': 20, 'features': momentum_features},
    'long': {'horizon': 60, 'features': fundamental_features}
}

# Ensemble predictions across horizons
```

## Guardrails

- Shorter horizons need higher turnover capacity
- Feature lookback should roughly match horizon
- Transaction costs constrain minimum horizon
- Signal decay tells you optimal horizon

## Checklist

- [ ] Horizon matches trading frequency
- [ ] Feature lookback aligned to horizon
- [ ] IC decay analysis performed
- [ ] Transaction costs considered
- [ ] Multi-horizon if signal persists
