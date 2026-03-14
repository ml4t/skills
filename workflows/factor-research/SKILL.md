---
name: ml4t-factor-research
description: Workflow for evaluating new alpha factors
category: workflows
type: workflow
dependencies: [feature-families, information-coefficient, evaluate-factor, feature-validation]
book_chapters: [7, 9]
---

# Factor Research Workflow

Systematic process for evaluating new alpha factors.

## Stage Overview

```
1. Hypothesis → 2. Compute → 3. Validate → 4. Evaluate → 5. Decision
```

## Stage 1: Hypothesis

```python
factor_hypothesis = {
    'name': 'momentum_12m',
    'mechanism': 'Trend persistence due to slow information diffusion',
    'expected_horizon': '1-3 months',
    'expected_ic': '0.03-0.05',
    'kill_criteria': 'IC < 0.01 or non-monotonic quantiles'
}
```

## Stage 2: Compute Factor

```python
def compute_factor(prices: pl.DataFrame) -> pl.Series:
    """12-month momentum factor."""
    return prices['close'].pct_change(252)

# Compute with no lookahead
factor = (
    prices
    .group_by('symbol')
    .apply(compute_factor)
    .with_columns(pl.col('factor').shift(1))  # Lag
)
```

## Stage 3: Validate Quality

```python
# 1. Check stationarity
stationarity = test_stationarity(factor)
assert stationarity['is_stationary'], "Factor not stationary"

# 2. Check coverage
coverage = factor.null_count() / len(factor)
assert coverage < 0.05, f"Too many nulls: {coverage:.1%}"

# 3. Check outliers
outlier_pct = (factor.abs() > 5 * factor.std()).mean()
factor = winsorize(factor, limits=(0.01, 0.99))
```

## Stage 4: Evaluate Predictive Power

```python
from ml4t.diagnostic.factor_analysis import FactorAnalyzer

analyzer = FactorAnalyzer(
    factor=factor,
    forward_returns=returns,
    quantiles=5,
    periods=[1, 5, 21]
)

results = analyzer.analyze()

# Key checks
assert results.ic_mean > 0.02, f"IC too low: {results.ic_mean:.3f}"
assert results.ic_ir > 0.3, f"IC unstable: {results.ic_ir:.2f}"
assert results.quantile_monotonic, "Non-monotonic quantiles"
```

## Stage 5: Decision

```python
def factor_decision(results: dict, hypothesis: dict) -> str:
    """Decide whether to proceed with factor."""
    checks = {
        'ic_above_threshold': results.ic_mean > 0.02,
        'quantiles_monotonic': results.quantile_monotonic,
        'ic_stable': results.ic_ir > 0.3,
        'turnover_acceptable': results.turnover < 0.5,
        'decay_matches_horizon': results.optimal_horizon in [5, 21]
    }

    passed = sum(checks.values())
    if passed >= 4:
        return 'PROCEED'
    elif passed >= 2:
        return 'INVESTIGATE'
    return 'REJECT'
```

## Checkpoints

- [ ] Economic hypothesis documented
- [ ] Factor computed with no lookahead
- [ ] Stationarity verified
- [ ] IC and IC IR calculated
- [ ] Quantile returns checked for monotonicity
- [ ] Turnover estimated
- [ ] Decision criteria applied
