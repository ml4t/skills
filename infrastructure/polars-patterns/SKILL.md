---
name: ml4t-polars-patterns
description: "Polars-first data processing patterns for financial data. Use when writing efficient grouped, windowed, or lazy-evaluated data transformations."
when_to_use: "Use when working with market data, computing per-symbol features, or processing datasets too large for pandas"
dependencies: []
metadata:
  book_chapters: "2, 3"
  library: ""
paths: ["**/*schema*.py", "**/*registry*.py", "**/*pipeline*.py", "**/*polars*.py", "**/*case_study*.py"]
---
# Polars Patterns for Quant Finance

Pandas groupby-apply with Python functions is 10-100x slower than Polars lazy expressions with `.over()`. For financial data - where most operations are per-symbol rolling computations - the performance gap determines whether your pipeline takes minutes or hours.

## The Problem

A typical quant workflow: load 500 symbols of daily data (2M rows), compute 20-day rolling features per symbol, cross-sectional rank, then join with labels. In pandas with `groupby().apply()`, this takes 45 seconds and 8 GB of RAM. The same logic in Polars lazy mode takes 2 seconds and 800 MB. The difference is not optimization - it is a fundamentally different execution model.

## The Pattern

### WRONG
```python
import pandas as pd

# Pandas: iterative groupby-apply - Python loop per group
df = pd.read_parquet("prices.parquet")

# Slow: Python function called once per symbol
def compute_features(group):
    group["momentum"] = group["close"].pct_change(20)
    group["volatility"] = group["close"].pct_change().rolling(20).std()
    group["rank"] = group["momentum"].rank(pct=True)
    return group

df = df.groupby("symbol").apply(compute_features)  # Python loop: 500 iterations
```

### CORRECT
```python
import polars as pl

# Polars: vectorized expressions with .over() - no Python loops
df = (
    pl.scan_parquet("prices.parquet")
    .with_columns(
        momentum=pl.col("close").pct_change(20).over("symbol"),
        volatility=pl.col("close").pct_change().rolling_std(20).over("symbol"),
    )
    .with_columns(
        rank=pl.col("momentum").rank().over("timestamp"),  # cross-sectional
    )
    .collect()
)
# Same result, 10-50x faster, fraction of memory
```

## Key Pattern: `.over()` for Per-Symbol Operations

`.over("symbol")` is the Polars equivalent of `groupby("symbol").transform()`, but it runs as a vectorized expression - no Python callback, no per-group overhead.

```python
df.with_columns(
    # Time-series operations per symbol
    ret_1d=pl.col("close").pct_change().over("symbol"),
    sma_20=pl.col("close").rolling_mean(20).over("symbol"),
    zscore=(
        (pl.col("close") - pl.col("close").rolling_mean(60).over("symbol"))
        / pl.col("close").rolling_std(60).over("symbol")
    ),
    # Cross-sectional operations per timestamp
    cs_rank=pl.col("close").pct_change().rank().over("timestamp"),
)
```

## Lazy Evaluation for Large Data

```python
# Lazy: build query plan, execute once - Polars optimizes the plan
result = (
    pl.scan_parquet("data/*.parquet")          # lazy: reads nothing yet
    .filter(pl.col("timestamp") >= "2020-01-01")  # pushed down to parquet
    .with_columns(ret=pl.col("close").pct_change().over("symbol"))
    .filter(pl.col("symbol").is_in(universe))     # pushed down
    .collect()                                     # executes optimized plan
)
```

Benefits: predicate pushdown reads only needed row groups from parquet, projection pushdown reads only needed columns, parallelism across cores automatically.

## Temporal Joins (As-Of Join)

Joining features to labels by exact timestamp misses rows. `join_asof` finds the nearest preceding match:

```python
# Join features (computed at varying times) to labels (fixed schedule)
labels_with_features = labels.join_asof(
    features.sort("timestamp"),
    on="timestamp",
    by="symbol",
    strategy="backward",  # most recent feature <= label timestamp
)
```

## Guardrails

- Always use `pl.scan_parquet()` (lazy) over `pl.read_parquet()` (eager) for files larger than 100 MB
- Never use `.map_elements()` (Python UDF) when a native expression exists - 10-100x penalty
- Single `.with_columns()` call for parallel computations - do not chain separate calls
- Convert to pandas only at visualization boundaries (`df.to_pandas()` for matplotlib/seaborn)
- Sort before `.rolling_*()` and `.over()` - Polars does not implicitly sort

## Checklist

- [ ] Using `pl.scan_parquet()` for files > 100 MB (lazy evaluation)
- [ ] Per-symbol operations use `.over("symbol")`, not groupby-apply
- [ ] Cross-sectional operations use `.over("timestamp")`
- [ ] All rolling features in a single `.with_columns()` call
- [ ] No `.map_elements()` where native expressions exist
- [ ] Pandas conversion only at visualization boundary
