---
name: ml4t-risk-metrics
description: "Compute portfolio risk measures including drawdown, VaR, CVaR, and tail metrics. Use when assessing portfolio risk beyond simple return statistics."
when_to_use: "Use when evaluating strategy performance or setting risk limits"
dependencies: []
metadata:
  book_chapters: "19"
  library: "ml4t-diagnostic"
paths: ["**/*portfolio*.py", "**/*position*.py", "**/*risk*.py", "**/*optim*.py", "**/*exposure*.py", "**/*kill*.py", "**/*stress*.py"]
---
# Risk Metrics

A strategy with Sharpe 1.5 and max drawdown -55% will get shut down before it recovers. Reporting returns without drawdowns, tail risk, and duration metrics hides the path dependency that determines whether a strategy survives.

## The Problem

Sharpe ratio is the default performance metric, but it treats upside and downside volatility equally and says nothing about tail losses. A strategy can have a high Sharpe while hiding a -40% drawdown that takes 18 months to recover. Fund managers and allocators care about max drawdown, time underwater, and worst-case losses — because those determine whether the strategy (and the fund) survives. Always report drawdown alongside return metrics.

## The Pattern

### WRONG
```python
import numpy as np

returns = strategy_returns  # daily
sharpe = returns.mean() / returns.std() * np.sqrt(252)
print(f"Sharpe: {sharpe:.2f}")  # Looks great — ships it
```

### CORRECT
```python
import numpy as np
from scipy.stats import norm

returns = strategy_returns  # daily, numpy array

# Return metrics
sharpe = returns.mean() / returns.std() * np.sqrt(252)
downside = np.minimum(returns, 0)  # All returns: negative kept, positive → 0
sortino = returns.mean() / np.sqrt((downside ** 2).mean()) * np.sqrt(252)

# Drawdown
cumulative = np.cumprod(1 + returns)
running_max = np.maximum.accumulate(cumulative)
drawdown = (cumulative - running_max) / running_max
max_dd = drawdown.min()
calmar = (returns.mean() * 252) / abs(max_dd)

# Tail risk (95% confidence)
var_95 = np.percentile(returns, 5)
cvar_95 = returns[returns <= var_95].mean()

print(f"Sharpe: {sharpe:.2f} | Sortino: {sortino:.2f} | Calmar: {calmar:.2f}")
print(f"Max DD: {max_dd:.1%} | VaR(95): {var_95:.1%} | CVaR(95): {cvar_95:.1%}")
```

## Metric Reference

| Metric | Formula | Measures |
|--------|---------|----------|
| Sharpe | mean(r) / std(r) * sqrt(252) | Risk-adjusted return |
| Sortino | mean(r) / sqrt(E[min(r,0)^2]) * sqrt(252) | Downside-adjusted return |
| Max drawdown | max peak-to-trough decline | Worst cumulative loss |
| Calmar | ann_return / \|max_dd\| | Return per unit of drawdown |
| VaR(95%) | 5th percentile of returns | Daily loss threshold |
| CVaR(95%) | mean of returns below VaR | Expected loss in tail |

## Parametric vs Historical VaR

```python
# Historical: uses actual distribution (captures fat tails)
var_hist = np.percentile(returns, 5)

# Parametric: assumes normal (underestimates tails)
var_param = returns.mean() + norm.ppf(0.05) * returns.std()

# Always prefer historical unless you need scenario-based VaR
```

## Guardrails

- Never report Sharpe alone — always include max drawdown and Calmar at minimum
- VaR underestimates tail risk by design — pair it with CVaR (Expected Shortfall)
- Historical VaR assumes the past contains the worst case — it does not
- Annualize consistently: multiply mean by 252, std by sqrt(252) for daily data
- Monitor current drawdown in real time, not just historical max

## Production Implementation

`ml4t-diagnostic` provides validated risk computation:

```python
from ml4t.diagnostic.api import PortfolioAnalysis

pa = PortfolioAnalysis(returns=strategy_returns, benchmark=benchmark_returns)
metrics = pa.compute_summary_stats()
report = metrics.summary()  # Sharpe, Sortino, max_dd, Calmar, VaR, CVaR, etc.
```

## Checklist

- [ ] Sharpe, Sortino, and Calmar all reported (not Sharpe alone)
- [ ] Max drawdown and drawdown duration computed
- [ ] CVaR computed alongside VaR for tail risk
- [ ] Metrics annualized consistently (daily * sqrt(252))
- [ ] Current drawdown monitored in live systems (not just historical max)
