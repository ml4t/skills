---
name: ml4t-synthetic-data
description: Generate realistic synthetic financial data for pipeline testing and stress scenarios. Use when you need ground-truth data or want to test strategies under controlled conditions.
dependencies: []
metadata:
  book_chapters: "5"
  library: ""
---

# Synthetic Data

Using i.i.d. normal returns to test a trading pipeline misses the features that break strategies in practice: volatility clustering, fat tails, and cross-asset correlation spikes during stress.

## The Problem

Real financial returns have autocorrelated volatility (calm periods cluster, so do volatile ones), fat tails (extreme moves happen 10x more often than a normal distribution predicts), and time-varying correlations (assets that are uncorrelated in normal markets become correlated in crashes). Testing a pipeline on i.i.d. Gaussian noise validates nothing — it will pass every strategy because none of the real-world failure modes are present. You need synthetic data that preserves these statistical properties.

## The Pattern

### WRONG
```python
import numpy as np

# i.i.d. normal returns — no clustering, no fat tails, no structure
returns = np.random.normal(0.0004, 0.01, size=(252, 10))
prices = 100 * np.exp(np.cumsum(returns, axis=0))
# Pipeline passes on this, fails on real data
```

### CORRECT
```python
import numpy as np

def generate_gbm_with_jumps(
    n_days: int = 252,
    mu: float = 0.08,
    sigma: float = 0.20,
    jump_prob: float = 0.02,
    jump_mean: float = -0.03,
    jump_std: float = 0.04,
    s0: float = 100.0,
) -> np.ndarray:
    """GBM with Poisson jumps — captures fat tails from rare large moves."""
    dt = 1 / 252
    # Diffusion component
    dW = np.random.normal(0, np.sqrt(dt), n_days)
    diffusion = (mu - 0.5 * sigma**2) * dt + sigma * dW

    # Jump component (compound Poisson)
    jumps = np.where(
        np.random.random(n_days) < jump_prob,
        np.random.normal(jump_mean, jump_std, n_days),
        0.0,
    )

    log_returns = diffusion + jumps
    return s0 * np.exp(np.cumsum(log_returns))
```

## Preserving Volatility Clustering

GARCH(1,1) generates returns where today's volatility depends on yesterday's shock — matching the clustering seen in real markets.

```python
def generate_garch_returns(
    n_days: int = 252,
    omega: float = 1e-6,
    alpha: float = 0.09,
    beta: float = 0.90,
    mu: float = 0.0003,
) -> np.ndarray:
    """GARCH(1,1) returns with volatility clustering."""
    returns = np.zeros(n_days)
    sigma2 = np.full(n_days, omega / (1 - alpha - beta))  # Unconditional variance

    for t in range(1, n_days):
        sigma2[t] = omega + alpha * returns[t-1]**2 + beta * sigma2[t-1]
        returns[t] = mu + np.sqrt(sigma2[t]) * np.random.standard_t(df=5)  # Fat tails via t-dist

    return returns
```

## Stationary Bootstrap

Resample real returns in blocks to preserve autocorrelation structure without parametric assumptions.

```python
def stationary_bootstrap(
    returns: np.ndarray, block_size: float = 10.0, seed: int = 42,
) -> np.ndarray:
    """Block bootstrap with geometric block lengths."""
    rng = np.random.default_rng(seed)
    T = len(returns)
    result = np.empty(T)
    p = 1.0 / block_size
    idx = rng.integers(T)
    for t in range(T):
        result[t] = returns[idx]
        idx = rng.integers(T) if rng.random() < p else (idx + 1) % T
    return result
```

## Guardrails

- Synthetic data validates pipelines and logic, not strategy profitability — always re-test on real data
- GBM alone misses volatility clustering — add GARCH or regime switching for realistic dynamics
- Cross-asset synthetic data must model correlations (use copulas or correlated Brownian motions)
- Set random seeds for reproducibility: `np.random.default_rng(seed)`
- Compare synthetic statistics (kurtosis, autocorrelation of squared returns) against real data to verify realism

## Checklist

- [ ] Synthetic data purpose documented (testing, stress, augmentation)
- [ ] Fat tails included (jump diffusion or t-distribution)
- [ ] Volatility clustering present (GARCH or regime switching)
- [ ] Parameters calibrated from real market statistics
- [ ] Random seed set for reproducibility
- [ ] Pipeline also tested on real data before any conclusions
