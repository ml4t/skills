---
name: ml4t-exposure-analysis
description: "Decompose portfolio into factor, sector, and concentration exposures. Use when checking for unintended bets or risk concentrations."
when_to_use: "Use when reviewing portfolio construction or diagnosing unexpected drawdowns"
dependencies: []
metadata:
  book_chapters: "17, 19"
  library: "ml4t-diagnostic"
paths: ["**/*portfolio*.py", "**/*position*.py", "**/*risk*.py", "**/*optim*.py", "**/*exposure*.py", "**/*kill*.py", "**/*stress*.py"]
---
# Exposure Analysis

A portfolio of 50 stocks can look diversified by count while having 80% of its risk in a single factor. Without exposure decomposition, you cannot distinguish between intended alpha bets and unintended factor tilts.

## The Problem

Position weights tell you what you own, not what risks you are taking. A "diversified" tech-heavy portfolio may have a market beta of 1.4, a momentum loading of +0.6, and 60% sector concentration in technology - meaning most of its variance comes from three correlated bets, not 50 independent ones. Exposure analysis decomposes portfolio risk into factor loadings, sector weights, and concentration measures so you can verify that the portfolio matches your thesis.

## The Pattern

### WRONG
```python
import numpy as np

# Only look at position weights
weights = np.array([0.05, 0.04, 0.03, ...])  # 50 stocks
print(f"Number of positions: {len(weights)}")
print(f"Max position: {weights.max():.1%}")
# "50 positions, max 5% - looks diversified!"
# But 35 of them are correlated growth stocks with beta > 1.3
```

### CORRECT
```python
import numpy as np
from sklearn.linear_model import LinearRegression

# Factor exposure via regression
# portfolio_returns: (T,), factor_returns: (T, K) - market, size, value, momentum
model = LinearRegression().fit(factor_returns, portfolio_returns)
betas = dict(zip(["market", "size", "value", "momentum"], model.coef_))
alpha = model.intercept_ * 252  # annualized

# Concentration: Herfindahl-Hirschman Index
hhi = (weights ** 2).sum()
effective_n = 1.0 / hhi  # equivalent number of equal-weight positions

# Net / gross exposure
net = weights.sum()
gross = np.abs(weights).sum()

print(f"Factor betas: {betas}")
print(f"Annualized alpha: {alpha:.2%}")
print(f"HHI: {hhi:.4f} (effective N={effective_n:.0f})")
print(f"Net: {net:.1%} | Gross: {gross:.1%}")
```

## Sector Concentration

```python
def sector_exposure(weights, sectors):
    """Aggregate weights by sector to detect concentration."""
    exposure = {}
    for w, s in zip(weights, sectors):
        exposure[s] = exposure.get(s, 0) + w
    return dict(sorted(exposure.items(), key=lambda x: -abs(x[1])))

# Flag any sector > 30% of gross exposure
for sector, wt in sector_exposure(weights, sectors).items():
    flag = " ** CONCENTRATED **" if abs(wt) > 0.30 else ""
    print(f"  {sector:20s} {wt:+.1%}{flag}")
```

## Rolling Factor Exposures

Factor betas drift over time. Use rolling regression to detect style drift:

```python
def rolling_betas(port_ret, factor_ret, window=63):
    """63-day rolling factor loadings."""
    T = len(port_ret)
    betas = np.full((T, factor_ret.shape[1]), np.nan)
    for t in range(window, T):
        model = LinearRegression().fit(
            factor_ret[t - window:t], port_ret[t - window:t])
        betas[t] = model.coef_
    return betas  # plot to see regime changes
```

## Guardrails

- Factor betas are unstable over short windows - use at least 63 days for daily data
- Sector weights should align with investment thesis - large unintended tilts signal construction error
- HHI above 0.10 (effective N < 10) means the portfolio is concentrated regardless of position count
- Compare exposures to benchmark - net active bets should be intentional

## Production Implementation

`ml4t-diagnostic` provides factor exposure and rolling attribution tools:

```python
from ml4t.diagnostic.evaluation.factor import FactorAnalysis, FactorData

factor_data = FactorData.from_dataframe(factors_df, rf_column="RF")
analysis = FactorAnalysis(strategy_returns, factor_data)
static = analysis.static_model()
rolling = analysis.rolling_model(window=63)
```

## Checklist

- [ ] Factor exposures computed (market, size, value, momentum at minimum)
- [ ] Sector/industry concentration measured and flagged if > 30%
- [ ] HHI and effective N reported (not just position count)
- [ ] Net and gross exposure tracked
- [ ] Rolling betas monitored for style drift
