---
name: ml4t-data-export
description: Store and export data in efficient formats
category: data
type: operational
dependencies: [fetch-data]
book_chapters: [3]
---

# Data Export

Efficient storage and retrieval for large financial datasets.

## Format Comparison

| Format | Read Speed | Size | Typing | Use Case |
|--------|------------|------|--------|----------|
| Parquet | Fast | Small | Strong | Default choice |
| Feather | Fastest | Medium | Strong | In-memory IPC |
| CSV | Slow | Large | Weak | Interchange |
| HDF5 | Medium | Small | Strong | Legacy |

## Parquet Best Practices

```python
import polars as pl

# Write with compression
df.write_parquet(
    'data.parquet',
    compression='zstd',
    statistics=True,  # Enable predicate pushdown
    row_group_size=100_000
)

# Read with filtering (pushed down)
df = pl.scan_parquet('data.parquet').filter(
    pl.col('date') >= '2020-01-01'
).collect()
```

## Partitioning

```python
# Partition by date for efficient range queries
df.write_parquet(
    'data/',
    partition_by=['year', 'month']
)

# Query specific partitions
df = pl.read_parquet('data/year=2024/month=12/')
```

## Schema Management

```python
# Enforce schema on write
schema = {
    'date': pl.Date,
    'symbol': pl.Utf8,
    'close': pl.Float64,
    'volume': pl.UInt64
}

df = df.cast(schema)
df.write_parquet('data.parquet')

# Validate on read
df = pl.read_parquet('data.parquet')
assert df.schema == schema
```

## Incremental Updates

```python
def append_data(path: str, new_data: pl.DataFrame):
    """Append new data without rewriting entire file."""
    existing = pl.read_parquet(path)
    max_date = existing['date'].max()

    # Only add new rows
    new_rows = new_data.filter(pl.col('date') > max_date)
    combined = pl.concat([existing, new_rows])
    combined.write_parquet(path)
```

## Guardrails

- Always use Parquet for production (fast + typed)
- Partition large datasets by date
- Validate schema after read
- Use compression (zstd is good default)

## Checklist

- [ ] Parquet format used (not CSV)
- [ ] Compression enabled
- [ ] Schema documented and enforced
- [ ] Partitioning for large datasets
- [ ] Statistics enabled for filtering
