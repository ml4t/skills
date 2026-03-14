---
name: ml4t-vectorized-backtest
description: Fast array-based backtesting for factor strategies
category: backtest
type: operational
dependencies: [run-backtest]
book_chapters: [17]
---

# Vectorized Backtest

Fast backtesting using array operations instead of event loops.

## When to Use

| Approach | Use Case | Speed |
|----------|----------|-------|
| Vectorized | Long-only, no path dependence | Very fast |
| Event-driven | Complex rules, path dependence | Slower |

## API

```python
def vectorized_backtest(
    signals: pl.DataFrame,    # (date, symbol) → signal
    returns: pl.DataFrame,    # (date, symbol) → return
    weight_func: str = 'equal',
    max_weight: float = 0.10
) -> pl.DataFrame:
    """
    Vectorized portfolio backtest.

    Returns portfolio returns series.
    """
    # Shift signals to avoid lookahead
    positions = signals.shift(1)

    # Apply weighting
    if weight_func == 'equal':
        weights = positions / positions.abs().sum(axis=1)
    elif weight_func == 'signal':
        weights = positions / positions.abs().sum(axis=1)

    # Clip weights
    weights = weights.clip(-max_weight, max_weight)

    # Portfolio return = sum(weight * return)
    portfolio_returns = (weights * returns).sum(axis=1)

    return portfolio_returns
```

## Position Matrix

```python
# Build position matrix from signals
def signal_to_positions(signal: pl.DataFrame, long_only: bool = True):
    """Convert continuous signal to positions."""
    if long_only:
        # Top quintile = 1, rest = 0
        return (signal.rank(pct=True) > 0.8).cast(pl.Int8)
    else:
        # Long top, short bottom
        rank = signal.rank(pct=True)
        return (
            pl.when(rank > 0.8).then(1)
            .when(rank < 0.2).then(-1)
            .otherwise(0)
        )
```

## Turnover Estimation

```python
def turnover(weights: pl.DataFrame) -> pl.Series:
    """Calculate daily turnover."""
    weight_changes = weights.diff().abs()
    return weight_changes.sum(axis=1) / 2  # Two-sided
```

## With Transaction Costs

```python
def backtest_with_costs(
    weights: pl.DataFrame,
    returns: pl.DataFrame,
    cost_bps: float = 10
) -> pl.DataFrame:
    """Vectorized backtest including costs."""
    gross_returns = (weights.shift(1) * returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1) / 2
    costs = turnover * cost_bps / 10000
    return gross_returns - costs
```

## Guardrails

- Must shift signals to prevent lookahead
- Cannot handle path-dependent rules
- Transaction costs are approximations
- No realistic fill simulation

## Checklist

- [ ] Signals shifted before use
- [ ] Weights normalized
- [ ] Turnover calculated
- [ ] Costs included
