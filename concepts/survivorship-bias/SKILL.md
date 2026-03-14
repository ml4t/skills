---
name: ml4t-survivorship-bias
description: Account for delisted securities in historical backtests
category: concepts
type: conceptual
dependencies: []
book_chapters: [3, 5]
---

# Survivorship Bias

Only testing on securities that survived to today inflates backtest returns.

## The Problem

```python
# WRONG: Use current S&P 500 for 2010 backtest
current_sp500 = get_current_constituents('SP500')  # 2024 list
backtest_2010 = data[data['symbol'].isin(current_sp500)]
# Missing: Lehman, Bear Stearns, Enron, WorldCom...
```

## Why It Matters

- Delisted stocks often went to zero (bankruptcy, fraud)
- Survivors have positive selection bias
- Effect: 1-2% annual return inflation is common
- Value/small-cap strategies most affected

## Rules

### Universe Construction

```python
# WRONG
universe = get_current_tickers()

# CORRECT: Point-in-time constituents
universe = get_historical_constituents(index='SP500', as_of=backtest_date)
```

### Handling Delistings

```python
# Track delisting returns
delisting_returns = {
    'bankruptcy': -1.0,      # Total loss
    'acquisition': 0.0,      # Use actual premium
    'going_private': 0.0,    # Use tender price
    'exchange_change': 0.0   # Continue tracking
}

# Apply delisting return on last trading day
if is_delisted(symbol, date):
    return delisting_returns[delisting_reason]
```

### Data Sources

| Source | Survivorship-Free? |
|--------|-------------------|
| CRSP | Yes (includes delistings) |
| Quandl Wiki | Yes (2007-2018) |
| Yahoo Finance | No (current tickers only) |
| Most free APIs | No |

## Index Reconstitution

```python
# S&P 500 changes ~20-25 constituents per year
# Must track additions AND deletions

recon_events = get_index_changes('SP500', start, end)
for event in recon_events:
    if event.type == 'deletion':
        # Stock often drops on deletion announcement
        # Backtest should sell BEFORE deletion, not after
        pass
```

## Guardrails

- Free data usually has survivorship bias
- CRSP is gold standard for US equities
- Crypto: exchanges delist coins frequently
- ETFs: check for fund closures

## Checklist

- [ ] Using point-in-time index constituents
- [ ] Delisting returns included (not just dropped)
- [ ] Universe changes tracked over time
- [ ] Data source documented for survivorship treatment
