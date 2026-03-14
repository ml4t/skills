---
name: ml4t-fetch-data
description: Reliable data acquisition with schema validation. Use when downloading or loading financial data from any provider.
dependencies: []
metadata:
  book_chapters: "2, 3"
  library: "ml4t-data"
---

# Fetch Data

Blindly loading data without validation produces silent schema drift, missing rows, and type errors that surface deep in modeling code.

## The Problem

Financial data providers change schemas, go offline, or return partial results without warning. Loading a CSV and trusting the columns exist, have the right types, and cover the expected date range is the single most common cause of broken pipelines. The failure mode is silent: your model trains on garbage and you only discover it when results make no sense.

## The Pattern

### WRONG
```python
import pandas as pd

# Blind load — no schema check, no gap detection, no type enforcement
df = pd.read_csv("etf_prices.csv")
returns = df["close"].pct_change()  # Might be string column
```

### CORRECT
```python
import polars as pl

EXPECTED_SCHEMA = {
    "timestamp": pl.Date,
    "symbol": pl.Utf8,
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "volume": pl.UInt64,
}

def load_and_validate(path: str) -> pl.DataFrame:
    """Load data with schema enforcement and basic integrity checks."""
    df = pl.read_parquet(path)

    # Schema check
    for col, dtype in EXPECTED_SCHEMA.items():
        assert col in df.columns, f"Missing column: {col}"
        assert df[col].dtype == dtype, f"{col}: expected {dtype}, got {df[col].dtype}"

    # Gap detection per symbol
    gaps = (
        df.sort("symbol", "timestamp")
        .with_columns(pl.col("timestamp").diff().over("symbol").alias("gap"))
        .filter(pl.col("gap") > pl.duration(days=5))
    )
    if len(gaps) > 0:
        print(f"WARNING: {len(gaps)} gaps > 5 days detected")

    return df

prices = load_and_validate("data/etfs/prices.parquet")
```

## Provider Failure Handling

Always wrap provider calls with retry and timeout. Providers go down, rate-limit, or return partial data.

```python
import time
import requests

def fetch_with_retry(url: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except (requests.Timeout, requests.HTTPError) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

## Canonical Schema

All ML4T data uses two canonical columns:
- **`symbol`** — entity identifier (exception: `cme_futures` uses `product`)
- **`timestamp`** — time column for all frequencies (daily and intraday)

If your source uses `asset`, `date`, `ticker`, or `pair`, rename at load time, not downstream.

## Guardrails

- Schema mismatches after provider updates are silent killers — always assert column names and types
- Gaps > 5 trading days indicate missing data, not holidays
- Never trust `close` without checking if adjustment is applied — use `adj_close` for returns
- Stale data (unchanged prices for 5+ days) signals a broken feed, not a flat market

## Production Implementation

`ml4t-data` provides validated loading with automatic schema enforcement:

```python
from ml4t.data import DataManager

dm = DataManager()
etfs = dm.load("etfs")  # Schema-validated, gap-checked, typed
futures = dm.load("cme_futures", products=["ES", "CL", "GC"])
```

## Checklist

- [ ] Schema validated on load (column names and types)
- [ ] Date range covers expected period
- [ ] Gaps detected and logged
- [ ] Provider errors handled with retry
- [ ] Canonical column names used (`symbol`, `timestamp`)
- [ ] Adjustment status known (`close` vs `adj_close`)
