---
name: ml4t-regime-features
description: Features that capture market regime state
category: features
type: operational
dependencies: [regime-awareness]
book_chapters: [7, 15]
---

# Regime Features

Use regime indicators as features, not for timing.

## Regime Indicators

| Indicator | Interpretation |
|-----------|----------------|
| VIX | Fear/complacency |
| VIX term structure | Stress vs calm |
| Yield curve slope | Growth expectations |
| Credit spreads | Risk appetite |
| Realized volatility | Current turbulence |
| Correlation | Diversification regime |

## Feature Engineering

```python
# Volatility regime
vix_z = (vix - vix.rolling(252).mean()) / vix.rolling(252).std()
vix_high = (vix_z > 1).astype(int)

# Term structure regime
vix_term = (vix_3m - vix) / vix  # Contango vs backwardation

# Yield curve regime
yield_slope = y10 - y2
curve_inverted = (yield_slope < 0).astype(int)

# Correlation regime
corr_matrix = returns.rolling(63).corr()
avg_corr = corr_matrix.mean().mean()
high_corr = (avg_corr > 0.5).astype(int)
```

## HMM Regime Detection

```python
from hmmlearn.hmm import GaussianHMM

# Fit HMM on returns
model = GaussianHMM(n_components=2, covariance_type='full')
model.fit(returns.values.reshape(-1, 1))

# Infer regime (use only past data)
regime = model.predict(returns.values.reshape(-1, 1))
```

## Usage as Feature

```python
# WRONG: Condition entry on regime
if regime == 'bull':
    enter_long()

# CORRECT: Include regime as feature
features['regime_vol'] = vix_z
features['regime_corr'] = avg_corr
features['regime_hmm'] = hmm_state

# Model learns when factors work
model.fit(X_with_regime, y)
```

## Guardrails

- Regime features inform model, don't override it
- Use lagged values (no lookahead)
- Multiple regime indicators for robustness
- HMM regimes have look-ahead risk (use walk-forward)

## Checklist

- [ ] Regime features use only past data
- [ ] Multiple regime indicators included
- [ ] Features, not conditional logic
- [ ] HMM fitted walk-forward if used
