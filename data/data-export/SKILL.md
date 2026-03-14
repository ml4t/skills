---
name: ml4t-data-export
description: Export financial data in efficient columnar formats with schema enforcement. Use when persisting datasets for analytics, sharing data across pipeline stages, or optimizing read performance.
dependencies: [fetch-data]
metadata:
  book_chapters: "2"
  library: "ml4t-data"
---

# Data Export

Saving financial data as CSV loses type information, bloats file size 5-10x, and makes every downstream read parse strings back into numbers — a tax paid on every pipeline run.

## The Problem

CSV is human-readable but machine-hostile: no type information (dates become strings, integers become floats), no compression (a 100MB Parquet file becomes 500MB CSV), no predicate pushdown (you must read the entire file to filter one column), and no schema enforcement (a renamed column breaks silently). For financial data pipelines where the same dataset is read hundreds of times by different notebooks, the cumulative cost of CSV is enormous in both time and correctness.

## The Pattern

### WRONG
```python
import pandas as pd

# CSV: no types, no compression, slow reads, 5x file size
df.to_csv("prices.csv", index=False)

# Every consumer must re-parse types
df = pd.read_csv("prices.csv", parse_dates=["date"])  # Hope the format matches
df["volume"] = df["volume"].astype(int)  # Was saved as float because of NaN
```

### CORRECT
```python
import polars as pl

# Enforce schema before writing
SCHEMA = {
    "timestamp": pl.Date,
    "symbol": pl.Utf8,
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "volume": pl.UInt64,
}

df = df.cast(SCHEMA)
df.write_parquet(
    "data/prices.parquet",
    compression="zstd",       # 3-5x smaller than uncompressed
    statistics=True,           # Enables predicate pushdown on read
    row_group_size=100_000,    # Balance between granularity and overhead
)

# Reader gets exact types, filters pushed down to storage layer
df = (
    pl.scan_parquet("data/prices.parquet")
    .filter(pl.col("timestamp") >= pl.lit("2020-01-01").str.to_date())
    .filter(pl.col("symbol") == "SPY")
    .collect()
)
# Only reads the row groups and columns needed — 10-100x faster than CSV
```

## Partitioning Large Datasets

For datasets spanning many years or thousands of symbols, partition by date to enable efficient range scans.

```python
import polars as pl

# Write partitioned dataset
df = df.with_columns(
    year=pl.col("timestamp").dt.year(),
)
for (year,), group in df.group_by("year"):
    path = f"data/prices/year={year}/data.parquet"
    group.drop("year").write_parquet(path, compression="zstd")

# Read specific partition (only touches one file)
df_2024 = pl.read_parquet("data/prices/year=2024/data.parquet")

# Or scan all with automatic partition filtering
df = pl.scan_parquet("data/prices/**/data.parquet", hive_partitioning=True).filter(
    pl.col("year") >= 2020
).collect()
```

## Schema Versioning

When schema evolves, write a sidecar `.schema.json` alongside the Parquet file containing the version number, column names/types, and row count. Readers assert the expected version before loading — a version mismatch raises immediately instead of failing silently downstream.

## Guardrails

- Never use CSV for production data pipelines — Parquet is strictly superior for typed columnar data
- Always enable `statistics=True` — it costs nothing on write and enables predicate pushdown on read
- `zstd` compression gives the best size/speed tradeoff; `snappy` is faster but larger
- Partition only when datasets exceed ~1GB or when you frequently filter by the partition key
- Schema changes must be explicit — a silently added column breaks downstream notebooks that assert schema

## Production Implementation

`ml4t-data` handles schema-enforced Parquet storage automatically:

```python
from ml4t.data import DataManager

dm = DataManager()
# All datasets stored as typed Parquet with canonical schema
etfs = dm.load("etfs")  # Enforced types, zstd compression, predicate pushdown
```

## Checklist

- [ ] Parquet format used for all persisted data
- [ ] Schema enforced via `cast()` before writing
- [ ] Compression enabled (`zstd` default)
- [ ] Statistics enabled for predicate pushdown
- [ ] Large datasets partitioned by date or symbol
- [ ] Schema version tracked for evolving datasets
