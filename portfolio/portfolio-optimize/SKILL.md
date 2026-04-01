---
name: ml4t-portfolio-optimize
description: "Construct optimal portfolios using mean-variance with shrinkage and constraints. Use when converting alpha signals into target portfolio weights."
when_to_use: "Use when combining multiple alpha signals or assets into a single portfolio"
dependencies: [position-sizing]
metadata:
  book_chapters: "17"
  library: ""
paths: ["**/*portfolio*.py", "**/*position*.py", "**/*risk*.py", "**/*optim*.py", "**/*exposure*.py", "**/*kill*.py", "**/*stress*.py"]
---
# Portfolio Optimization

Unconstrained Markowitz produces portfolios that are optimal in-sample and catastrophic out-of-sample. Estimation error in expected returns and covariances gets amplified into extreme, unstable weights.

## The Problem

Mean-variance optimization maximizes expected return for a given risk level, but it treats its inputs as truth. With N assets, the covariance matrix has N(N+1)/2 parameters — all estimated with error. The optimizer exploits these errors, concentrating in assets whose returns are overestimated and covariances underestimated. A 100-asset optimizer can produce 300% long / 200% short positions that flip completely with one more month of data.

## The Pattern

### WRONG
```python
import numpy as np
from scipy.optimize import minimize

# Naive Markowitz with sample estimates
mu = returns.mean(axis=0) * 252
cov = np.cov(returns, rowvar=False) * 252

def neg_sharpe(w):
    ret = w @ mu
    vol = np.sqrt(w @ cov @ w)
    return -ret / vol

n = len(mu)
result = minimize(neg_sharpe, np.ones(n) / n, method="SLSQP",
                  constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
# Result: extreme weights, massive turnover, poor OOS performance
```

### CORRECT
```python
import numpy as np
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize

# Shrinkage covariance — far more stable
lw = LedoitWolf().fit(returns)
cov = lw.covariance_ * 252

# Minimum variance (avoids estimating expected returns entirely)
n = cov.shape[0]

def portfolio_var(w):
    return w @ cov @ w

result = minimize(
    portfolio_var, np.ones(n) / n, method="SLSQP",
    bounds=[(0.0, 0.05)] * n,  # max 5% per asset
    constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
)
weights = result.x
```

## Practical Alternatives to Markowitz

| Method | Avoids Estimating | Best When |
|--------|-------------------|-----------|
| Minimum variance | Expected returns | You trust covariance more than returns |
| Risk parity | Both (uses vol only) | You want diversification, not alpha |
| Black-Litterman | Raw sample returns | You have views but want stable base |
| Shrinkage MVO | Nothing, but stabilizes | You need full optimization with guardrails |

## Risk Parity

```python
def risk_parity(cov: np.ndarray) -> np.ndarray:
    """Equal risk contribution — needs only covariance."""
    n = cov.shape[0]
    def objective(w):
        vol = np.sqrt(w @ cov @ w)
        rc = w * (cov @ w) / vol  # risk contributions
        return ((rc - vol / n) ** 2).sum()

    result = minimize(objective, np.ones(n) / n, method="SLSQP",
                      bounds=[(0.01, 1.0)] * n,
                      constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
    return result.x
```

## Guardrails

- Always use shrinkage (Ledoit-Wolf or Oracle Approximating) — sample covariance is never acceptable for optimization
- Prefer minimum variance or risk parity when return forecasts are weak (IC < 0.05)
- Bound individual weights (1-5% typical) — unconstrained solutions are always wrong
- Monitor turnover — high turnover signals unstable estimates, not real alpha
- Rebalance no more than weekly unless transaction costs are near zero

## Checklist

- [ ] Covariance estimated with shrinkage (LedoitWolf or similar)
- [ ] Individual position bounds set (typically 1-5%)
- [ ] Method matched to signal quality (min-var if IC is weak)
- [ ] Turnover computed and within cost budget
- [ ] Out-of-sample backtest confirms stability vs equal-weight baseline
