---
name: ml4t-regime-awareness
description: "Market regimes as conditioning features for risk scaling, not timing signals. Use when incorporating regime detection into strategy logic."
when_to_use: "Use when building features, sizing positions, or evaluating strategy robustness across market conditions"
dependencies: []
metadata:
  book_chapters: "9"
  library: "ml4t-engineer"
---
# Regime Awareness

Markets alternate between regimes (low/high volatility, trending/mean-reverting, risk-on/risk-off). Regime detection for diagnostics and risk scaling is reliable. Regime detection for market timing is not.

## The Problem

Regime-switching models promise to predict when to be in or out of the market. In practice, regime transitions are identified with high confidence only after they have already occurred. A model that correctly labels the March 2020 crash as "crisis" does so 2-4 weeks late, after the drawdown has already happened. Trading on regime predictions produces whipsaw losses and underperforms a regime-conditioned but always-invested approach.

The correct use of regimes is as a conditioning feature: scale risk, adjust position sizes, and evaluate strategy performance per regime - but stay invested.

## The Pattern

### WRONG

```python
# Regime-timing: go to cash when model predicts "bear"
def generate_signal(data, regime_model):
    regime = regime_model.predict(data)
    if regime == "bear":
        return 0.0       # exit market entirely
    else:
        return model.predict(data)  # normal signal
```

### CORRECT

```python
import numpy as np

# Regime-as-feature: condition risk scaling on observable regime indicator
realized_vol = returns.rolling(21).std() * np.sqrt(252)
vol_rank = realized_vol.rolling(252).rank(pct=True)

# Tercile-based regime label (observable, no prediction needed)
regime = np.where(vol_rank < 0.33, "low_vol",
         np.where(vol_rank < 0.66, "mid_vol", "high_vol"))

# Scale position sizes by regime (always invested, risk-adjusted)
vol_scale = {"low_vol": 1.3, "mid_vol": 1.0, "high_vol": 0.5}
position = base_signal * np.vectorize(vol_scale.get)(regime)
```

## Regime Indicators

| Type | Indicators | Use case |
|------|------------|----------|
| Volatility | Realized vol, VIX, ATR percentile | Risk scaling |
| Trend | ADX, SMA slope, momentum sign | Feature conditioning |
| Liquidity | Bid-ask spread, volume ratio, Amihud | Position sizing |
| Macro | Yield curve slope, credit spread | Regime label |

## Regime-Sliced Evaluation

Always evaluate strategy performance per regime, not just in aggregate:

```python
import numpy as np

for label in ["low_vol", "mid_vol", "high_vol"]:
    mask = regime == label
    regime_ret = strategy_returns[mask]
    sharpe = regime_ret.mean() / regime_ret.std() * np.sqrt(252)
    max_dd = (np.maximum.accumulate(regime_ret.cumsum()) - regime_ret.cumsum()).max()
    print(f"{label}: Sharpe={sharpe:.2f}, MaxDD={max_dd:.1%}, N={mask.sum()}")
```

A strategy with Sharpe 1.5 that comes entirely from one regime is fragile. Robust strategies have positive (if unequal) performance across all regimes.

## Guardrails

- Define regime labels BEFORE backtesting - choosing regimes after seeing results is snooping.
- Use observable indicators (realized vol, yield curve slope), not latent model outputs, for regime classification.
- Report strategy metrics per regime in every backtest report.
- Never use regime prediction for binary in/out decisions - use it for continuous risk scaling.
- Regime labels must use expanding or rolling windows to avoid lookahead bias.

## Production Implementation

`ml4t-engineer` exposes regime indicators as model inputs:

```python
from ml4t.engineer import compute_features

regime_inputs = compute_features(data, [
    "adx",
    "choppiness_index",
    "volatility_percentile_rank",
])
data = data.join(regime_inputs, on=["timestamp", "symbol"], how="left")
```

Use these as conditioning features or sizing inputs, not binary in/out switches.

## Checklist

- [ ] Regime definitions specified ex-ante (in strategy term sheet, before backtesting)
- [ ] Regime labels use only backward-looking data (no lookahead)
- [ ] Strategy metrics reported per regime (not just aggregate Sharpe)
- [ ] Position sizing or risk parameters vary with regime (continuous scaling)
- [ ] No binary market-timing signals based on regime prediction
