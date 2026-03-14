---
name: ml4t-define-universe
description: Define and maintain point-in-time investment universes
category: data
type: operational
dependencies: [survivorship-bias, point-in-time]
book_chapters: [2, 3]
---

# Define Universe

Precise, point-in-time universe specification prevents survivorship bias.

## Core Rules

```python
# WRONG: Current constituents for historical backtest
universe = get_current_sp500()  # 2024 list for 2015 backtest

# CORRECT: Point-in-time constituents
universe = get_historical_constituents('SP500', as_of='2015-01-01')
```

## Universe Types

| Type | Definition | Example |
|------|------------|---------|
| Static | Fixed list | ["SPY", "QQQ", "IWM"] |
| Index-based | Track membership | S&P 500 constituents |
| Rules-based | Dynamic filters | Volume > $50M, Price > $5 |
| Sector | Industry groups | GICS Technology |

## Filter Specification

```python
universe_config = {
    "base": "US_EQUITIES",
    "filters": {
        "min_price": 5.0,
        "min_volume_usd": 50_000_000,  # 90-day average
        "min_history_days": 252,
        "exclude_adr": True,
        "exclude_otc": True
    },
    "rebalance": "quarterly",
    "buffer": 0.05  # Hysteresis to reduce turnover
}
```

## Delistings

```python
# Track delisting events
delisting_returns = {
    'bankruptcy': -1.0,      # Total loss
    'acquisition': 0.0,      # Use actual premium
    'going_private': 0.0,    # Use tender price
}

# Apply on last trading day
if symbol in delisted_on(date):
    return delisting_returns[reason]
```

## Guardrails

- Free data sources usually have survivorship bias
- CRSP is gold standard for US equities (includes delistings)
- Buffer filters to prevent excess rebalancing
- Log all universe changes with dates

## Checklist

- [ ] Universe documented precisely
- [ ] Point-in-time constituents used
- [ ] Delistings handled with returns
- [ ] Rebalance schedule specified
- [ ] Data source survivorship-free
