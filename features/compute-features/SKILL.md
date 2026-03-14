---
name: ml4t-compute-features
description: Config-driven feature computation with dependency resolution
category: features
type: operational
dependencies: [lookahead-bias]
book_chapters: [7]
quantlab_module: ml4t.engineer.api
---

# Compute Features

Config-driven feature computation with automatic dependency resolution.

## API

```python
from ml4t.engineer.api import compute_features

# Three input formats:
# 1. List of feature names (default params)
df = compute_features(data, ["rsi", "macd", "bollinger_bands"])

# 2. List of dicts with custom params
df = compute_features(data, [
    {"name": "rsi", "params": {"period": 14}},
    {"name": "macd", "params": {"fast": 12, "slow": 26}},
])

# 3. YAML config file
df = compute_features(data, "config/features.yaml")
```

## Available Features

| Category | Features |
|----------|----------|
| Trend | sma, ema, dema, tema, kama, t3, trima |
| Momentum | rsi, macd, stochastic, roc, kdj |
| Volatility | bollinger_bands, atr, keltner |
| Volume | obv, ad_line, chaikin |
| Microstructure | amihud, kyle_lambda, roll_spread, vpin |
| Statistics | linear_reg, variance, std_dev |

## YAML Config Format

```yaml
# features.yaml
features:
  - name: rsi
    params:
      period: 14
  - name: macd
    params:
      fast: 12
      slow: 26
      signal: 9
  - name: bollinger_bands
    params:
      period: 20
      std_dev: 2.0
```

## Feature Registry

```python
from ml4t.engineer.core.registry import get_registry

registry = get_registry()
print(registry.list_features())  # All available
print(registry.get_feature("rsi"))  # Feature metadata
```

## Guardrails

- Features computed in topological order (dependencies first)
- Uses Polars expressions (lazy evaluation supported)
- Input must have OHLCV columns for most features
- Check `feature.lookback` for minimum data requirements
