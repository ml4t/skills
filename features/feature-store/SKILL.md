---
name: ml4t-feature-store
description: "Organize computed features in versioned storage with schema enforcement and point-in-time retrieval. Use when persisting features for reproducible ML experiments or sharing across pipelines."
when_to_use: "Use when features are shared across models or need reproducible reconstruction"
dependencies: []
metadata:
  book_chapters: "8"
  library: "ml4t-engineer"
paths: ["**/*feature*.py", "**/*label*.py", "**/*barrier*.py", "**/*store*.py", "**/*horizon*.py", "**/*meta_label*.py", "**/*microstructure*.py", "**/*regime*.py", "**/*selection*.py"]
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

Any serious feature store needs PIT-safe retrieval semantics. In a file-based
design that may be an `as_of` filter; in a database-backed design it is usually
a point-in-time join. March recomputations must never leak into January training.

## Guardrails

- **Never overwrite** — create a new version, never modify an existing one
- **Metadata is mandatory** — every version records parameters, computation date, and row count
- **Schema enforcement** — every feature DataFrame must have `timestamp` and `symbol` columns
- **Point-in-time safety** — every downstream consumer needs either `as_of` semantics or an explicit PIT join

## Production Implementation

`ml4t-engineer` implements the storage layer as a DuckDB-backed offline feature
store with explicit point-in-time joins:

```python
from ml4t.engineer import compute_features, feature_catalog
from ml4t.engineer.store import OfflineFeatureStore

# Browse available features
print(feature_catalog.list(category="momentum"))

# Compute, persist, and join point-in-time safely
features = compute_features(prices, ["mom", "realized_volatility"])
with OfflineFeatureStore("features.duckdb") as store:
    store.save_features(features, "daily_features", mode="replace")
    train_set = store.point_in_time_join(labels, "daily_features", join_keys=["symbol"])
```

## Checklist

- [ ] Every feature file has a version directory and metadata.json
- [ ] Schema validated before write (required columns present, no null timestamps)
- [ ] Old versions never overwritten — only new versions created
- [ ] Point-in-time retrieval or join works correctly for downstream training
- [ ] Feature registry (index) lists all available features and their current versions
