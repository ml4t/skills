# Audit Report: `ml4t-data` Usage in `~/ml4t/skills`

Date: 2026-03-14

Scope:

- `/home/stefan/ml4t/skills`
- All `SKILL.md` files and repo guidance files that reference `ml4t-data`
- Current `ml4t-data` source in `/home/stefan/ml4t/libraries/ml4t-data`

Method:

- Static API audit against current library source
- No skill snippets were executed
- Library source was treated as ground truth over skill prose

## Executive Summary

The main `ml4t-data` drift pattern in the skills repo was repeated misuse of
`DataManager.load(...)` as if it were a dataset registry API. In the current
library, `DataManager.load(...)` is a storage-backed ingest operation, not a
shortcut like `load("etfs")`, `load("us_equities")`, or
`load(datasets=[...], as_of_date=...)`.

There were also two broader overclaims:

- the skills implied `ml4t-data` currently ships a generic survivorship-free
  `us_equities` dataset loader
- the skills implied `ml4t-data` currently provides a generic point-in-time
  multi-dataset join helper through `DataManager`

Those APIs do not exist in the current library.

I updated the stale skill snippets and the repo guidance so the examples now
use current, narrower library capabilities:

- `DataManager.fetch(...)`, `batch_load(...)`, and `batch_load_universe(...)`
- storage-backed `DataManager.load(...)`
- `WikiPricesProvider` for survivorship-bias-free US equities history through 2018
- `FREDProvider.fetch_ohlcv(..., vintage_date=...)` for point-in-time macro access

## Findings

### 1. High: several skills used `DataManager.load(...)` as a nonexistent dataset loader

These files were stale:

- `infrastructure/canonical-schema/SKILL.md`
- `data/validate-data/SKILL.md`
- `data/data-export/SKILL.md`
- `data/define-universe/SKILL.md`
- `concepts/survivorship-bias/SKILL.md`
- `concepts/point-in-time/SKILL.md`

Typical wrong patterns:

- `dm.load("etfs")`
- `dm.load("cme_futures")`
- `dm.load("us_equities")`
- `dm.load(datasets=["prices", "fundamentals"], as_of_date="filing_date", ...)`
- `dm.load("etfs", validate=True)`

Current ground truth:

- `DataManager.fetch(...)` for single-symbol retrieval
- `DataManager.batch_load(...)` for multi-symbol retrieval
- `DataManager.batch_load_universe(...)` for maintained static universes
- `DataManager.load(...)` only when a storage backend is configured and you want
  provider-to-storage ingest

Source:

- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/data_manager.py`

### 2. High: the survivorship-bias skill claimed a generic `us_equities` panel that the library does not ship

The old snippet implied:

- `equities = dm.load("us_equities")`

That API does not exist.

What the current library actually provides:

- `WikiPricesProvider` as a survivorship-bias-free US equities archive through
  2018-03-27

Source:

- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/providers/wiki_prices.py`

Update made:

- rewrote the Production Implementation to use
  `ml4t.data.providers.wiki_prices.WikiPricesProvider`
- kept the skill’s conceptual requirement that PIT constituents and delisting
  handling remain explicit in research code

### 3. High: the point-in-time skill claimed a generic PIT join API that the library does not have

The old snippet implied:

- `dm.load(datasets=["prices", "fundamentals"], as_of_date="filing_date", ...)`

That API does not exist.

What the current library actually provides:

- point-in-time access for specific providers, notably
  `FREDProvider.fetch_ohlcv(..., vintage_date=...)`
- some explicit workflow helpers such as the COT join workflow, but not a
  generic multi-dataset PIT orchestration layer on `DataManager`

Sources:

- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/providers/fred.py`
- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/cot/workflow.py`

Update made:

- rewrote the Production Implementation to show current PIT access via
  `FREDProvider`
- explicitly noted that multi-dataset PIT joins still belong in research code

### 4. Medium: the canonical-schema skill overclaimed automatic schema enforcement for book-style dataset loaders

The old snippet implied:

- `dm.load("etfs")` and `dm.load("cme_futures")` both return fully canonicalized
  datasets

