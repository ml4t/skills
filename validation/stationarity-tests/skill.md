---
name: ml4t-stationarity-tests
description: Test time series for stationarity
category: validation
type: operational
dependencies: [non-stationarity]
book_chapters: [6, 9]
---

# Stationarity Tests

Verify features are stationary before modeling.

## Tests

| Test | H0 | Stationary if |
|------|-----|--------------|
| ADF | Unit root | p < 0.05 |
| KPSS | Stationary | p > 0.05 |
| PP | Unit root | p < 0.05 |

## API

```python
from statsmodels.tsa.stattools import adfuller, kpss

def test_stationarity(series: np.ndarray) -> dict:
    """Run ADF and KPSS tests."""
    # ADF: H0 = has unit root (non-stationary)
    adf_stat, adf_pval, *_ = adfuller(series, autolag='AIC')

    # KPSS: H0 = stationary
    kpss_stat, kpss_pval, *_ = kpss(series, regression='c')

    return {
        'adf_statistic': adf_stat,
        'adf_pvalue': adf_pval,
        'kpss_statistic': kpss_stat,
        'kpss_pvalue': kpss_pval,
        'is_stationary': adf_pval < 0.05 and kpss_pval > 0.05
    }
```

## Decision Matrix

| ADF | KPSS | Conclusion |
|-----|------|------------|
| Reject | Fail to reject | Stationary |
| Fail to reject | Reject | Non-stationary |
| Reject | Reject | Trend-stationary |
| Fail to reject | Fail to reject | Need more data |

## Making Stationary

```python
# Method 1: First difference
diff = series.diff().dropna()

# Method 2: Log returns
log_ret = np.log(series).diff().dropna()

# Method 3: Fractional differentiation (preserves memory)
from fracdiff import fdiff
frac_diff = fdiff(series, d=0.4)  # 0 < d < 1
```

## Batch Testing

```python
def test_all_features(X: pl.DataFrame) -> pl.DataFrame:
    """Test stationarity of all features."""
    results = []
    for col in X.columns:
        test = test_stationarity(X[col].drop_nulls().to_numpy())
        results.append({
            'feature': col,
            'adf_pval': test['adf_pvalue'],
            'kpss_pval': test['kpss_pvalue'],
            'stationary': test['is_stationary']
        })
    return pl.DataFrame(results)
```

## Guardrails

- Both ADF and KPSS should agree
- KPSS is sensitive to number of lags
- Returns are usually stationary; prices are not
- Non-stationary features can still be useful

## Checklist

- [ ] Both ADF and KPSS run
- [ ] Features made stationary if needed
- [ ] Transformation documented
- [ ] Original vs transformed IC compared
