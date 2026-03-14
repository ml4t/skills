---
name: ml4t-feature-store
description: Version and serve features consistently
category: features
type: operational
dependencies: [data-export]
book_chapters: [7, 26]
---

# Feature Store

Centralized storage for versioned, point-in-time correct features.

## Core Concepts

| Term | Definition |
|------|------------|
| Feature | Named, versioned calculation |
| Entity | What feature describes (symbol, date) |
| Point-in-time | Value as of specific timestamp |
| Materialization | Pre-computed storage |

## Schema

```python
# Standard feature table format
schema = {
    'timestamp': pl.Datetime,    # When feature was known
    'entity_id': pl.Utf8,        # e.g., symbol
    'feature_name': pl.Utf8,     # Feature identifier
    'value': pl.Float64,         # Feature value
    'version': pl.Utf8           # Feature definition version
}
```

## Simple Implementation

```python
class FeatureStore:
    def __init__(self, path: str):
        self.path = Path(path)

    def write(self, name: str, df: pl.DataFrame, version: str):
        """Store feature with version."""
        path = self.path / name / f"v{version}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(path)

    def read(self, name: str, version: str = 'latest',
             as_of: str = None) -> pl.DataFrame:
        """Read feature, optionally point-in-time."""
        df = pl.read_parquet(self.path / name / f"v{version}.parquet")
        if as_of:
            df = df.filter(pl.col('timestamp') <= as_of)
        return df
```

## Feature Registry

```python
FEATURE_REGISTRY = {
    'momentum_12m': {
        'version': '1.0',
        'formula': 'close.pct_change(252)',
        'frequency': 'daily',
        'dependencies': ['close'],
        'author': 'team@example.com'
    },
    'volatility_20d': {
        'version': '2.1',
        'formula': 'returns.rolling(20).std() * sqrt(252)',
        'frequency': 'daily',
        'dependencies': ['returns']
    }
}
```

## Guardrails

- Always version feature definitions
- Store computation timestamp, not just data date
- Point-in-time retrieval prevents lookahead
- Document feature formulas

## Checklist

- [ ] Features versioned
- [ ] Point-in-time retrieval supported
- [ ] Feature formulas documented
- [ ] Dependencies tracked
