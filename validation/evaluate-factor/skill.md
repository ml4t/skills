---
name: ml4t-evaluate-factor
description: Evaluate alpha factors with Alphalens-style analysis
category: validation
type: operational
dependencies: [information-coefficient]
book_chapters: [9]
quantlab_module: ml4t.diagnostic.factor_analysis
---

# Evaluate Factor

Comprehensive factor evaluation before portfolio integration.

## Key Metrics

| Metric | What It Measures |
|--------|------------------|
| IC | Correlation with forward returns |
| IC IR | Consistency of IC over time |
| Quantile returns | Return spread by signal strength |
| Turnover | Trading cost proxy |
| Decay | How quickly signal loses power |

## API

```python
from ml4t.diagnostic.factor_analysis import FactorAnalyzer

analyzer = FactorAnalyzer(
    factor=signal,
    forward_returns=returns,
    quantiles=5,
    periods=[1, 5, 21]  # 1d, 1w, 1m
)

# Run full analysis
results = analyzer.analyze()

# Key outputs
print(f"IC: {results.ic_mean:.3f}")
print(f"IC IR: {results.ic_ir:.3f}")
print(f"Top-Bottom Spread: {results.quantile_spread:.1%}")
print(f"Turnover: {results.turnover:.1%}")
```

## Quantile Analysis

```python
def quantile_returns(signal: pl.Series, returns: pl.Series,
                     n_quantiles: int = 5) -> pl.DataFrame:
    """Calculate returns by signal quantile."""
    quantiles = signal.qcut(n_quantiles, labels=False)

    return (
        pl.DataFrame({'q': quantiles, 'ret': returns})
        .group_by('q')
        .agg(pl.col('ret').mean())
        .sort('q')
    )

# Good factor: monotonic relationship
# Q1 < Q2 < Q3 < Q4 < Q5 (or reverse)
```

## Turnover Analysis

```python
def factor_turnover(signal: pl.Series, n_quantiles: int = 5) -> float:
    """Measure position changes between periods."""
    quantiles = signal.qcut(n_quantiles, labels=False)
    changes = (quantiles != quantiles.shift(1)).mean()
    return changes
```

## Decay Analysis

```python
# IC by forward return horizon
for horizon in [1, 5, 10, 20, 40, 60]:
    fwd_ret = returns.shift(-horizon)
    ic = information_coefficient(signal, fwd_ret).mean()
    print(f"{horizon}d IC: {ic:.3f}")

# Optimal horizon where IC peaks
```

## Guardrails

- IC alone is insufficient; check quantile monotonicity
- High turnover = high transaction costs
- Factor decay determines rebalance frequency
- t-stats with HAC standard errors

## Checklist

- [ ] IC and IC IR calculated
- [ ] Quantile returns are monotonic
- [ ] Turnover estimated
- [ ] Decay analysis performed
- [ ] Statistical significance tested
