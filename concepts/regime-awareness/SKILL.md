---
name: ml4t-regime-awareness
description: Handle non-stationarity via regime-as-a-feature approach
category: concepts
type: conceptual
dependencies: []
book_chapters: [1, 7, 17]
---

# Regime Awareness

Markets are non-stationary. Regime awareness is mandatory for risk management.

## Key Principle

Use **regime-as-a-feature** (robust indicators), NOT regime-switching timing.

Regime detection for diagnostics = reliable
Regime detection for timing = brittle, usually fails

## Regime Indicators

| Type | Indicators | Use |
|------|------------|-----|
| Volatility | VIX, realized vol, ATR state | Risk scaling |
| Trend | ADX, slope of SMA, momentum sign | Strategy selection |
| Liquidity | Spread, volume, Amihud | Position sizing |
| Macro | Yield curve slope, credit spreads | Regime filter |

## Implementation

```python
# Regime as feature, not as timing signal
df['vol_regime'] = (
    df['realized_vol_20']
    .rolling(252).rank(pct=True)
    .cut(bins=[0, 0.33, 0.66, 1.0], labels=['low', 'mid', 'high'])
)

# Use for conditioning, not timing
df['position_size'] = df['base_size'] * df['vol_regime'].map({
    'low': 1.5, 'mid': 1.0, 'high': 0.5
})
```

## Regime-Sliced Evaluation

```python
# Evaluate strategy BY regime, not conditionally trade
for regime in ['low', 'mid', 'high']:
    regime_returns = returns[df['vol_regime'] == regime]
    print(f"{regime}: Sharpe={sharpe_ratio(regime_returns):.2f}")
```

## Guardrails

- Define regimes BEFORE backtesting (prevent regime-snooping)
- Report metrics per regime, not just aggregate
- Don't trade based on regime prediction (usually fails)
- Use regime for risk scaling, not entry timing

## Rules

```python
# WRONG: Trade regime timing
if predict_regime() == 'bull':
    go_long()

# CORRECT: Regime conditions strategy
base_signal = model.predict(X)
position = base_signal * vol_scaling[current_regime]
```

## Checklist

- [ ] Regime definitions specified ex-ante (in Strategy Term Sheet)
- [ ] Backtest shows performance by regime
- [ ] Risk parameters vary with regime
- [ ] Not timing entry/exit based on regime prediction
