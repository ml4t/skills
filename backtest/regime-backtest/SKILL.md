---
name: ml4t-regime-backtest
description: "Decompose strategy performance by market regime — volatility, trend, liquidity. Use when diagnosing whether a strategy is regime-dependent."
when_to_use: "Use when aggregate metrics hide regime-dependent fragility"
dependencies: [run-backtest]
metadata:
  book_chapters: "16, 19"
  library: ""
paths: ["**/*backtest*.py", "**/*strategy*.py", "**/*engine*.py", "**/*broker*.py", "**/*cost*.py", "**/*regime*.py", "**/*tearsheet*.py"]
---
# Regime-Conditional Backtesting

An aggregate Sharpe of 1.2 might come from Sharpe 3.0 in bull markets and -0.5 in bear markets. Reporting only the aggregate hides the most important question: does the strategy survive the regimes that matter most?

## The Problem

Strategies often harvest one regime and bleed in others. A momentum strategy that earns 80% of returns during trending markets and loses during choppy periods looks fine in aggregate over a bull run — but collapses when the regime shifts. Without per-regime decomposition, you cannot tell whether your alpha is robust or regime-dependent.

## The Pattern

### WRONG
```python
import numpy as np

# One number for the whole period — hides regime dependence
sharpe = returns.mean() / returns.std() * np.sqrt(252)
print(f"Sharpe: {sharpe:.2f}")  # "Looks great!" ... until the regime changes
```

### CORRECT
```python
import polars as pl
import numpy as np

def classify_regimes(df: pl.DataFrame) -> pl.DataFrame:
    """Label each bar by volatility and trend regime (using lagged data only)."""
    return df.with_columns(
        vol_regime=pl.when(
            pl.col("close").pct_change().rolling_std(63) >
            pl.col("close").pct_change().rolling_std(63).shift(1).rolling_quantile(0.7, window_size=252)
        ).then(pl.lit("high_vol")).otherwise(pl.lit("low_vol")),
        trend_regime=pl.when(
            pl.col("close").pct_change().rolling_mean(63) > 0
        ).then(pl.lit("bull")).otherwise(pl.lit("bear")),
    )

def regime_metrics(df: pl.DataFrame, ret_col: str = "strategy_ret") -> pl.DataFrame:
    """Sharpe, drawdown, and day count per regime."""
    return df.group_by("vol_regime", "trend_regime").agg(
        sharpe=(pl.col(ret_col).mean() / pl.col(ret_col).std() * np.sqrt(252)),
        max_dd=(
            (pl.col(ret_col).cum_sum() - pl.col(ret_col).cum_sum().cum_max()).min()
        ),
        days=pl.col(ret_col).count(),
    )
```

## Stress Period Overlay

Define known stress periods and report strategy behavior during each:

```python
STRESS_PERIODS = {
    "GFC":        ("2008-09-01", "2009-03-31"),
    "COVID":      ("2020-02-15", "2020-03-31"),
    "Rate shock": ("2022-01-01", "2022-06-30"),
}

for name, (start, end) in STRESS_PERIODS.items():
    subset = df.filter(pl.col("timestamp").is_between(start, end))
    ret = subset.get_column("strategy_ret")
    print(f"{name}: return={ret.sum():.1%}, max_dd={...:.1%}, days={len(ret)}")
```

Stress periods are in-sample (known events), so they test survival, not prediction.

## Guardrails

- Regime classification must use **lagged** indicators — computing a 63-day rolling stat uses only past data, but make sure the threshold (quantile breakpoint) is also expanding/rolling, not computed on the full sample
- Some regimes have few observations — report day count alongside metrics and do not trust Sharpe from fewer than 60 days
- A strategy that only works in one regime is fragile — demand positive Sharpe in at least 3 of 4 quadrants (bull/bear x low/high vol)

## Production Implementation

`ml4t-backtest` strategies can condition on regime within `on_data`:

```python
from ml4t.backtest import Strategy

class RegimeAware(Strategy):
    def on_data(self, timestamp, data, context, broker):
        regime = context.get("vol_regime", "low_vol")
        if regime == "high_vol":
            # reduce exposure or skip trading
            return
        # normal logic
```

## Checklist

- [ ] At least two regime dimensions tested (volatility + trend)
- [ ] Regime labels computed from lagged data only (no lookahead in thresholds)
- [ ] Per-regime Sharpe, max drawdown, and day count reported
- [ ] Strategy profitable in at least 3 of 4 regime quadrants
- [ ] Known stress periods analyzed separately
