---
name: ml4t-point-in-time
description: "Ensure data reflects what was known at each decision point, not revised or restated values. Use when joining fundamental, macro, or alternative data to price series."
when_to_use: "Use when joining fundamental, macro, or alternative data to price series for signal construction"
dependencies: [lookahead-bias]
metadata:
  book_chapters: "2, 4"
  library: "ml4t-data"
---
# Point-in-Time Correctness

Joining data by event date instead of availability date uses information that did not exist yet, inflating backtest returns by 1-3% annually on fundamental strategies.

## The Problem

Fundamental data has two timestamps: when the economic event occurred (quarter-end) and when the data became publicly available (SEC filing date, press release, data vendor publication). Using the event date treats revised, delayed, or embargoed data as if it were available in real time.

Example: Apple's Q4 2024 revenue (period ending Dec 31) is filed with the SEC on Jan 31, 2025. A model that joins revenue on Dec 31 uses data 31 days before it existed.

Macro data has the same problem: GDP is released ~30 days after quarter-end and revised two to three times over the following months.

## The Pattern

### WRONG

```python
import polars as pl

# Join fundamentals on the quarter they describe
prices = pl.read_parquet("prices.parquet")
fundamentals = pl.read_parquet("fundamentals.parquet")

df = prices.join(
    fundamentals,
    left_on=["symbol", "timestamp"],
    right_on=["symbol", "quarter_end"],    # uses event date
    how="left",
)
```

### CORRECT

```python
import polars as pl

prices = pl.read_parquet("prices.parquet")
fundamentals = pl.read_parquet("fundamentals.parquet")

# Join on filing date (when the data became publicly available)
df = prices.join_asof(
    fundamentals.sort("filing_date"),
    left_on="timestamp",
    right_on="filing_date",              # uses availability date
    by="symbol",
    strategy="backward",                 # only use data available by this date
)
```

## Key Date Types

| Date field | What it means | Safe to join on? |
|------------|---------------|-----------------|
| `quarter_end` / `period_end` | When the economic event occurred | No |
| `filing_date` / `published_at` | When the data became public | Yes |
| `release_date` (macro) | When the statistical agency published it | Yes |
| `revised_date` | When a correction was issued | Only for the revision |

## Macro Data: Release Calendars

```python
# GDP example: align by release date, not observation quarter
gdp_releases = pl.DataFrame({
    "observation_quarter": ["2024-Q3", "2024-Q3", "2024-Q3"],
    "release_date": ["2024-10-30", "2024-11-27", "2024-12-19"],
    "release_type": ["advance", "second", "third"],
    "value": [4.9, 5.2, 4.9],
})
# A point-in-time feature on Nov 1, 2024 should use 4.9 (advance), not 5.2
```

## Guardrails

- Every fundamental join must use a `filing_date` or `release_date` column, never `quarter_end` or `period_end`.
- For SEC data, use `accepted_at` (filing acceptance timestamp), not the cover-page period date. Vendor "current" snapshots are NOT point-in-time safe.
- FRED data: check the release calendar (`FRED/releases`), not the observation date.
- Earnings data: available after market close on announcement day, not at open.
- Add a 1-day buffer after filing date to account for data vendor processing lag.

## Production Implementation

`ml4t-data` provides point-in-time access for specific datasets rather than a generic PIT join helper:

```python
from ml4t.data.providers.fred import FREDProvider

provider = FREDProvider()
unrate = provider.fetch_ohlcv(
    "UNRATE",
    "2024-01-01",
    "2024-03-31",
    vintage_date="2024-03-15",
)
# Multi-dataset PIT joins still belong in your research code
```

## Checklist

- [ ] All fundamental joins use `filing_date` / `release_date`, not period-end
- [ ] Macro features aligned by publication date with release calendar
- [ ] 1-day buffer added for data processing lag
- [ ] No "as-reported" vs "revised" confusion in the feature pipeline
- [ ] `join_asof` with `strategy="backward"` used for temporal alignment
