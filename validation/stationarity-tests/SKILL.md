---
name: ml4t-stationarity-tests
description: Test whether time series features are stationary before modeling using ADF and KPSS tests. Use when preparing features for ML models or diagnosing spurious regression.
dependencies: []
metadata:
  book_chapters: "9"
  library: "ml4t-diagnostic"
---

# Stationarity Tests

Feeding non-stationary features (raw prices, trending volume) into ML models produces spurious correlations that vanish out of sample. Test stationarity first, transform if needed.

## The Problem

Raw asset prices are non-stationary: their mean and variance change over time. A regression of one non-stationary series on another can produce high R-squared and significant t-statistics even when there is no causal relationship (spurious regression). In ML4T, this means a model trained on raw prices will appear to predict well in-sample but fail live. Returns and most financial ratios are stationary. The gap between "looks predictive" and "is predictive" often comes down to stationarity.

## The Pattern

### WRONG

```python
import numpy as np
from sklearn.linear_model import Ridge

# Model raw prices — non-stationary, spurious correlation
X = price_features  # Trending upward
y = forward_prices  # Also trending upward
model = Ridge().fit(X, y)
print(f"R-squared: {model.score(X, y):.3f}")  # High but meaningless
```

### CORRECT

```python
import numpy as np
from statsmodels.tsa.stattools import adfuller, kpss

def test_stationarity(series):
    """Run ADF and KPSS tests. Both must agree."""
    series = series[~np.isnan(series)]
    adf_stat, adf_pval, *_ = adfuller(series, autolag='AIC')
    kpss_stat, kpss_pval, *_ = kpss(series, regression='c', nlags='auto')
    return {
        'adf_pval': adf_pval,     # H0: unit root (non-stationary)
        'kpss_pval': kpss_pval,   # H0: stationary
        'stationary': adf_pval < 0.05 and kpss_pval > 0.05
    }

# Test before modeling
for col in ['price', 'returns', 'momentum_12m', 'volatility_20d']:
    result = test_stationarity(features[col].to_numpy())
    status = "OK" if result['stationary'] else "TRANSFORM"
    print(f"{col:>20}: ADF p={result['adf_pval']:.3f}, "
          f"KPSS p={result['kpss_pval']:.3f} -> {status}")
```

## Decision Matrix

| ADF rejects H0? | KPSS rejects H0? | Conclusion | Action |
|---|---|---|---|
| Yes | No | Stationary | Use as-is |
| No | Yes | Non-stationary | Difference or use returns |
| Yes | Yes | Trend-stationary | Remove trend, then use |
| No | No | Inconclusive | Get more data or use returns |

## Making Features Stationary

```python
# Method 1: First difference (simplest)
diff = series.diff().dropna()

# Method 2: Log returns (standard for prices)
log_ret = np.log(series / series.shift(1)).dropna()

# Method 3: Fractional differentiation (preserves memory)
# d=1.0 is full differencing; d=0.3-0.5 balances stationarity + memory
from fracdiff import fdiff
frac_diff = fdiff(series.to_numpy(), d=0.4)
```

## Guardrails

- Always run BOTH ADF and KPSS — they have opposite null hypotheses and catch different failures
- KPSS is sensitive to lag selection; use `nlags='auto'` to avoid misleading results
- Returns are almost always stationary; prices almost never are
- Non-stationary features can still be useful inside tree-based models (which split on rank), but regularized linear models and neural networks require stationarity
- After transformation, verify IC is preserved — aggressive differencing can destroy signal

## Production Implementation

`ml4t-diagnostic` provides batch stationarity testing:

```python
from ml4t.diagnostic.evaluation.stats import robust_ic

# robust_ic handles non-stationary inputs by auto-detecting
# and applying appropriate transformations before IC computation
ic_result = robust_ic(signal, forward_returns)
```

## Checklist

- [ ] Both ADF and KPSS tests run on every feature
- [ ] Non-stationary features transformed (differencing, returns, or frac-diff)
- [ ] Transformation method documented per feature
- [ ] IC compared before vs after transformation to verify signal preservation
- [ ] Tree models distinguished from linear/DL models in stationarity requirements
