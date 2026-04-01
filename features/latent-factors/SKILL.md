---
name: ml4t-latent-factors
description: "Extract latent factors from return panels using PCA, IPCA, or autoencoders with proper noise diagnostics. Use when reducing dimensionality or discovering risk structure."
when_to_use: "Use when building factor models from high-dimensional return or characteristic panels"
dependencies: [lookahead-bias, walk-forward-cv]
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
metadata:
  book_chapters: "14"
  library: "ml4t-diagnostic"
---
# Latent Factor Extraction

PCA explains 80% of return variance — but variance is not alpha. The first principal component captures market beta, which earns the equity premium, not a tradeable edge. Confusing variance-explained with pricing power is the central mistake.

## The Problem

With 400+ published return predictors, hand-picking factors invites overfitting. Latent factor methods (PCA, autoencoders) extract structure directly from data. But three failure modes undermine them:

1. **Variance != pricing** — high-variance factors may capture idiosyncratic noise, not compensated risk.
2. **Eigenvector instability** — when assets (N) approach time periods (T), sample covariance is dominated by noise. Marchenko-Pastur theory gives the noise boundary.
3. **Full-sample PCA is leakage** — fitting PCA on the complete panel, then testing on a held-out period, leaks the covariance structure of the test period into training.

## The Pattern

### WRONG
```python
from sklearn.decomposition import PCA
import numpy as np

# Fit PCA on FULL return panel, then use factors for prediction
pca = PCA(n_components=5)
factors = pca.fit_transform(returns_panel)  # Full-sample fit = leakage

# "80% variance explained" — but does it predict returns?
print(f"Explained variance: {pca.explained_variance_ratio_.sum():.1%}")
signal = factors[:, 0]  # Assumes first PC predicts returns
```

### CORRECT
```python
from sklearn.decomposition import PCA
import numpy as np

# Walk-forward PCA: fit on training window only
def walk_forward_pca(returns, n_components=5, train_window=504):
    """Fit PCA per fold, project test data with training eigenvectors."""
    factors = np.full((len(returns), n_components), np.nan)
    for t in range(train_window, len(returns)):
        train = returns[t - train_window:t]
        pca = PCA(n_components=n_components)
        pca.fit(train)
        factors[t] = pca.transform(returns[t:t+1])
    return factors

# Noise test: compare eigenvalues to Marchenko-Pastur upper bound
def mp_upper_bound(n_assets, n_periods):
    """Random matrix theory noise threshold."""
    gamma = n_assets / n_periods
    return (1 + np.sqrt(gamma)) ** 2

# Only keep components whose eigenvalue exceeds the noise bound
threshold = mp_upper_bound(n_assets=100, n_periods=504)
significant = pca.explained_variance_[:5] > threshold
print(f"Signal components: {significant.sum()} of 5")
```

## Method Comparison

| Method | Strengths | Limitations |
|--------|-----------|-------------|
| PCA | Fast, linear, interpretable loadings | Static betas, variance != pricing |
| IPCA | Dynamic betas via characteristics | Sensitive to characteristic selection |
| Autoencoder | Non-linear factor structure | Overfits without adversarial constraints |
| RP-PCA | Incorporates risk-premium signal | Requires pricing-error objective |

Start with PCA + Marchenko-Pastur filtering. Graduate to IPCA only if characteristics drive time-varying exposures.

## Guardrails

- **Walk-forward fit**: PCA must be re-fit on each fold's training data — never on the full panel
- **Marchenko-Pastur test**: discard components below the random-matrix noise bound
- **Microcap bias**: equal-weighted PCA is dominated by small/illiquid stocks — use market-cap weighting or NYSE breakpoints
- **Loading rotation**: eigenvectors are not stable across subperiods — don't assign fixed economic labels ("this is momentum")
- **Autoencoder seeds**: report results across 10+ random seeds; single-seed results are unreliable

## Production Implementation

`ml4t-diagnostic` provides factor evaluation infrastructure for custom latent factor outputs:

```python
import polars as pl
from ml4t.diagnostic.api import compute_ic_series

# After walk-forward PCA, evaluate factor predictiveness via IC
ic = compute_ic_series(
    predictions=factor_df,      # DataFrame with date, symbol, prediction
    returns=forward_returns_df,  # DataFrame with date, symbol, forward_return
    date_col="date",
    entity_col="symbol",
)
```

## Checklist

- [ ] PCA fit walk-forward per fold, not on full panel
- [ ] Marchenko-Pastur noise threshold applied to discard noise components
- [ ] Variance-explained distinguished from predictive power (IC tested)
- [ ] Microcap bias controlled (cap-weighted or filtered universe)
- [ ] Results stable across random seeds (for autoencoders)
