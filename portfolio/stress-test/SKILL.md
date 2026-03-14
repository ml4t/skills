---
name: ml4t-stress-test
description: Test portfolios against historical crises and hypothetical shocks to quantify tail exposure. Use when assessing whether a strategy survives extreme markets.
dependencies: [risk-metrics]
metadata:
  book_chapters: "19"
  library: ""
---

# Stress Testing

A strategy backtested on 2015-2023 has never seen a regime where equities and bonds fall simultaneously. Without stress testing against 2008, 2020, and 2022, you are implicitly betting that those regimes will not recur.

## The Problem

Backtests cover only the historical sample, which may exclude the scenarios most relevant to survival. A momentum strategy backtested from 2010 onward has never experienced the 2009 momentum crash (-46% in one month). Stress testing applies known crisis scenarios and hypothetical shocks to the current portfolio, revealing exposures that summary statistics hide. This is not optional — it is how you discover that your "diversified" portfolio has a hidden correlation spike that produces a -30% month.

## The Pattern

### WRONG
```python
import numpy as np

# Only looks at backtest period (2016-2023) — misses major crises
returns = backtest_returns  # 2016-2023 daily
max_loss = returns.min()
print(f"Worst day: {max_loss:.1%}")  # -3.2%, looks safe
# But GFC 2008 would have been -15% in a single week for this portfolio
```

### CORRECT
```python
import numpy as np

# Define crisis scenarios as asset-class shocks
SCENARIOS = {
    "GFC 2008":       {"equity": -0.50, "bond": +0.15, "credit": -0.30, "vol": +3.0},
    "COVID Mar 2020":  {"equity": -0.34, "bond": +0.08, "credit": -0.15, "vol": +4.0},
    "Rate Shock 2022": {"equity": -0.20, "bond": -0.15, "credit": -0.10, "vol": +1.5},
    "Correlation Spike":{"equity": -0.25, "bond": -0.10, "credit": -0.20, "vol": +2.0},
}

# Apply each scenario to current portfolio weights
weights = np.array([0.40, 0.30, 0.20, 0.10])  # equity, bond, credit, vol
asset_classes = ["equity", "bond", "credit", "vol"]

for name, shocks in SCENARIOS.items():
    pnl = sum(weights[i] * shocks.get(ac, 0) for i, ac in enumerate(asset_classes))
    survives = pnl > -0.20  # survival threshold
    print(f"{name:25s} PnL: {pnl:+.1%}  {'OK' if survives else 'BREACH'}")
```

## Factor Stress Testing

```python
def factor_stress(weights, factor_betas, factor_shocks):
    """Stress via factor exposures rather than asset classes.

    factor_betas: (n_assets, n_factors) from regression
    factor_shocks: dict of factor_name -> shock magnitude
    """
    shocks = np.array([factor_shocks[f] for f in factor_names])
    asset_impacts = factor_betas @ shocks
    return weights @ asset_impacts

# Example: what if momentum factor drops 3 sigma?
loss = factor_stress(weights, betas, {"momentum": -0.15, "value": 0.05})
```

## Hypothetical Scenarios to Always Include

| Scenario | Key Feature | Why It Matters |
|----------|-------------|----------------|
| 2008 GFC | Equity crash + credit freeze | Tests leverage and liquidity |
| 2020 COVID | Fastest drawdown in history | Tests execution under vol spike |
| 2022 Rate Shock | Bonds and equities fall together | Tests diversification assumption |
| Correlation spike | All correlations go to 0.8 | Tests if hedges actually work |
| Liquidity freeze | 5x normal bid-ask spreads | Tests transaction cost sensitivity |

## Guardrails

- Historical scenarios are a floor, not a ceiling — always include a "2x worst" hypothetical
- Correlations increase under stress — use stressed correlations, not normal-regime estimates
- Test at current positions, not average or target weights
- Update scenario library when new crises occur (each one reveals a new failure mode)

## Checklist

- [ ] At least 3 historical crisis scenarios applied (2008, 2020, 2022)
- [ ] At least 1 hypothetical scenario (correlation spike or liquidity freeze)
- [ ] Survival threshold defined (e.g., max -20% in any scenario)
- [ ] Factor exposures stress-tested (not just asset-class proxies)
- [ ] Scenario library reviewed and updated within last 12 months
