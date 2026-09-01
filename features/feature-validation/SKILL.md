---
name: ml4t-feature-validation
description: "Validate features before training - IC significance, stability, redundancy, and contamination checks. Use when auditing feature quality before model fitting."
when_to_use: "Use when adding new features to a model or auditing an existing feature set"
dependencies: [lookahead-bias]
metadata:
  book_chapters: "7, 8"
  library: "ml4t-diagnostic"
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
---
# Feature Validation

A feature with IC of 0.05 on the full sample may have IC of 0.12 in one year and -0.03 in every other year. Without validation, the model trains on noise disguised as signal.

## The Problem

Skipping feature validation leads to three failures: lookahead contamination,
regime-specific features that fail live, and redundant features that waste model capacity.

## The Pattern

### WRONG
```python
from sklearn.ensemble import GradientBoostingRegressor

# Train on all features without any validation - overfitting guaranteed
model = GradientBoostingRegressor(n_estimators=200)
model.fit(X_train, y_train)  # 50 features, no idea which are noise
```

### CORRECT
```python
from scipy.stats import spearmanr
import numpy as np

def validate_feature(feature: np.ndarray, target: np.ndarray, dates: np.ndarray) -> dict:
    """Screen a single feature for predictive quality."""
    ok = ~np.isnan(feature) & ~np.isnan(target)  # both: one nan makes ic nan
    ic, p_value = spearmanr(feature[ok], target[ok])
    unique_quarters = np.unique(dates.astype("datetime64[Q]"))
    quarterly_ics = []
    for q in unique_quarters:
        mask = dates.astype("datetime64[Q]") == q
        if mask.sum() > 30:
            qic, _ = spearmanr(feature[mask], target[mask])
            quarterly_ics.append(qic)

    ic_mean = np.nanmean(quarterly_ics)
    ic_std = np.nanstd(quarterly_ics)
    ic_ir = ic_mean / ic_std if ic_std > 0 else 0  # IC information ratio
    leakage_flag = abs(ic) > 0.10

    return {
        "ic": ic, "p_value": p_value, "ic_ir": ic_ir,
        "pct_positive_quarters": np.mean([q > 0 for q in quarterly_ics]),
        "leakage_flag": leakage_flag,
    }
```

## Validation Checklist Sequence

| Step | Check | Pass Criteria |
|------|-------|---------------|
| 1. Completeness | Null percentage | < 5% (or documented imputation) |
| 2. Outliers | Values beyond 5 sigma | < 1% (winsorize if needed) |
| 3. IC significance | Spearman rank correlation | p-value < 0.05 |
| 4. IC stability | Quarterly IC information ratio | IC-IR > 0.5 |
| 5. Leakage screen | Absolute IC threshold | \|IC\| < 0.10 or explained mechanism |
| 6. Redundancy | Pairwise correlation with existing features | < 0.7 |

## IC Decay Analysis

```python
def ic_decay(feature: np.ndarray, returns: np.ndarray, horizons: list[int]) -> dict:
    """IC should decay with horizon - if it doesn't, suspect leakage."""
    n, decay = len(returns), {}
    gaps = np.r_[0, np.cumsum(np.isnan(returns))]  # missing returns so far
    cum = np.r_[1.0, np.cumprod(1.0 + np.nan_to_num(returns))]
    for h in horizons:
        # Compounded t+1..t+h. np.roll wrapped the sample start into the tail,
        # and a plain cumprod let one missing return poison every later window.
        fwd, whole = np.full(n, np.nan), gaps[1 + h:n + 1] == gaps[1:n - h + 1]
        fwd[:n - h] = np.where(whole, cum[1 + h:n + 1] / cum[1:n - h + 1] - 1.0, np.nan)
        valid = ~np.isnan(feature) & ~np.isnan(fwd)
        ic, _ = spearmanr(feature[valid], fwd[valid])
        decay[h] = ic
    return decay  # Expect: decreasing |IC| as h increases
```

## Guardrails

- **IC > 0.10 is suspicious** - nearly always lookahead contamination in daily equity data
- **IC-IR < 0.5 means unstable** - the feature works sometimes but is overall unreliable
- **Non-decaying IC across horizons** - strong sign of information leakage
- **Always validate on expanding windows** - never compute IC on the full sample at once

## Production Implementation

```python
from ml4t.diagnostic.api import compute_ic_hac_stats, cross_sectional_ic_series
from ml4t.diagnostic.metrics import analyze_feature_outcome

ic_series = cross_sectional_ic_series(features, forward_returns, pred_col="signal", ret_col="forward_return", entity_col="symbol")
stats = compute_ic_hac_stats(ic_series)  # HAC-corrected t-stats

analysis = analyze_feature_outcome(
    predictions=features, prices=prices, pred_col="prediction",
    price_col="close", date_col="date", group_col="symbol",
)
```

## Checklist

- [ ] Every feature has IC computed with p-value < 0.05
- [ ] IC stability checked across time (IC-IR > 0.5)
- [ ] Any feature with |IC| > 0.10 investigated for leakage
- [ ] IC peaks at expected horizon then decays (non-decaying IC suggests leakage)
- [ ] Pairwise correlation < 0.7 with all other selected features
- [ ] Null percentage < 5% and outliers winsorized
