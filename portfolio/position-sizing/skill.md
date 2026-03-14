---
name: ml4t-position-sizing
description: Determine position sizes from signals and risk constraints
category: portfolio
type: operational
dependencies: [transaction-costs]
book_chapters: [18, 20]
---

# Position Sizing

Convert signals to position weights with risk control.

## Methods

| Method | Formula | Use Case |
|--------|---------|----------|
| Equal | 1/N | Baseline |
| Signal | signal / sum(abs(signal)) | Alpha-weighted |
| Volatility | 1 / vol | Risk parity lite |
| Kelly | edge / variance | Theoretical optimal |
| Risk budget | target_risk / expected_risk | Vol targeting |

## Kelly Criterion

```python
def kelly_fraction(
    expected_return: float,
    volatility: float,
    risk_free: float = 0
) -> float:
    """Full Kelly sizing."""
    excess = expected_return - risk_free
    return excess / (volatility ** 2)

# Half Kelly is more common (reduces variance)
position = kelly_fraction(mu, sigma) / 2
```

## Volatility Targeting

```python
def vol_target_weight(
    signal: pl.Series,
    realized_vol: pl.Series,
    target_vol: float = 0.10
) -> pl.Series:
    """Scale positions to target volatility."""
    base_weight = signal / signal.abs().sum()
    vol_scalar = target_vol / realized_vol
    return base_weight * vol_scalar.clip(0.5, 2.0)
```

## Risk Budget

```python
def risk_budget_sizing(
    signals: pl.DataFrame,
    covariance: np.ndarray,
    target_risk: float = 0.10
) -> np.ndarray:
    """Size to target portfolio volatility."""
    normalized = signals / signals.abs().sum()
    weights = normalized.values

    # Current portfolio risk
    port_var = weights @ covariance @ weights
    port_vol = np.sqrt(port_var) * np.sqrt(252)

    # Scale to target
    scale = target_risk / port_vol
    return weights * min(scale, 2.0)  # Cap leverage
```

## Constraints

```python
def apply_constraints(
    weights: np.ndarray,
    max_position: float = 0.10,
    max_sector: float = 0.30,
    max_leverage: float = 1.0,
    sectors: np.ndarray = None
) -> np.ndarray:
    """Apply portfolio constraints."""
    # Position limits
    weights = np.clip(weights, -max_position, max_position)

    # Sector limits
    if sectors is not None:
        for s in np.unique(sectors):
            mask = sectors == s
            sector_weight = weights[mask].sum()
            if abs(sector_weight) > max_sector:
                weights[mask] *= max_sector / abs(sector_weight)

    # Leverage
    leverage = np.abs(weights).sum()
    if leverage > max_leverage:
        weights *= max_leverage / leverage

    return weights
```

## Guardrails

- Full Kelly is too aggressive; use half or quarter
- Volatility estimates are noisy; use smoothed values
- Constraints prevent concentration
- Transaction costs may favor slower rebalancing

## Checklist

- [ ] Sizing method documented
- [ ] Maximum position limits set
- [ ] Leverage constraint applied
- [ ] Volatility targeting if appropriate
