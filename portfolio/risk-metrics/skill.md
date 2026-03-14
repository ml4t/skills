---
name: ml4t-risk-metrics
description: Calculate portfolio risk measures (VaR, CVaR, drawdown)
category: portfolio
type: operational
dependencies: []
book_chapters: [20]
---

# Risk Metrics

Measure and monitor portfolio risk.

## Key Metrics

| Metric | Definition | Use |
|--------|------------|-----|
| Volatility | std(returns) * sqrt(252) | Baseline risk |
| VaR | Quantile of loss distribution | Tail risk |
| CVaR (ES) | Expected loss beyond VaR | Extreme risk |
| Max DD | Largest peak-to-trough | Drawdown risk |
| Sortino | return / downside_std | Downside-focused |

## Value at Risk

```python
def var(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Historical VaR."""
    return np.percentile(returns, (1 - confidence) * 100)

def var_parametric(
    portfolio_return: float,
    portfolio_vol: float,
    confidence: float = 0.95
) -> float:
    """Parametric VaR assuming normality."""
    from scipy.stats import norm
    z = norm.ppf(1 - confidence)
    return portfolio_return + z * portfolio_vol
```

## Conditional VaR (Expected Shortfall)

```python
def cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Expected loss beyond VaR."""
    var_threshold = var(returns, confidence)
    return returns[returns <= var_threshold].mean()
```

## Maximum Drawdown

```python
def max_drawdown(returns: pl.Series) -> dict:
    """Calculate maximum drawdown and duration."""
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max

    max_dd = drawdown.min()
    end_idx = drawdown.arg_min()

    # Find start (peak before trough)
    start_idx = cumulative[:end_idx].arg_max()

    # Find recovery
    recovery = (cumulative[end_idx:] >= cumulative[start_idx]).arg_max()

    return {
        'max_drawdown': max_dd,
        'start': start_idx,
        'trough': end_idx,
        'recovery': recovery,
        'duration': end_idx - start_idx
    }
```

## Sortino Ratio

```python
def sortino_ratio(
    returns: np.ndarray,
    target: float = 0,
    annualize: bool = True
) -> float:
    """Return per unit of downside risk."""
    excess = returns - target
    downside = excess[excess < 0]
    downside_std = np.sqrt(np.mean(downside ** 2))

    ratio = returns.mean() / downside_std
    if annualize:
        ratio *= np.sqrt(252)
    return ratio
```

## Calmar Ratio

```python
def calmar_ratio(returns: np.ndarray) -> float:
    """Annualized return / max drawdown."""
    annual_return = returns.mean() * 252
    max_dd = max_drawdown(returns)['max_drawdown']
    return annual_return / abs(max_dd)
```

## Guardrails

- VaR underestimates tail risk (use CVaR)
- Historical VaR assumes future like past
- Max DD looks backwards; monitor current DD
- Annualize consistently (sqrt(252) for daily)

## Checklist

- [ ] Multiple risk metrics calculated
- [ ] CVaR for tail risk
- [ ] Drawdown tracked continuously
- [ ] Risk limits defined per metric
