---
name: ml4t-regime-backtest
description: Analyze strategy performance by market regime
category: backtest
type: operational
dependencies: [regime-awareness, run-backtest]
book_chapters: [17, 21]
---

# Regime Backtest

Evaluate strategy performance across different market conditions.

## Regime Classification

```python
def classify_regimes(returns: pl.Series, volatility: pl.Series) -> pl.Series:
    """Classify into 4 regimes."""
    vol_high = volatility > volatility.quantile(0.7)
    ret_pos = returns.rolling(63).mean() > 0

    return (
        pl.when(ret_pos & ~vol_high).then(pl.lit('bull_calm'))
        .when(ret_pos & vol_high).then(pl.lit('bull_volatile'))
        .when(~ret_pos & ~vol_high).then(pl.lit('bear_calm'))
        .otherwise(pl.lit('bear_volatile'))
    )
```

## Regime-Conditioned Metrics

```python
def regime_performance(
    strategy_returns: pl.Series,
    regime: pl.Series
) -> dict:
    """Calculate metrics per regime."""
    results = {}

    for r in regime.unique():
        mask = regime == r
        rets = strategy_returns.filter(mask)

        results[r] = {
            'sharpe': rets.mean() / rets.std() * np.sqrt(252),
            'return': rets.sum(),
            'volatility': rets.std() * np.sqrt(252),
            'max_dd': calculate_max_drawdown(rets.cum_sum()),
            'days': mask.sum()
        }

    return results
```

## Visualization

```python
def plot_regime_performance(results: dict):
    """Regime performance heatmap."""
    regimes = list(results.keys())
    metrics = ['sharpe', 'return', 'volatility', 'max_dd']

    data = [[results[r][m] for m in metrics] for r in regimes]
    # Create heatmap with regimes on y-axis, metrics on x-axis
```

## Stress Testing

```python
# Define stress periods
STRESS_PERIODS = {
    'gfc_2008': ('2008-09-01', '2009-03-31'),
    'covid_crash': ('2020-02-15', '2020-03-31'),
    'rate_shock_2022': ('2022-01-01', '2022-06-30'),
}

def stress_test(returns: pl.DataFrame, periods: dict) -> dict:
    """Calculate performance during stress periods."""
    results = {}
    for name, (start, end) in periods.items():
        stress_rets = returns.filter(
            (pl.col('date') >= start) & (pl.col('date') <= end)
        )
        results[name] = {
            'return': stress_rets.sum(),
            'max_dd': calculate_max_drawdown(stress_rets),
            'days': len(stress_rets)
        }
    return results
```

## Guardrails

- Regime classification should use lagged data
- Some regimes may have few observations
- Stress periods are in-sample (known events)
- Good strategy works across regimes

## Checklist

- [ ] Multiple regime definitions tested
- [ ] Performance by regime calculated
- [ ] Stress periods analyzed
- [ ] Strategy doesn't depend on single regime
