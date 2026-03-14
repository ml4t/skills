---
name: ml4t-tearsheet
description: Generate comprehensive performance reports from backtest returns. Use when evaluating strategy quality beyond a single Sharpe number.
dependencies: [run-backtest]
metadata:
  book_chapters: "16"
  library: "ml4t-backtest"
---

# Strategy Tearsheet

A single metric hides more than it reveals. A tearsheet shows cumulative returns, drawdowns, rolling Sharpe, monthly heatmap, and a metrics table — exposing regime dependence, tail risk, and decay that one number cannot.

## The Problem

Reporting only Sharpe ratio misses critical failure modes. A Sharpe of 1.5 could come from steady 10 bps/day or from one massive gain followed by slow bleed. Max drawdown reveals survival risk. Rolling Sharpe reveals whether alpha is decaying. Monthly returns reveal seasonality. You need all of them.

## The Pattern

### WRONG
```python
# Single number — hides everything important
sharpe = returns.mean() / returns.std() * np.sqrt(252)
print(f"Sharpe: {sharpe:.2f}")  # "Looks great!" — but is the strategy dying?
```

### CORRECT
```python
import numpy as np
import matplotlib.pyplot as plt

def tearsheet(returns: np.ndarray, periods: int = 252):
    """Minimal tearsheet: 4 panels + metrics table."""
    cum = (1 + returns).cumprod()
    peak = np.maximum.accumulate(cum)
    dd = (cum - peak) / peak

    # Key metrics
    sharpe = returns.mean() / returns.std() * np.sqrt(periods)
    max_dd = dd.min()
    calmar = (cum[-1] ** (periods / len(returns)) - 1) / abs(max_dd) if max_dd else 0
    win_rate = (returns > 0).mean()
    profit_factor = returns[returns > 0].sum() / abs(returns[returns < 0].sum())

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(cum, linewidth=1)
    axes[0].set_title("Cumulative Returns")
    axes[1].fill_between(range(len(dd)), dd, 0, alpha=0.5, color="red")
    axes[1].set_title("Drawdown")
    rolling = (
        np.convolve(returns, np.ones(63), "valid") /
        np.convolve(returns**2 - returns.mean()**2, np.ones(63), "valid")**0.5
    ) * np.sqrt(periods)  # approximate rolling Sharpe
    axes[2].plot(rolling, linewidth=1)
    axes[2].axhline(0, color="gray", linewidth=0.5)
    axes[2].set_title("Rolling Sharpe (63-day)")

    print(f"Sharpe:        {sharpe:>8.2f}")
    print(f"Max Drawdown:  {max_dd:>8.1%}")
    print(f"Calmar:        {calmar:>8.2f}")
    print(f"Win Rate:      {win_rate:>8.1%}")
    print(f"Profit Factor: {profit_factor:>8.2f}")
    return fig
```

## Required Metrics

| Metric | Formula | Red Flag |
|--------|---------|----------|
| Sharpe | $(\mu - r_f) / \sigma \times \sqrt{252}$ | < 0.5 |
| Max Drawdown | $\max(\text{peak} - \text{trough}) / \text{peak}$ | > 25% |
| Calmar | CAGR / \|Max DD\| | < 0.5 |
| Win Rate | $N_{\text{win}} / N_{\text{total}}$ | < 40% for trend |
| Profit Factor | $\sum \text{gains} / |\sum \text{losses}|$ | < 1.2 |

Always report **gross and net** (after costs). A gross Sharpe of 1.5 that drops to 0.3 net means costs dominate alpha.

## Guardrails

- Annualize with the correct frequency: 252 (daily), 52 (weekly), 12 (monthly)
- Report net-of-cost metrics alongside gross — the gap is the cost burden
- Compare strategy Sharpe to a passive benchmark, not zero
- Use Deflated Sharpe Ratio when selecting among multiple strategies (corrects for multiple testing)

## Production Implementation

`ml4t-backtest` generates tearsheets from `BacktestResult`:

```python
from ml4t.backtest import Engine, BacktestConfig

result = Engine(config).run(strategy, feed)
# result exposes: .sharpe, .max_drawdown, .calmar, .returns, .equity
print(f"Sharpe: {result.sharpe:.2f}  MaxDD: {result.max_drawdown:.1%}")
```

## Checklist

- [ ] Cumulative return, drawdown, and rolling Sharpe plotted
- [ ] Sharpe, max drawdown, Calmar, win rate, profit factor reported
- [ ] Both gross and net metrics shown
- [ ] Annualization matches data frequency
- [ ] Compared to benchmark (not just absolute)
