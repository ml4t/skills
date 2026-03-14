---
name: ml4t-drift-detection
description: Detect data and model drift in production
category: validation
type: operational
dependencies: []
book_chapters: [26, 27]
---

# Drift Detection

Monitor for distribution shifts that degrade model performance.

## Drift Types

| Type | What Changes | Detection |
|------|--------------|-----------|
| Data drift | Input distribution | PSI, KS test |
| Concept drift | X→Y relationship | Performance decay |
| Prior drift | Target distribution | Class balance |

## Population Stability Index (PSI)

```python
def calculate_psi(expected: np.ndarray, actual: np.ndarray,
                  n_bins: int = 10) -> float:
    """PSI between reference and current distributions."""
    # Bin the data
    breakpoints = np.percentile(expected, np.linspace(0, 100, n_bins + 1))
    expected_pct = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    actual_pct = np.histogram(actual, bins=breakpoints)[0] / len(actual)

    # Avoid division by zero
    expected_pct = np.clip(expected_pct, 0.001, None)
    actual_pct = np.clip(actual_pct, 0.001, None)

    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return psi

# Interpretation
# PSI < 0.1: No drift
# PSI 0.1-0.25: Moderate drift
# PSI > 0.25: Significant drift
```

## KS Test for Drift

```python
from scipy.stats import ks_2samp

def detect_drift(reference: np.ndarray, current: np.ndarray,
                 threshold: float = 0.05) -> bool:
    """Kolmogorov-Smirnov test for drift."""
    stat, pval = ks_2samp(reference, current)
    return pval < threshold  # True if drift detected
```

## Performance Monitoring

```python
def rolling_performance(predictions: pl.DataFrame,
                        window: int = 63) -> pl.DataFrame:
    """Track rolling IC and accuracy."""
    return predictions.with_columns([
        pl.corr('pred', 'actual').rolling(window).alias('rolling_ic'),
        (pl.col('pred_class') == pl.col('actual_class'))
          .rolling(window).mean().alias('rolling_accuracy')
    ])

# Alert on significant decline
if current_ic < baseline_ic * 0.7:
    trigger_alert("IC declined 30%+")
```

## Monitoring Dashboard

```python
metrics_to_monitor = {
    'feature_drift': lambda: max(calculate_psi(f) for f in features),
    'rolling_sharpe': lambda: rolling_returns.mean() / rolling_returns.std(),
    'rolling_ic': lambda: rolling_ic.mean(),
    'max_drawdown': lambda: calculate_drawdown(portfolio)
}

# Alert thresholds
thresholds = {
    'feature_drift': 0.25,
    'rolling_sharpe': 0.5,
    'rolling_ic': 0.02,
    'max_drawdown': 0.15
}
```

## Guardrails

- Baseline period should be stable, representative
- Multiple metrics catch different drift types
- Some drift is normal; establish baselines
- Retrain triggers should be pre-defined

## Checklist

- [ ] PSI calculated for key features
- [ ] Performance metrics tracked
- [ ] Alert thresholds defined
- [ ] Retrain triggers documented
