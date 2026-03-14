---
name: ml4t-portfolio-optimize
description: Optimize portfolio weights for risk-return trade-offs
category: portfolio
type: operational
dependencies: [position-sizing]
book_chapters: [18]
---

# Portfolio Optimization

Optimize weights for expected return and risk.

## Methods

| Method | Objective | Inputs |
|--------|-----------|--------|
| Mean-variance | max(μ - λσ²) | Returns, covariance |
| Min variance | min(σ²) | Covariance only |
| Risk parity | Equal risk contribution | Covariance |
| Max Sharpe | max(μ/σ) | Returns, covariance |

## Mean-Variance

```python
from scipy.optimize import minimize

def mean_variance_optimize(
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    risk_aversion: float = 1.0,
    constraints: dict = None
) -> np.ndarray:
    """Classic Markowitz optimization."""
    n = len(expected_returns)

    def objective(w):
        port_ret = w @ expected_returns
        port_var = w @ covariance @ w
        return -(port_ret - risk_aversion * port_var)

    # Constraints
    cons = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]  # Fully invested

    # Bounds
    bounds = [(0, 1) for _ in range(n)]  # Long only

    result = minimize(objective, np.ones(n)/n, method='SLSQP',
                      bounds=bounds, constraints=cons)
    return result.x
```

## Risk Parity

```python
def risk_parity_weights(covariance: np.ndarray) -> np.ndarray:
    """Equal risk contribution portfolio."""
    n = covariance.shape[0]

    def risk_contribution(w):
        port_var = w @ covariance @ w
        marginal = covariance @ w
        return w * marginal / np.sqrt(port_var)

    def objective(w):
        rc = risk_contribution(w)
        target = np.ones(n) / n  # Equal RC
        return np.sum((rc - target) ** 2)

    result = minimize(objective, np.ones(n)/n, method='SLSQP',
                      bounds=[(0.01, 1) for _ in range(n)],
                      constraints=[{'type': 'eq', 'fun': lambda w: sum(w) - 1}])
    return result.x
```

## Robust Estimation

```python
from sklearn.covariance import LedoitWolf

def robust_covariance(returns: np.ndarray) -> np.ndarray:
    """Shrinkage estimator for stability."""
    lw = LedoitWolf()
    lw.fit(returns)
    return lw.covariance_
```

## Black-Litterman

```python
def black_litterman(
    market_weights: np.ndarray,
    covariance: np.ndarray,
    views: np.ndarray,       # P matrix: which assets
    view_returns: np.ndarray, # Q vector: expected returns
    tau: float = 0.05,
    omega: np.ndarray = None  # View uncertainty
) -> np.ndarray:
    """Incorporate views into equilibrium."""
    if omega is None:
        omega = np.diag(np.diag(views @ covariance @ views.T)) * tau

    # Prior (equilibrium returns)
    pi = covariance @ market_weights

    # Posterior
    M = np.linalg.inv(np.linalg.inv(tau * covariance) + views.T @ np.linalg.inv(omega) @ views)
    posterior = M @ (np.linalg.inv(tau * covariance) @ pi + views.T @ np.linalg.inv(omega) @ view_returns)

    return posterior
```

## Guardrails

- Sample covariance is unstable; use shrinkage
- Expected returns are hardest to estimate
- Constraints prevent corner solutions
- Rebalancing costs matter

## Checklist

- [ ] Covariance estimated with shrinkage
- [ ] Constraints prevent concentration
- [ ] Method matched to available inputs
- [ ] Turnover considered
