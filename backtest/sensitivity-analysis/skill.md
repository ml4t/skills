---
name: ml4t-sensitivity-analysis
description: Test strategy robustness to parameter changes
category: backtest
type: operational
dependencies: [run-backtest]
book_chapters: [17]
---

# Sensitivity Analysis

Measure how performance changes with parameter variations.

## Parameter Sweep

```python
def parameter_sweep(
    strategy_fn: callable,
    param_grid: dict,
    data: pl.DataFrame
) -> pl.DataFrame:
    """Sweep over parameter combinations."""
    results = []

    for params in itertools.product(*param_grid.values()):
        param_dict = dict(zip(param_grid.keys(), params))
        returns = strategy_fn(data, **param_dict)

        results.append({
            **param_dict,
            'sharpe': returns.mean() / returns.std() * np.sqrt(252),
            'return': returns.sum(),
            'volatility': returns.std() * np.sqrt(252),
            'max_dd': calculate_max_drawdown(returns)
        })

    return pl.DataFrame(results)
```

## One-at-a-Time Analysis

```python
def oat_analysis(
    strategy_fn: callable,
    base_params: dict,
    variations: dict,  # param -> [values]
    data: pl.DataFrame
) -> dict:
    """Vary one parameter at a time from baseline."""
    results = {'baseline': strategy_fn(data, **base_params)}

    for param, values in variations.items():
        results[param] = []
        for val in values:
            test_params = base_params.copy()
            test_params[param] = val
            returns = strategy_fn(data, **test_params)
            results[param].append({
                'value': val,
                'sharpe': returns.mean() / returns.std() * np.sqrt(252)
            })

    return results
```

## Robustness Score

```python
def robustness_score(sweep_results: pl.DataFrame) -> float:
    """Fraction of parameter combinations that are profitable."""
    positive = (sweep_results['sharpe'] > 0).sum()
    total = len(sweep_results)
    return positive / total

# Good strategy: robustness > 0.7
# Fragile strategy: robustness < 0.3
```

## Cliff Detection

```python
def detect_cliffs(sweep_results: pl.DataFrame, param: str) -> list:
    """Find where small param changes cause large metric changes."""
    sorted_results = sweep_results.sort(param)
    sharpe_changes = sorted_results['sharpe'].diff().abs()

    # Identify large changes
    threshold = sharpe_changes.std() * 2
    cliff_idx = sharpe_changes > threshold

    return sorted_results.filter(cliff_idx)[param].to_list()
```

## Visualization

```python
def plot_sensitivity_heatmap(results: pl.DataFrame, x: str, y: str):
    """2D heatmap of Sharpe ratio vs two parameters."""
    pivot = results.pivot(values='sharpe', index=y, columns=x)
    # Create heatmap
```

## Guardrails

- Results should be stable near optimal parameters
- Performance cliffs suggest overfitting
- Optimal shouldn't be at parameter boundary
- Test different metrics (Sharpe, Sortino, Calmar)

## Checklist

- [ ] Parameter ranges span reasonable values
- [ ] Robustness score calculated
- [ ] Cliffs identified and avoided
- [ ] Chosen parameters not at boundary
- [ ] Multiple metrics checked
