---
name: ml4t-feature-store
description: Organize computed features in versioned parquet files with schema enforcement and point-in-time retrieval. Use when features are shared across models or need reproducible reconstruction.
dependencies: []
metadata:
  book_chapters: "8"
  library: "ml4t-engineer"
---

# Feature Store

Scattered CSV files with undocumented columns create silent schema drift — yesterday's `momentum` column used a 60-day window, today's uses 20 days, and nothing recorded the change. A structured feature store prevents this.

## The Problem

Without versioned storage, feature definitions drift silently. A researcher recomputes features with different parameters, overwrites the file, and downstream models train on inconsistent data. Point-in-time correctness is also lost: loading features "as of January 2024" returns data that was computed using information from March 2024.

## The Pattern

### WRONG
```python
import polars as pl

# Unversioned, unstructured, no metadata — silent drift guaranteed
features.write_csv("features.csv")  # What version? What parameters? When computed?
# Later: someone overwrites with different parameters
features_v2.write_csv("features.csv")  # Old version gone forever
```

### CORRECT
```python
import polars as pl
import json
from pathlib import Path
from datetime import datetime

def save_features(
    df: pl.DataFrame, name: str, version: str,
    store_path: Path, params: dict,
) -> Path:
    """Save features with version and metadata."""
    dest = store_path / name / f"v{version}"
    dest.mkdir(parents=True, exist_ok=True)

    df.write_parquet(dest / "data.parquet")
    metadata = {
        "name": name, "version": version,
        "params": params, "columns": df.columns,
        "rows": len(df), "computed_at": datetime.now().isoformat(),
    }
    (dest / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return dest

def load_features(
    name: str, version: str, store_path: Path, as_of: str | None = None,
) -> pl.DataFrame:
    """Load features, optionally point-in-time filtered."""
    df = pl.read_parquet(store_path / name / f"v{version}" / "data.parquet")
    if as_of:
        df = df.filter(pl.col("timestamp") <= as_of)
    return df
```

## Directory Layout

```
feature_store/
├── momentum_63d/
│   ├── v1.0/
│   │   ├── data.parquet
│   │   └── metadata.json    # params, computed_at, row count
│   └── v1.1/
│       ├── data.parquet
│       └── metadata.json
├── realized_vol_21d/
│   └── v1.0/
│       ├── data.parquet
│       └── metadata.json
└── registry.json             # Index of all features and versions
```

## Schema Enforcement

```python
REQUIRED_COLUMNS = {"timestamp", "symbol"}

def validate_schema(df: pl.DataFrame, name: str) -> None:
    """Enforce minimum schema before saving."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Feature '{name}' missing required columns: {missing}")
    if df.select("timestamp").null_count().item() > 0:
        raise ValueError(f"Feature '{name}' has null timestamps")
```

## Point-in-Time Correctness

The `as_of` filter ensures you only see features that were available at a given date. This prevents lookahead: a feature recomputed in March 2024 with a bug fix must not appear when loading "as of January 2024."

## Guardrails

- **Never overwrite** — create a new version, never modify an existing one
- **Metadata is mandatory** — every version records parameters, computation date, and row count
- **Schema enforcement** — every feature DataFrame must have `timestamp` and `symbol` columns
- **Point-in-time retrieval** — `as_of` filtering must be available for any downstream consumer

## Production Implementation

`ml4t-engineer` provides catalog-driven computation plus an offline feature store:

```python
from ml4t.engineer import compute_features, feature_catalog
from ml4t.engineer.store import OfflineFeatureStore

# Browse available features
print(feature_catalog.list(category="momentum"))

# Compute, persist, and join point-in-time safely
features = compute_features(prices, ["momentum_63d", "realized_vol_21d"])
with OfflineFeatureStore("features.duckdb") as store:
    store.save_features(features, "daily_features", mode="replace")
    train_set = store.point_in_time_join(labels, "daily_features", join_keys=["symbol"])
```

## Checklist

- [ ] Every feature file has a version directory and metadata.json
- [ ] Schema validated before write (required columns present, no null timestamps)
- [ ] Old versions never overwritten — only new versions created
- [ ] Point-in-time retrieval works correctly with `as_of` parameter
- [ ] Feature registry (index) lists all available features and their current versions
