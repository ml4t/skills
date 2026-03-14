---
name: ml4t-fetch-data
description: Load ML4T datasets using canonical loaders
category: data
type: operational
dependencies: []
book_chapters: [3, 4, 5]
quantlab_module: ml4t_code.loaders
---

# Fetch Data

Load ML4T datasets via standardized loaders. All return Polars DataFrames.

## API

```python
from ml4t_code.loaders import (
    load_etf_universe,      # 50 ETFs daily OHLCV
    load_crypto_premium,    # Binance perpetual premium index
    load_crypto_ohlcv,      # Crypto OHLCV
    load_macro,             # FRED macro indicators
    load_ff_factors,        # Fama-French factors
    load_aqr_factors,       # AQR factors (QMJ, BAB, etc.)
    load_wiki_prices,       # 3000+ US equities 2007-2018
    load_futures_continuous,# Rolled futures contracts
    load_futures_individual # Individual futures contracts
)
```

## Usage

```python
# ETF momentum case study
etfs = load_etf_universe()
# cols: date, symbol, open, high, low, close, volume, adj_close

# Crypto funding rate case study
premium = load_crypto_premium(frequency="1h")
# cols: timestamp, symbol, premium_index_open/high/low/close

# Factor data
ff5 = load_ff_factors("ff5")           # 5-factor monthly
aqr_qmj = load_aqr_factors("qmj")      # Quality Minus Junk
aqr_bab = load_aqr_factors("bab", frequency="daily")

# Futures
futures = load_futures_continuous(
    products=["ES", "CL", "GC"],
    positions=["0"]  # Front month only
)
```

## Data Sources

| Loader | Source | Coverage |
|--------|--------|----------|
| `load_etf_universe` | Yahoo Finance | 50 ETFs, 2005+ |
| `load_crypto_premium` | Binance | 20 perps, 2019+ |
| `load_wiki_prices` | Quandl | 3000+ stocks, 2007-2018 |
| `load_ff_factors` | Ken French | 1926+ monthly |
| `load_aqr_factors` | AQR | Various |
| `load_macro` | FRED | Treasury yields, GDP, etc. |

## Guardrails

- Wiki prices end 2018 (dataset discontinued)
- Check `require_data()` messages for missing files
- Use `adj_close` for returns, not `close`
