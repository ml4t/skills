---
name: ml4t-triple-barrier
description: Label trades using profit target, stop loss, and time barriers
category: features
type: operational
dependencies: [lookahead-bias]
book_chapters: [7]
quantlab_module: ml4t.engineer.labeling
---

# Triple-Barrier Labeling

Labels reflect trading outcomes: +1 (profit hit), -1 (stop hit), 0 (time expiry).

## API

```python
from ml4t.engineer.labeling.barriers import BarrierConfig, ATRBarrierConfig

# Fixed barriers
config = BarrierConfig(
    upper_barrier=0.02,      # 2% profit target
    lower_barrier=0.01,      # 1% stop loss
    max_holding_period=10,   # 10 bars max
    side=1                   # 1=long, -1=short, None=symmetric
)

# Volatility-adaptive barriers
config = ATRBarrierConfig(
    upper_multiplier=2.0,    # 2x ATR profit
    lower_multiplier=1.5,    # 1.5x ATR stop
    atr_period=14,
    max_holding_period=20
)
```

## Usage

```python
from ml4t.engineer.labeling import triple_barrier

labels = triple_barrier(
    prices=df,
    config=config,
    price_col="close",
    timestamp_col="date"
)
# Returns: label, exit_time, holding_period, return
```

## Dynamic Barriers

```python
# Use column names for adaptive barriers
df['upper'] = df['atr_14'] * 2
df['lower'] = df['atr_14'] * 1.5

config = BarrierConfig(
    upper_barrier='upper',
    lower_barrier='lower',
    max_holding_period=20
)
```

## Guardrails

- **Purging required**: label_horizon = max_holding_period
- **Class imbalance**: Check distribution, use class weights
- **Barrier width**: Too tight → mostly stops; too wide → mostly time expiry

```python
# CV must match label horizon
cv = CombinatorialPurgedCV(
    label_horizon=10,  # Same as max_holding_period
    embargo_size=2
)
```

## Label Interpretation

| Label | Long Position | Short Position |
|-------|--------------|----------------|
| +1 | Profit target hit | Profit target hit |
| -1 | Stop loss hit | Stop loss hit |
| 0 | Time expiry | Time expiry |
