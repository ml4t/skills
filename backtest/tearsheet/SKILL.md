---
name: ml4t-tearsheet
description: Generate performance reports and metrics from backtest results
category: backtest
type: operational
dependencies: [run-backtest]
book_chapters: [17]
quantlab_module: ml4t.diagnostic.reporting
---

# Tearsheet

Generate performance metrics and reports from backtest results.

## Core Metrics

```python
from ml4t.diagnostic.evaluation.metrics import (
    sharpe_ratio,
    sortino_ratio,
    max_drawdown,
    calmar_ratio,
    information_coefficient,
    deflated_sharpe_ratio
)

# From returns series
sr = sharpe_ratio(returns, risk_free=0.0, periods=252)
sortino = sortino_ratio(returns, risk_free=0.0, periods=252)
mdd = max_drawdown(returns)
calmar = calmar_ratio(returns, periods=252)

# Factor evaluation
ic = information_coefficient(predictions, actual_returns)
dsr = deflated_sharpe_ratio(sharpe_ratios)  # From CPCV folds
```

## Key Metrics Formulas

| Metric | Formula | Good Value |
|--------|---------|------------|
| Sharpe | (μ - rf) / σ × √252 | > 1.0 |
| Sortino | (μ - rf) / σ_down × √252 | > 1.5 |
| Max DD | max(peak - trough) / peak | < 20% |
| Calmar | CAGR / Max DD | > 1.0 |
| IC | corr(pred, actual) | > 0.03 |

## Report Generation

```python
from ml4t.diagnostic.reporting import generate_tearsheet

report = generate_tearsheet(
    returns=strategy_returns,
    benchmark=benchmark_returns,
    positions=position_history
)
```

## Guardrails

- Always annualize with correct periods (252 daily, 52 weekly, 12 monthly)
- Report gross AND net (after costs) metrics
- Compare to benchmark Sharpe, not just absolute
- Use Deflated Sharpe when testing multiple strategies
