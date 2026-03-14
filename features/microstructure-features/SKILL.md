---
name: ml4t-microstructure-features
description: Features from order flow and market microstructure
category: features
type: operational
dependencies: [build-bars]
book_chapters: [4, 7]
---

# Microstructure Features

Extract signals from order flow and book dynamics.

## Feature Types

| Feature | Data Required | Signal |
|---------|---------------|--------|
| Spread | Quote | Liquidity cost |
| OFI | Trades | Order flow imbalance |
| VWAP deviation | Minute bars | Institutional activity |
| Book depth | L2 quotes | Support/resistance |
| Kyle's Lambda | Trades + quotes | Price impact |

## Order Flow Imbalance (OFI)

```python
def compute_ofi(trades: pl.DataFrame) -> pl.DataFrame:
    """Signed trade flow."""
    # Classify trades by tick rule
    trades = trades.with_columns([
        pl.when(pl.col('price') > pl.col('price').shift(1))
        .then(pl.col('size'))
        .when(pl.col('price') < pl.col('price').shift(1))
        .then(-pl.col('size'))
        .otherwise(0)
        .alias('signed_volume')
    ])

    return trades.group_by_dynamic('timestamp', every='5m').agg([
        pl.col('signed_volume').sum().alias('ofi'),
        pl.col('size').sum().alias('total_volume')
    ])
```

## VWAP Deviation

```python
def vwap_deviation(bars: pl.DataFrame) -> pl.DataFrame:
    """Price vs VWAP as institutional signal."""
    vwap = (bars['close'] * bars['volume']).cum_sum() / bars['volume'].cum_sum()
    return (bars['close'] - vwap) / vwap
```

## Spread Features

```python
def spread_features(quotes: pl.DataFrame) -> dict:
    """Liquidity features from quotes."""
    return {
        'quoted_spread': quotes['ask'] - quotes['bid'],
        'relative_spread': (quotes['ask'] - quotes['bid']) / quotes['mid'],
        'effective_spread': 2 * abs(quotes['trade_price'] - quotes['mid']),
        'spread_volatility': quotes['relative_spread'].rolling(20).std()
    }
```

## Guardrails

- Microstructure features need tick/quote data
- Higher data requirements than daily features
- Most relevant for intraday strategies
- Latency matters for live trading

## Checklist

- [ ] Tick/quote data available
- [ ] Trade classification accurate
- [ ] Features aligned to trading horizon
- [ ] Data latency acceptable
