---
name: ml4t-stress-test
description: Test portfolio under extreme scenarios
category: portfolio
type: operational
dependencies: [risk-metrics]
book_chapters: [20]
---

# Stress Testing

Evaluate portfolio under extreme market conditions.

## Scenario Types

| Type | Source | Example |
|------|--------|---------|
| Historical | Past crises | 2008 GFC |
| Hypothetical | Constructed | 2x GFC severity |
| Sensitivity | Single factor | +200bp rates |

## Historical Scenarios

```python
HISTORICAL_SCENARIOS = {
    'black_monday_1987': {'equity': -0.226, 'bond': 0.02, 'gold': 0.03},
    'gfc_2008': {'equity': -0.50, 'bond': 0.15, 'credit': -0.30},
    'covid_crash_2020': {'equity': -0.34, 'bond': 0.08, 'vol': 4.0},
    'rate_shock_2022': {'equity': -0.20, 'bond': -0.15, 'credit': -0.10},
}

def apply_scenario(
    weights: np.ndarray,
    asset_mapping: dict,  # position -> asset class
    scenario: dict
) -> float:
    """Calculate portfolio loss under scenario."""
    loss = 0
    for i, w in enumerate(weights):
        asset_class = asset_mapping[i]
        shock = scenario.get(asset_class, 0)
        loss += w * shock
    return loss
```

## Factor Stress

```python
def factor_stress_test(
    weights: np.ndarray,
    factor_betas: np.ndarray,  # (n_assets, n_factors)
    factor_shocks: dict        # factor -> shock magnitude
) -> float:
    """Stress test via factor exposures."""
    shocks = np.array([factor_shocks.get(f, 0) for f in factor_names])
    asset_impacts = factor_betas @ shocks
    return weights @ asset_impacts
```

## Monte Carlo Stress

```python
def monte_carlo_stress(
    returns: np.ndarray,
    weights: np.ndarray,
    n_simulations: int = 10000,
    tail_percentile: float = 1.0
) -> dict:
    """Simulate extreme scenarios."""
    # Resample from worst historical returns
    worst_mask = returns <= np.percentile(returns, tail_percentile, axis=0)

    scenarios = []
    for _ in range(n_simulations):
        scenario = np.array([
            np.random.choice(r[m]) for r, m in zip(returns.T, worst_mask.T)
        ])
        scenarios.append(weights @ scenario)

    return {
        'mean_stress_loss': np.mean(scenarios),
        'worst_case': np.min(scenarios),
        '1pct_loss': np.percentile(scenarios, 1)
    }
```

## Stress Report

```python
def stress_test_report(
    weights: np.ndarray,
    scenarios: dict
) -> pl.DataFrame:
    """Generate stress test report."""
    results = []
    for name, scenario in scenarios.items():
        loss = apply_scenario(weights, asset_mapping, scenario)
        results.append({
            'scenario': name,
            'loss': loss,
            'survives': loss > -0.20  # Example threshold
        })
    return pl.DataFrame(results)
```

## Guardrails

- Historical scenarios may underestimate future crises
- Correlations change under stress (usually increase)
- Test portfolio at current positions, not average
- Update scenarios as new crises occur

## Checklist

- [ ] Major historical crises tested
- [ ] Factor sensitivities analyzed
- [ ] Survival thresholds defined
- [ ] Scenarios updated regularly
