# ML4T Engineer Skills API Audit

Date: 2026-03-14
Library reviewed: `ml4t-engineer`
Skills project reviewed: `~/ml4t/skills`

## Scope

I reviewed every `~/ml4t/skills` file that references `ml4t-engineer` directly or uses its public API surface:

- `AGENTS.md`
- `REVIEW_PROMPT.md`
- `README.md`
- `concepts/data-leakage/SKILL.md`
- `concepts/lookahead-bias/SKILL.md`
- `features/compute-features/SKILL.md`
- `features/feature-families/SKILL.md`
- `features/feature-store/SKILL.md`
- `features/meta-labels/SKILL.md`
- `features/regime-features/SKILL.md`
- `features/triple-barrier/SKILL.md`
- `workflows/case-study-development/SKILL.md`

Validation basis:

- Current package exports in `~/ml4t/libraries/ml4t-engineer/src/ml4t/engineer/__init__.py`
- Current feature/labeling/store APIs in `api.py`, `labeling/__init__.py`, `dataset.py`, `discovery/catalog.py`, `store/offline.py`
- Runtime smoke checks against the installed package via `uv run python`

## Executive Summary

Most of the core API references are current:

- `compute_features`
- `feature_catalog`
- `FeatureCatalog`
- `create_dataset_builder`
- `LabelingConfig`
- `atr_triple_barrier_labels`
- `meta_labels`
- `OfflineFeatureStore`
- direct indicator imports such as `from ml4t.engineer.features.momentum import macd, rsi, adx`

The stale areas are concentrated in examples that use outdated or nonexistent feature names, plus one invalid `compute_features(..., config=...)` call pattern.

## Inventory

### Verified current

- `AGENTS.md`
- `REVIEW_PROMPT.md`
- `README.md` (generic library mention only)
- `concepts/data-leakage/SKILL.md`
- `concepts/lookahead-bias/SKILL.md`
- `features/triple-barrier/SKILL.md`
- `features/meta-labels/SKILL.md`

### Needs correction

- `features/compute-features/SKILL.md`
- `features/feature-families/SKILL.md`
- `features/feature-store/SKILL.md`
- `features/regime-features/SKILL.md`
- `workflows/case-study-development/SKILL.md`

## Findings

### 1. Invalid `compute_features(..., config=...)` usage

Severity: High

File:
- `workflows/case-study-development/SKILL.md:99`

Current text:

```python
features = compute_features(data, config="setup.yaml")
```

Issue:
- `compute_features` does not accept a `config=` keyword.
- The signature is `compute_features(data, features)`.
- The second argument can be a list of feature names, a list of feature-spec dicts, or a YAML path containing a feature spec list or a dict with a top-level `features:` key.
- A generic `setup.yaml` will not work unless it is specifically a feature config file in that format.

Recommended fix:
- Replace with either:

```python
features = compute_features(data, "config/features.yaml")
```

or

```python
features = compute_features(data, [
    {"name": "rsi", "params": {"period": 14}},
    {"name": "macd", "params": {"fast": 12, "slow": 26, "signal": 9}},
])
```

If the skill wants to keep a single `setup.yaml`, it should state that a feature block must be extracted and passed into `compute_features`, not that the whole file is accepted directly.

### 2. Nonexistent feature names in `feature-families`

Severity: High

File:
- `features/feature-families/SKILL.md:92-94`

Current text:

```python
features = compute_features(data, [
    "momentum_63d", "rsi_14", "realized_vol_21d", "roll_yield",
])
```

Issue:
- These names do not exist in the current registry.
- Runtime validation against `feature_catalog.list()` confirmed all four names are absent.
- The current library uses canonical names such as `rsi`, `mom`, `realized_volatility`, `garman_klass_volatility`, `volatility_adjusted_returns`, etc.
- `roll_yield` is not currently a registry feature in `ml4t-engineer`.

Recommended fix:
- Use actual registry names, for example:

```python
features = compute_features(data, [
    "mom", "rsi", "realized_volatility", "garman_klass_volatility",
])
```

Or, if the intent is to illustrate economic families including carry/value, keep the conceptual discussion but stop presenting the example as a direct `ml4t-engineer` registry call until those features actually exist.

### 3. `feature-families` overstates how the library organizes features

Severity: Medium

File:
- `features/feature-families/SKILL.md:82`

Issue:
- The skill says the library provides features “organized by family” in the economic sense used by the skill: momentum, mean-reversion, volatility, carry, value.
- The actual registry categories are implementation-oriented: momentum, volatility, trend, regime, microstructure, statistics, ML, price transform, volume, risk, math.
- Carry/value are not first-class registry categories in the current library.

Recommended fix:
- Either reword to “organized by registry category” or keep the economic-family explanation and explicitly say the mapping from skill families to library categories is approximate.

### 4. Nonexistent feature names in `feature-store`

Severity: High

File:
- `features/feature-store/SKILL.md:119`

Current text:

```python
features = compute_features(prices, ["momentum_63d", "realized_vol_21d"])
```

Issue:
- `momentum_63d` and `realized_vol_21d` are not current registry features.

Recommended fix:
- Replace with current names, for example:

```python
features = compute_features(prices, ["mom", "realized_volatility"])
```

or another pair drawn from `feature_catalog.list(...)`.

### 5. `feature-store` skill mixes a generic versioned-parquet concept with a different actual library API

