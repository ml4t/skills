---
name: ml4t-continuous-futures
description: Build roll-adjusted continuous futures series
category: data
type: operational
dependencies: [fetch-data]
book_chapters: [3]
quantlab_module: ml4t_code.loaders
---

# Continuous Futures

Stitch individual contracts into tradeable time series.

## API

```python
from ml4t_code.loaders import load_futures_continuous

# Load front month for major products
futures = load_futures_continuous(
    products=["ES", "CL", "GC"],
    positions=["0"]  # Front month only
)

# Columns: ts_event, open, high, low, close, volume,
#          product, position, underlying, adj_close
```

## Roll Methods

| Method | Formula | Use Case |
|--------|---------|----------|
| Panama | Shift by gap at roll | Price levels preserved |
| Ratio | Multiply by ratio | Returns preserved |
| Calendar | Fixed date | Simple |
| Open Interest | Max OI switch | Activity-based |

## Panama Adjustment

```python
# At roll date, calculate gap
gap = new_contract_price - old_contract_price

# Adjust all historical prices
adj_close = close + cumulative_gap
# Returns on adj_close match tradeable returns
```

## Roll Schedule

```python
roll_config = {
    'ES': {'roll_days': -5, 'expiry': 'third_friday'},  # 5 days before
    'CL': {'roll_days': -3, 'expiry': 'third_bday'},
    'GC': {'roll_days': -2, 'expiry': 'third_bday'}
}

# Roll when front month OI < back month OI is also common
```

## Term Structure

```python
# Load multiple positions for carry signals
futures = load_futures_continuous(
    products=["ES"],
    positions=["0", "1", "2"]  # Front, second, third
)

# Calculate carry (term structure slope)
front = futures.filter(pl.col("position") == "0")
back = futures.filter(pl.col("position") == "1")
carry = (front['adj_close'] - back['adj_close']) / front['adj_close']
```

## Guardrails

- Use adj_close for returns, close for current price
- Roll dates affect backtest execution assumptions
- Carry signals require accurate term structure
- Different markets have different roll conventions

## Checklist

- [ ] Roll method documented
- [ ] Panama adjustment applied for returns
- [ ] Term structure positions available
- [ ] Roll dates verified against exchange calendars
