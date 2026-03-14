---
name: ml4t-feature-validation
description: Quality checks before using features in models
category: features
type: operational
dependencies: [validate-data, information-coefficient]
book_chapters: [7, 9]
---

# Feature Validation

Verify features are clean and predictive before modeling.

## Quality Checks

| Check | Method | Action |
|-------|--------|--------|
| Missing values | `null_count()` | Impute or drop |
| Outliers | `abs(z) > 5` | Winsorize |
| Stationarity | ADF test | Difference |
| Constant | `nunique() < 10` | Drop |
| Leakage | IC decay | Investigate |

## Validation Pipeline

```python
def validate_features(X: pl.DataFrame, y: pl.Series) -> dict:
    """Run feature quality checks."""
    results = {}

    for col in X.columns:
        results[col] = {
            'null_pct': X[col].null_count() / len(X),
            'unique_pct': X[col].n_unique() / len(X),
            'outlier_pct': (X[col].abs() > 5 * X[col].std()).mean(),
            'ic': information_coefficient(X[col], y).mean(),
        }

    return results
```

## Outlier Treatment

```python
def winsorize(x: pl.Series, limits: tuple = (0.01, 0.99)) -> pl.Series:
    """Clip extreme values."""
    lower = x.quantile(limits[0])
    upper = x.quantile(limits[1])
    return x.clip(lower, upper)
```

## Leakage Detection

```python
# Suspiciously high IC suggests leakage
if ic > 0.3:
    print(f"WARNING: {col} has IC={ic:.2f}, check for leakage")

# IC should decay with horizon
for horizon in [1, 5, 20, 60]:
    ic = information_coefficient(X[col], returns.shift(-horizon))
    print(f"IC at {horizon}d: {ic:.3f}")
```

## Stability Analysis

```python
# Check IC stability across time
rolling_ic = []
for start in pd.date_range(X.index.min(), X.index.max(), freq='Q'):
    end = start + pd.DateOffset(months=3)
    ic = information_coefficient(X.loc[start:end], y.loc[start:end])
    rolling_ic.append(ic)

# High variance = unstable feature
ic_ir = np.mean(rolling_ic) / np.std(rolling_ic)
```

## Guardrails

- High IC (>0.1) is suspicious without clear mechanism
- IC should decay with prediction horizon
- Unstable features may be noise
- Cross-sectional and time-series IC can differ

## Checklist

- [ ] Missing values handled
- [ ] Outliers winsorized
- [ ] IC calculated per feature
- [ ] Leakage check (IC too high?)
- [ ] Stability across time assessed
