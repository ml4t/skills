---
name: ml4t-sensitivity-analysis
description: "Test strategy robustness to parameter variation and detect overfitting cliffs. Use when validating that performance is stable across parameter perturbations."
when_to_use: "Use when validating that performance is not fragile to exact parameter choices"
dependencies: [run-backtest]
metadata:
  book_chapters: "16"
  library: "ml4t-backtest"
paths: ["**/*backtest*.py", "**/*strategy*.py", "**/*engine*.py", "**/*broker*.py", "**/*cost*.py", "**/*regime*.py", "**/*tearsheet*.py"]
---
# Parameter Sensitivity Analysis

A strategy optimized to Sharpe 2.0 at lookback=21 that drops to 0.3 at lookback=20 or lookback=22 is not a strategy - it is a curve fit. Sensitivity analysis sweeps parameters to verify that performance is stable across a neighborhood, not balanced on a knife edge.

## The Problem

Single-parameter backtests find the best setting. But the best setting may be a statistical fluke - one data point away from failure. If small perturbations in entry threshold, lookback period, or position sizing cause large performance swings, the parameters are overfit. You need to see the performance surface, not just its peak.

## The Pattern

### WRONG
```python
import numpy as np

# Optimize one parameter, report the best - classic overfitting
best_sharpe, best_lookback = -np.inf, None
for lookback in range(5, 60):
    ret = run_strategy(prices, lookback=lookback)
    sr = ret.mean() / ret.std() * np.sqrt(252)
    if sr > best_sharpe:
        best_sharpe, best_lookback = sr, lookback
print(f"Best: lookback={best_lookback}, Sharpe={best_sharpe:.2f}")  # overstated
```

### CORRECT
```python
import itertools
import numpy as np
import polars as pl
import matplotlib.pyplot as plt

def parameter_sweep(prices, param_grid: dict, strategy_fn) -> pl.DataFrame:
    """Sweep all parameter combinations, return full results table."""
    rows = []
    for combo in itertools.product(*param_grid.values()):
        params = dict(zip(param_grid.keys(), combo))
        ret = strategy_fn(prices, **params)
        sr = ret.mean() / ret.std() * np.sqrt(252)
        cum = np.cumprod(1 + ret)
        max_dd = ((np.maximum.accumulate(cum) - cum) / np.maximum.accumulate(cum)).max()
        rows.append({**params, "sharpe": sr, "max_dd": max_dd})
    return pl.DataFrame(rows)

grid = {"lookback": range(10, 50, 5), "threshold": [0.01, 0.02, 0.03, 0.05]}
results = parameter_sweep(prices, grid, my_strategy)

# Robustness = fraction of combinations with Sharpe > 0
robustness = (results.get_column("sharpe") > 0).mean()
print(f"Robustness: {robustness:.0%} of {len(results)} combos are profitable")

# Cliff detection: large Sharpe change between adjacent parameter values
for param in grid:
    sorted_df = results.sort(param)
    diffs = sorted_df.get_column("sharpe").diff().abs()
    if diffs.max() > 2 * diffs.std():
        print(f"WARNING: performance cliff detected in {param}")
```

## Reading the Sensitivity Surface

```python
# 2D heatmap: lookback vs threshold
pivot = results.pivot(on="threshold", index="lookback", values="sharpe")
fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(pivot.drop("lookback").to_numpy(), aspect="auto", cmap="RdYlGn")
ax.set_xlabel("Threshold")
ax.set_ylabel("Lookback")
ax.set_title("Sharpe Ratio Sensitivity Surface")
plt.colorbar(im, ax=ax)
```

A healthy strategy shows a broad plateau (many green cells). A fragile strategy shows a single bright cell surrounded by red.

## Guardrails

- Robustness score below 50% means the strategy is fragile - most parameter settings lose money. Target: >60% of grid has Sharpe > 0 for deployable strategies
- Performance cliffs (Sharpe drops > 2 std between adjacent parameters) suggest overfitting to a boundary
- Optimal parameters at the edge of the grid suggest the true optimum is outside your search range - extend it
- Always check multiple metrics (Sharpe, max drawdown, Calmar) - a parameter set that maximizes Sharpe but doubles drawdown is not robust

## Production Implementation

Use `ml4t-backtest` for realistic execution in each grid cell:

```python
from ml4t.backtest import Engine, DataFeed, BacktestConfig

results = []
for lookback, threshold in itertools.product([10, 20, 30], [0.01, 0.03]):
    config = BacktestConfig(commission_type="PER_SHARE", commission_per_share=0.005)
    result = Engine(DataFeed(prices), MyStrategy(lookback, threshold), config).run()
    results.append({"lookback": lookback, "threshold": threshold,
                    "sharpe": result.metrics["sharpe_ratio"]})
```

## Checklist

- [ ] At least 2 parameters varied simultaneously (not one-at-a-time only)
- [ ] Robustness score computed (fraction of grid with Sharpe > 0)
- [ ] Performance cliffs identified and flagged
- [ ] Optimal parameters not at grid boundary
- [ ] Multiple metrics checked (Sharpe, max drawdown, Calmar)
- [ ] Sensitivity heatmap or surface plotted
