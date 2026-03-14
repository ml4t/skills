---
name: ml4t-synthetic-data
description: Generate synthetic data for testing and augmentation
category: data
type: operational
dependencies: []
book_chapters: [6]
---

# Synthetic Data

Generate artificial data for testing pipelines and stress scenarios.

## Use Cases

| Purpose | Method |
|---------|--------|
| Pipeline testing | Known ground truth |
| Stress testing | Extreme scenarios |
| Data augmentation | Expand training set |
| Sensitivity analysis | Parameter perturbation |

## GBM (Geometric Brownian Motion)

```python
import numpy as np

def generate_gbm(
    n_steps: int = 252,
    mu: float = 0.10,      # Annual drift
    sigma: float = 0.20,   # Annual volatility
    s0: float = 100,
    dt: float = 1/252      # Daily
) -> np.ndarray:
    """Generate GBM price path."""
    dW = np.random.normal(0, np.sqrt(dt), n_steps)
    returns = (mu - 0.5 * sigma**2) * dt + sigma * dW
    log_prices = np.log(s0) + np.cumsum(returns)
    return np.exp(log_prices)
```

## Regime-Switching

```python
def generate_regime_switching(
    n_steps: int = 252,
    regimes: dict = {
        'bull': {'mu': 0.15, 'sigma': 0.12, 'prob': 0.7},
        'bear': {'mu': -0.10, 'sigma': 0.30, 'prob': 0.3}
    }
) -> tuple[np.ndarray, np.ndarray]:
    """Generate price with regime switches."""
    regime = np.random.choice(
        list(regimes.keys()),
        size=n_steps,
        p=[r['prob'] for r in regimes.values()]
    )
    # Generate returns conditional on regime
    ...
    return prices, regime
```

## Bootstrap

```python
def stationary_bootstrap(
    returns: np.ndarray,
    n_samples: int = 1000,
    block_size: float = 10.0  # Average block length
) -> np.ndarray:
    """Generate bootstrap samples preserving autocorrelation."""
    T = len(returns)
    samples = np.zeros((n_samples, T))
    p = 1 / block_size

    for i in range(n_samples):
        idx = np.random.randint(T)
        for t in range(T):
            if np.random.random() < p:
                idx = np.random.randint(T)
            samples[i, t] = returns[idx]
            idx = (idx + 1) % T

    return samples
```

## Guardrails

- Synthetic data validates pipelines, not strategies
- Real market features (fat tails, clustering) are hard to replicate
- Always test on real data before deployment
- Document synthetic data parameters

## Checklist

- [ ] Purpose of synthetic data documented
- [ ] Parameters chosen from realistic ranges
- [ ] Used for testing, not final validation
- [ ] Real data tests also performed