That was wrong for two reasons:

- the `load("...")` calls are not valid
- the book futures manager keeps Databento-native fields such as `ts_event`
  rather than a generic `timestamp` column

Current ground truth:

- generic OHLCV provider fetches and batch loads standardize to
  `[timestamp, symbol, open, high, low, close, volume]`
- specialized book managers may retain source-native schema

Sources:

- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/providers/base.py`
- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/managers/batch_manager.py`
- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/futures/book_downloader.py`

Update made:

- rewrote the Production Implementation to use `DataManager.batch_load(...)`
  with Yahoo data, which does return canonical OHLCV

### 5. Medium: the export skill described automatic Parquet handling, but showed the wrong API

The concept was directionally right, but the old code used:

- `dm.load("etfs")`

which would not export anything in the current library.

Current ground truth:

- Parquet export is exercised through a configured storage backend such as
  `HiveStorage(StorageConfig(...))`
- `DataManager.load(symbol, start, end, provider=...)` writes into storage and
  returns a storage key

Sources:

- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/storage/backend.py`
- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/storage/hive.py`
- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/data_manager.py`

Update made:

- rewrote the Production Implementation to use `HiveStorage` +
  `StorageConfig` + `DataManager.load(...)`

### 6. Medium: the define-universe skill overstated current library support

The old snippet implied:

- `dm.load("us_equities")`
- universe filters applied via `DataManager` configuration

That is too broad for current `ml4t-data`.

Current ground truth:

- `Universe.get(...)` and `DataManager.batch_load_universe(...)` provide
  maintained static symbol universes
- point-in-time membership and liquidity filtering still need to be applied in
  research code

Source:

- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/universe.py`
- `/home/stefan/ml4t/libraries/ml4t-data/src/ml4t/data/managers/batch_manager.py`

Update made:

- rewrote the Production Implementation to use `batch_load_universe("sp500", ...)`
- explicitly noted that PIT and liquidity filters remain explicit

## Files Updated

Skill files:

- `infrastructure/canonical-schema/SKILL.md`
- `concepts/survivorship-bias/SKILL.md`
- `concepts/point-in-time/SKILL.md`
- `data/validate-data/SKILL.md`
- `data/data-export/SKILL.md`
- `data/define-universe/SKILL.md`

Repo guidance:

- `AGENTS.md`
- `README.md`
- `REVIEW_PROMPT.md`

## Files Reviewed and Left Unchanged

These `ml4t-data` references were already current enough and did not need edits:

- `data/fetch-data/SKILL.md`
- `data/continuous-futures/SKILL.md`

Why they were left alone:

- `fetch-data` already uses `DataManager.fetch(...)` and `batch_load(...)`
- `continuous-futures` already uses current exports:
  `FUTURES_REGISTRY`, `FuturesDataManager`, and `ContinuousContractBuilder`

## Recommended Ongoing Guardrails

1. Treat `data_manager.py` as the source of truth for `DataManager`.

2. Do not invent dataset loaders on `DataManager`. If an example wants:

- a generic fetch: use `fetch(...)`
- multi-symbol load: use `batch_load(...)`
- maintained static universes: use `batch_load_universe(...)`
- storage-backed ingest: use `load(...)` with a configured storage backend

3. Do not claim generic PIT joins or a built-in survivorship-free `us_equities`
   panel unless those APIs are actually added to `ml4t-data`.

4. For conceptual skills, it is better to show a narrower but real library
   capability than a broader invented convenience API.

## Bottom Line

The `ml4t-data` drift in `~/ml4t/skills` was real but localized. The repo did
not need a conceptual rewrite; it needed a cleanup of stale Production
Implementation snippets and a few repo-level guardrails.

After this pass, the `ml4t-data` examples now reflect the current library more
accurately and more narrowly:

- fetch and batch-load with `DataManager`
- storage-backed ingest with `DataManager.load(...)`
- survivorship-free historical equities via `WikiPricesProvider`
- point-in-time macro access via `FREDProvider(..., vintage_date=...)`
