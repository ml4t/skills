---
name: ml4t-exposure-analysis
description: Analyze factor and sector exposures
category: portfolio
type: operational
dependencies: []
book_chapters: [18, 20]
---

# Exposure Analysis

Decompose portfolio risk into factor exposures.

## Factor Decomposition

```python
from sklearn.linear_model import LinearRegression

def factor_exposures(
    portfolio_returns: np.ndarray,
    factor_returns: np.ndarray,
    factor_names: list
) -> dict:
    """Regress portfolio on factors."""
    model = LinearRegression()
    model.fit(factor_returns, portfolio_returns)

    return {
        'betas': dict(zip(factor_names, model.coef_)),
        'alpha': model.intercept_ * 252,  # Annualized
        'r_squared': model.score(factor_returns, portfolio_returns)
    }
```

## Risk Attribution

```python
def risk_attribution(
    weights: np.ndarray,
    factor_betas: np.ndarray,
    factor_covariance: np.ndarray
) -> dict:
    """Decompose risk into factor and specific."""
    # Factor risk
    port_factor_exposure = weights @ factor_betas
    factor_var = port_factor_exposure @ factor_covariance @ port_factor_exposure

    # Total and specific
    total_var = weights @ full_covariance @ weights
    specific_var = total_var - factor_var

    return {
        'factor_risk_pct': factor_var / total_var,
        'specific_risk_pct': specific_var / total_var,
        'factor_contributions': port_factor_exposure ** 2 * np.diag(factor_covariance)
    }
```

## Sector Exposure

```python
def sector_exposure(
    weights: np.ndarray,
    sector_mapping: dict  # asset -> sector
) -> dict:
    """Net exposure by sector."""
    exposure = {}
    for i, w in enumerate(weights):
        sector = sector_mapping[i]
        exposure[sector] = exposure.get(sector, 0) + w
    return exposure
```

## Style Analysis

```python
def style_analysis(
    portfolio_returns: np.ndarray,
    style_indices: dict  # name -> returns
) -> dict:
    """Determine style exposures with constraints."""
    from scipy.optimize import minimize

    X = np.column_stack(list(style_indices.values()))

    def objective(w):
        predicted = X @ w
        return np.sum((portfolio_returns - predicted) ** 2)

    # Weights sum to 1, non-negative (style box)
    result = minimize(
        objective,
        np.ones(len(style_indices)) / len(style_indices),
        constraints=[{'type': 'eq', 'fun': lambda w: sum(w) - 1}],
        bounds=[(0, 1) for _ in style_indices]
    )

    return dict(zip(style_indices.keys(), result.x))
```

## Monitoring Dashboard

```python
def exposure_summary(weights: np.ndarray, metadata: dict) -> dict:
    """Generate exposure summary for monitoring."""
    return {
        'net_exposure': weights.sum(),
        'gross_exposure': np.abs(weights).sum(),
        'long_exposure': weights[weights > 0].sum(),
        'short_exposure': weights[weights < 0].sum(),
        'concentration': (weights ** 2).sum(),  # HHI
        'top_5_weight': np.sort(np.abs(weights))[-5:].sum()
    }
```

## Guardrails

- Factor betas change over time; use rolling
- Sector weights should align with thesis
- Monitor concentration (HHI)
- Compare to benchmark exposures

## Checklist

- [ ] Factor exposures calculated
- [ ] Sector weights documented
- [ ] Concentration monitored
- [ ] Exposure limits defined
