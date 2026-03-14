---
name: ml4t-factor-research
description: Systematic factor research process from hypothesis through IC analysis, decay profiling, and capacity assessment. Use when evaluating a new alpha factor or auditing an existing factor for deployment readiness.
dependencies: [information-coefficient, feature-families, feature-validation, horizon-design, evaluate-factor]
metadata:
  book_chapters: "7, 8"
  library: "ml4t-diagnostic"
---

# Factor Research Workflow

Testing one factor on one period and deploying is data mining. Systematic factor research requires IC significance, stability across subperiods, decay profiling, and capacity estimation before any factor enters a model.

## The Problem

A researcher computes 12-month momentum, sees a positive rank IC of 0.04, and adds it to the model. Six months later, the factor IC has collapsed. The problem: the IC was estimated on one period without significance testing, there was no check for stability or decay, and the factor's capacity was never assessed. A factor that "works" on paper but fails in production is worse than no factor at all.

## The Pattern

### WRONG

```python
# Test one factor, one period, deploy on a single positive number
import numpy as np
from scipy.stats import spearmanr

factor = prices.pct_change(252)  # 12-month momentum
fwd_ret = prices.pct_change(21).shift(-21)  # 1-month forward return

ic, _ = spearmanr(factor.dropna(), fwd_ret.dropna())
print(f"IC: {ic:.3f}")  # 0.04 — looks good, ship it
```

### CORRECT

```python
# Systematic evaluation: IC series → significance → stability → decay → capacity
import numpy as np
import polars as pl
from scipy.stats import spearmanr

# Step 1: Compute cross-sectional IC for every rebalance date
ic_series = []
for date in rebalance_dates:
    cross_section = data.filter(pl.col("timestamp") == date)
    ic, _ = spearmanr(cross_section["factor"], cross_section["fwd_ret"])
    ic_series.append({"timestamp": date, "ic": ic})

ic_df = pl.DataFrame(ic_series)

# Step 2: Significance with HAC standard errors (Newey-West)
ic_mean = ic_df["ic"].mean()
ic_std = ic_df["ic"].std()
n = len(ic_df)
# Newey-West adjustment for autocorrelation (see ml4t-information-coefficient)
t_stat = ic_mean / (ic_std / np.sqrt(n))  # Simplified; use HAC for production

# Step 3: Stability — split into subperiods
midpoint = n // 2
ic_first_half = ic_df[:midpoint]["ic"].mean()
ic_second_half = ic_df[midpoint:]["ic"].mean()

# Step 4: Decay — test multiple horizons (see ml4t-horizon-design)
for horizon in [1, 5, 10, 21, 63]:
    fwd = prices.pct_change(horizon).shift(-horizon)
    ic_h, _ = spearmanr(factor.dropna(), fwd.dropna())
    print(f"  {horizon}d IC: {ic_h:.4f}")

# Step 5: Decision gate
print(f"IC: {ic_mean:.4f} (t={t_stat:.2f})")
print(f"Stability: {ic_first_half:.4f} / {ic_second_half:.4f}")
assert abs(t_stat) > 2.0, "IC not statistically significant"
assert ic_first_half * ic_second_half > 0, "IC sign flipped across subperiods"
```

## Five-Gate Evaluation

| Gate | Metric | Threshold | Skill Reference |
|------|--------|-----------|-----------------|
| Significance | IC t-stat (HAC) | > 2.0 | `ml4t-information-coefficient` |
| Stability | Subperiod IC sign agreement | Same sign in all halves | `ml4t-feature-validation` |
| Decay | Half-life vs rebalance frequency | Half-life > 2x rebalance period | `ml4t-horizon-design` |
| Uniqueness | Correlation with existing factors | < 0.7 rank correlation | `ml4t-feature-families` |
| Capacity | Turnover-implied trading volume | Tradeable at target AUM | `ml4t-evaluate-factor` |

A factor must pass all five gates. Passing three out of five is not enough — a factor that is significant but unstable will cause regime-dependent blowups.

## Guardrails

- If IC > 0.10 on daily equity data, suspect lookahead bias — real equity ICs are typically 0.02-0.05
- If factor turnover exceeds 50% monthly, capacity is likely constrained — check with `ml4t-evaluate-factor`
- If IC is high but quantile returns are non-monotonic, the signal is noisy and may not translate to returns
- If subperiod ICs disagree in sign, the factor is likely spurious regardless of full-period IC

## Production Implementation

`ml4t-diagnostic` provides HAC-adjusted IC statistics and factor evaluation:

```python
from ml4t.diagnostic.evaluation import compute_ic_series, compute_ic_hac_stats
from ml4t.diagnostic import Evaluator

ic = compute_ic_series(factor=factor_values, forward_returns=fwd_returns)
stats = compute_ic_hac_stats(ic)  # Newey-West adjusted t-stat

evaluator = Evaluator(config={"quantiles": 5, "periods": [1, 5, 21]})
report = evaluator.evaluate(features=features, labels=labels)
```

## Checklist

- [ ] Economic hypothesis documented with mechanism and expected IC range
- [ ] Factor computed with no lookahead (lagged by at least one period)
- [ ] IC series computed cross-sectionally for every rebalance date
- [ ] IC significance tested with HAC standard errors (t > 2.0)
- [ ] Subperiod stability verified (IC same sign in both halves)
- [ ] Decay profile computed across multiple horizons
- [ ] Uniqueness checked against existing factor correlation matrix
- [ ] Capacity estimated based on turnover and universe liquidity
