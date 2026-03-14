---
name: ml4t-vectorized-backtest
description: Fast array-based signal evaluation for factor strategies. Use when screening signals before committing to full event-driven simulation.
dependencies: [run-backtest]
metadata:
  book_chapters: "16"
  library: ""
---

# Vectorized Backtesting

Matrix operations can evaluate a signal across thousands of assets in seconds — but only if you shift positions by one bar. Without the shift, you are trading on prices you have already seen, and the backtest is meaningless.

## The Problem

Vectorized backtests compute `positions * returns` in one shot. The critical mistake is using today's signal to trade today's return. That is lookahead bias: you are "buying" at the price your signal already observed. The fix is a single `.shift(1)` — but forgetting it inflates Sharpe by 0.5-1.0 or more.

## The Pattern

### WRONG
```python
import polars as pl

# Signal computed on close[t], applied to return[t] — lookahead!
signals = df.with_columns(
    signal=pl.col("close").pct_change(21)  # 21-day momentum
)
positions = (signals.get_column("signal") > 0).cast(pl.Int8)
returns = df.get_column("close").pct_change()
strategy_returns = positions * returns  # BUG: no shift
```

### CORRECT
```python
import polars as pl
import numpy as np

# Shift positions by 1: decide on bar t, hold from t+1
df = df.with_columns(
    signal=pl.col("close").pct_change(21),
    fwd_ret=pl.col("close").pct_change().shift(-1),  # next-bar return
)
positions = (pl.col("signal") > 0).cast(pl.Int8)

result = df.with_columns(positions=positions).with_columns(
    gross_ret=pl.col("positions") * pl.col("fwd_ret"),
    turnover=pl.col("positions").diff().abs(),
).with_columns(
    net_ret=pl.col("gross_ret") - pl.col("turnover") * 10 / 10_000,  # 10 bps cost
)

sharpe = (
    result.get_column("net_ret").mean()
    / result.get_column("net_ret").std()
    * np.sqrt(252)
)
```

## Cross-Sectional Signals (Multi-Asset)

For panel data, rank across assets each day then compute portfolio returns:

```python
ranked = (
    df.with_columns(
        rank=pl.col("signal").rank().over("timestamp") /
             pl.col("signal").count().over("timestamp")
    )
    .with_columns(
        weight=pl.when(pl.col("rank") > 0.8).then(1)
               .when(pl.col("rank") < 0.2).then(-1)
               .otherwise(0)
    )
)
# Normalize weights per day, then portfolio_return = sum(weight * fwd_ret)
```

## Limitations

Vectorized backtests **cannot** model: position limits, partial fills, path-dependent exits (stop-loss, trailing stop), margin requirements, or realistic slippage. Use them for signal screening, then validate winners with event-driven simulation.

## Guardrails

- Missing `.shift(1)` on positions (or equivalent `.shift(-1)` on returns) is the most common vectorized backtest bug
- Turnover estimate = `abs(weight_change).sum() / 2` per rebalance — include cost deduction
- Beware survivorship bias: if delisted assets disappear from your panel, long-only results are inflated
- Sharpe above 3.0 in a vectorized backtest almost certainly means a bug

## Production Implementation

For production validation, switch to `ml4t-backtest`'s event-driven engine (see `run-backtest` skill). Vectorized backtests are a screening tool, not a final answer.

## Checklist

- [ ] Positions shifted by 1 bar relative to signal (or returns shifted by -1)
- [ ] Weights normalized per rebalance date (sum to 1 or market-neutral)
- [ ] Turnover computed and cost deducted from gross returns
- [ ] No survivorship bias in the asset universe
- [ ] Winners re-validated with event-driven backtest
