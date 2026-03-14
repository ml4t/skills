---
name: ml4t-canonical-schema
description: Standardized data schema across all financial datasets. Use when loading, transforming, or storing market data to ensure consistent column names and types.
dependencies: [fetch-data, validate-data]
metadata:
  book_chapters: "2, 3"
  library: "ml4t-data"
---

# Canonical Schema

When every dataset uses different column names — `date` vs `ts_event` vs `timestamp`, `asset` vs `ticker` vs `symbol` — every downstream notebook needs special-case handling. One canonical schema eliminates this class of bugs entirely.

## The Problem

Provider A delivers data with columns `date`, `ticker`, `close`. Provider B uses `ts_event`, `symbol`, `price`. Provider C uses `timestamp`, `asset`, `adj_close`. Every notebook that consumes data must know which provider it came from and map columns accordingly. Someone forgets, and a `ColumnNotFoundError` surfaces deep in a modeling pipeline. This is not a data problem — it is a naming problem, and it is entirely preventable.

## The Pattern

### WRONG
```python
import polars as pl

# Different column names per dataset — downstream code breaks constantly
etfs = pl.read_parquet("etfs.parquet")        # has: date, ticker, close
futures = pl.read_parquet("futures.parquet")   # has: ts_event, product, settle
crypto = pl.read_parquet("crypto.parquet")     # has: timestamp, symbol, close

# Every notebook needs provider-specific column mapping
if "date" in df.columns:
    df = df.rename({"date": "timestamp"})
elif "ts_event" in df.columns:
    df = df.rename({"ts_event": "timestamp"})
# Repeat for every column, every dataset, every notebook
```

### CORRECT
```python
import polars as pl

# Canonical schema: enforced once at load time, trusted everywhere after
CANONICAL_COLUMNS = {
    "time": "timestamp",    # ALL frequencies: daily, hourly, minute
    "entity": "symbol",     # Exception: cme_futures uses "product"
}

def enforce_schema(df: pl.DataFrame, dataset: str) -> pl.DataFrame:
    """Rename provider columns to canonical names at load time."""
    renames = {}
    # Time column: accept common variants, output "timestamp"
    for variant in ["date", "ts_event", "datetime", "time"]:
        if variant in df.columns:
            renames[variant] = "timestamp"
    # Entity column: accept common variants, output "symbol"
    if dataset != "cme_futures":  # futures use "product"
        for variant in ["asset", "ticker", "pair", "instrument"]:
            if variant in df.columns:
                renames[variant] = "symbol"
    return df.rename(renames)

# Load once, use everywhere — no downstream renames needed
etfs = enforce_schema(pl.read_parquet("etfs.parquet"), "etfs")
assert "timestamp" in etfs.columns
assert "symbol" in etfs.columns
```

## The Two Canonical Columns

| Column | Name | Type | Usage |
|--------|------|------|-------|
| Time | `timestamp` | `Date` or `Datetime` | Every dataset, every frequency |
| Entity | `symbol` | `Utf8` | All datasets except CME futures |
| Entity (futures) | `product` | `Utf8` | CME futures only (contract identifier) |

Why `timestamp` for daily data? Because the same code works for daily, hourly, and minute data without branching. A `Date` is a valid timestamp.

Why `product` for futures? Because a futures "symbol" is ambiguous (ES vs ESH24 vs the continuous contract). `product` identifies the commodity, which is what you group by.

## OHLCV Columns

Lowercase, no prefix: `open`, `high`, `low`, `close`, `volume`. If adjustments exist: `adj_close`. Never `Close`, `CLOSE`, `Adj Close`, or `adjclose`.

## Enforcement Point

Schema enforcement happens at load time, not downstream. This means:

1. Data loaders validate and rename on return
2. Notebooks never import raw provider data directly
3. If a notebook gets a `ColumnNotFoundError` for `date` or `asset`, the notebook is wrong — fix the notebook to use `timestamp` or `symbol`

## Guardrails

- Never rename canonical columns back to legacy names in notebooks — fix the notebook
- Never add compatibility shims that accept both old and new names — migrate forward
- If a new provider uses a different name, add the rename in the loader, not in 50 notebooks
- `product` is only for CME futures — do not generalize to other datasets
- Check for legacy names (`asset`, `date`, `ticker`, `pair`) during code review

## Production Implementation

`ml4t-data` standardizes generic OHLCV fetches to canonical columns:

```python
from ml4t.data import DataManager

dm = DataManager()
panel = dm.batch_load(
    ["SPY", "QQQ"],
    start="2015-01-01",
    end="2024-12-31",
    provider="yahoo",
)
# Columns: timestamp, symbol, open, high, low, close, volume
```

## Checklist

- [ ] All data loaded through loaders that enforce canonical names
- [ ] Time column is `timestamp` for every dataset and frequency
- [ ] Entity column is `symbol` (or `product` for CME futures only)
- [ ] OHLCV columns are lowercase: `open`, `high`, `low`, `close`, `volume`
- [ ] No legacy column names (`date`, `asset`, `ticker`, `pair`) in notebook code
- [ ] Schema enforcement is at load time, not scattered across notebooks