Severity: Medium

File:
- `features/feature-store/SKILL.md` overall, especially `:1-131`
- Library API actually reviewed in `ml4t-engineer/store/offline.py`

Issue:
- The skill frames the pattern as a versioned parquet store with `metadata.json`, `registry.json`, and `as_of` loading.
- The current `ml4t-engineer` implementation is a DuckDB-backed `OfflineFeatureStore` with:
  - `save_features(df, table_name, mode=...)`
  - `load_features(table_name, columns=None, filter_expr=None, limit=None)`
  - `point_in_time_join(labels, features_table, ...)`
- There is no library-level `as_of` parameter on `load_features`, no version directory layout, and no JSON registry/metadata abstraction.

Recommended fix:
- If this is meant to be a generic architecture skill, keep the conceptual pattern but stop implying that `ml4t-engineer` implements that exact storage model.
- If it is meant to illustrate the library specifically, rewrite the skill around the actual DuckDB store API and `point_in_time_join` semantics.

### 6. `regime-features` claims catalog support for nonexistent features

Severity: High

File:
- `features/regime-features/SKILL.md:83-90`

Current text:

```python
features = compute_features(data, [
    "vix_percentile", "realized_vol_zscore", "adx_14", "yield_curve_slope",
])
```

Issue:
- None of these four names exist in the current registry.
- Runtime checks confirmed the registry instead exposes regime/volatility-adjacent features such as:
  - `adx`
  - `choppiness_index`
  - `fractal_efficiency`
  - `hurst_exponent`
  - `trend_intensity_index`
  - `realized_volatility`
  - `volatility_percentile_rank`
  - `volatility_regime_probability`
- `vix_percentile` and `yield_curve_slope` are macro features, not current `ml4t-engineer` registry features.

Recommended fix:
- Replace the example with actual registry names, e.g.:

```python
features = compute_features(data, [
    "adx", "choppiness_index", "volatility_percentile_rank", "volatility_regime_probability",
])
```

- If the skill wants to teach macro regime inputs, describe them as external features rather than as `ml4t-engineer` catalog entries.

### 7. `compute-features` skill overstates panel-awareness of `compute_features`

Severity: Medium

File:
- `features/compute-features/SKILL.md:1-91`

Issue:
- The skill is explicitly about “systematic feature computation across multiple assets with group-aware operations.”
- Its production section then points to `compute_features(...)` as if that API handles grouped panel computation automatically.
- The current implementation in `api.py` dispatches registry features directly as expressions and does not automatically add `.over("symbol")` or otherwise partition by asset.
- Library docs also distinguish standalone multi-asset/cross-asset functions from registry-driven `compute_features` calls.

Why this matters:
- As written, the skill implies that `compute_features` is the safe drop-in solution for long-format multi-asset panels. That is not guaranteed by the current API.

Recommended fix:
- Reword the production section to say:
  - use `compute_features` for single-series / per-asset OHLCV pipelines, and
  - use explicit grouped Polars logic or standalone cross-asset functions for panel features.
- If you want a library-backed panel example, show grouping outside the registry call or use functions from `ml4t.engineer.features.cross_asset` where appropriate.

## Verified-current references

These examples align with the current library and do not need API changes:

### `features/triple-barrier/SKILL.md:76-94`
- `from ml4t.engineer.config import LabelingConfig`
- `from ml4t.engineer.labeling import atr_triple_barrier_labels`
- `LabelingConfig.atr_barrier(...)`
- `atr_triple_barrier_labels(df, config=config, price_col="close", timestamp_col="timestamp")`

### `features/meta-labels/SKILL.md:91-106`
- `atr_triple_barrier_labels(...)` followed by `meta_labels(..., signal_col="signal", return_col="label_return")`
- This matches the current API and output column names.

### `concepts/data-leakage/SKILL.md:78-94`
- `create_dataset_builder(...)`
- `builder.split(cv)` with fold objects exposing `X_train`, `y_train`, `X_test`, `y_test`
- This is current.

### `concepts/lookahead-bias/SKILL.md:98-111`
- `create_dataset_builder(...)` usage is current.
- The example correctly illustrates leakage-safe scaling via the builder.

### `features/compute-features/SKILL.md:83-90`
- The bare API examples are current:
  - `from ml4t.engineer import compute_features, feature_catalog`
  - `feature_catalog.list()`
  - `compute_features(data, ["rsi", "macd", "bollinger_bands"])`
  - `compute_features(data, "config/features.yaml")`
- Only the panel-positioning around this example needs tightening.

## Recommended patch order

1. Fix `workflows/case-study-development/SKILL.md`
- This is the only outright invalid call signature.

2. Fix invalid registry feature names
- `features/feature-families/SKILL.md`
- `features/feature-store/SKILL.md`
- `features/regime-features/SKILL.md`

3. Tighten library capability descriptions
- `features/compute-features/SKILL.md`
- `features/feature-families/SKILL.md`
- `features/feature-store/SKILL.md`

## Bottom line

The public `ml4t-engineer` API references in the skills repo are mostly current. The main cleanup needed is:

- remove stale feature names,
- stop implying `compute_features` accepts arbitrary `setup.yaml` via `config=`,
- stop presenting nonexistent macro/carry/value features as registry-backed,
- clarify that `compute_features` is not a complete panel-grouping abstraction.
