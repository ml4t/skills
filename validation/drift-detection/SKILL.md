---
name: ml4t-drift-detection
description: Detect when model inputs or predictions shift from the training distribution using PSI and statistical tests. Use when monitoring deployed models or diagnosing out-of-sample performance decay.
dependencies: []
metadata:
  book_chapters: "9, 16"
  library: "ml4t-diagnostic"
---

# Drift Detection

A model trained on 2018-2022 data may silently fail when the 2023 distribution shifts. Systematic drift detection catches degradation before it becomes a drawdown.

## The Problem

Financial distributions are non-stationary. Volatility regimes change, correlations spike during crises, and feature distributions shift as markets evolve. A model deployed without monitoring can trade on stale assumptions for months. The three drift types — data drift (input distributions change), concept drift (feature-target relationship changes), and prior drift (target distribution changes) — each require different detection strategies. By the time performance metrics visibly decay, the damage is already done.

## The Pattern

### WRONG

```python
# Deploy model and check performance monthly — too late
model = train_model(X_train, y_train)
# ... 3 months later ...
print(f"Live Sharpe: {live_sharpe:.2f}")  # Already lost money
```

### CORRECT

```python
import numpy as np
from scipy.stats import ks_2samp

def calculate_psi(reference, current, n_bins=10):
    """Population Stability Index between two distributions."""
    breakpoints = np.percentile(reference, np.linspace(0, 100, n_bins + 1))
    ref_pct = np.histogram(reference, bins=breakpoints)[0] / len(reference)
    cur_pct = np.histogram(current, bins=breakpoints)[0] / len(current)
    ref_pct = np.clip(ref_pct, 1e-4, None)
    cur_pct = np.clip(cur_pct, 1e-4, None)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))

# Monitor every feature at each rebalance
ref_data = X_train  # Training period as baseline
cur_data = X_live   # Most recent window

for col_idx, col_name in enumerate(feature_names):
    psi = calculate_psi(ref_data[:, col_idx], cur_data[:, col_idx])
    ks_stat, ks_pval = ks_2samp(ref_data[:, col_idx], cur_data[:, col_idx])
    flag = "DRIFT" if psi > 0.25 else "ok"
    print(f"{col_name:>25}: PSI={psi:.3f}, KS p={ks_pval:.3f} [{flag}]")
```

## PSI Thresholds

| PSI | Interpretation | Action |
|---|---|---|
| < 0.10 | No significant drift | Continue |
| 0.10 - 0.25 | Moderate drift | Investigate, increase monitoring |
| > 0.25 | Significant drift | Consider retraining |

## Detecting Concept Drift

Feature distributions can be stable while the feature-target relationship breaks. Track rolling IC to catch this:

```python
from scipy.stats import spearmanr

def rolling_ic(predictions, actuals, window=63):
    """Rolling rank IC to detect concept drift."""
    ic_series = []
    for i in range(window, len(predictions)):
        ic, _ = spearmanr(predictions[i-window:i], actuals[i-window:i])
        ic_series.append(ic)
    return np.array(ic_series)

ic = rolling_ic(model_predictions, realized_returns)
baseline_ic = np.mean(ic[:252])  # First year as baseline
if np.mean(ic[-63:]) < baseline_ic * 0.5:
    print("ALERT: IC declined >50% from baseline")
```

## Guardrails

- Baseline period must be representative and stable — do not use crisis periods as reference
- PSI and KS test catch different things: PSI is binned (better for tails), KS is continuous
- Some drift is normal in financial data — set thresholds based on historical drift rates, not arbitrary cutoffs
- Retrain triggers should be predefined (not decided after seeing losses)
- Monitor prediction distribution too, not just features — a model can produce drifted outputs from stable inputs

## Production Implementation

`ml4t-diagnostic` provides integrated drift monitoring:

```python
from ml4t.diagnostic.api import compute_ic_series
from ml4t.diagnostic.evaluation.drift import analyze_drift

drift = analyze_drift(reference_df, current_df, methods=["psi", "wasserstein"])
ic_df = compute_ic_series(predictions, forward_returns, entity_col="symbol")
recent_ic = ic_df.tail(63)["ic"].mean()
baseline_ic = ic_df.head(252)["ic"].mean()
print(f"Baseline IC: {baseline_ic:.4f}, Recent IC: {recent_ic:.4f}")
```

## Checklist

- [ ] PSI computed for all key features at each rebalance
- [ ] KS test run alongside PSI for continuous distribution comparison
- [ ] Rolling IC tracked for concept drift detection
- [ ] Alert thresholds predefined (not set after observing losses)
- [ ] Retrain protocol documented and triggered automatically on drift
