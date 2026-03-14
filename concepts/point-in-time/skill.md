---
name: ml4t-point-in-time
description: Use data as it was available, not as revised later
category: concepts
type: conceptual
dependencies: [lookahead-bias]
book_chapters: [3, 5]
---

# Point-in-Time Correctness

Use data as it was available at decision time, not revised values.

## Key Concepts

| Term | Definition |
|------|------------|
| Event time | When something happened (e.g., Q4 earnings period) |
| Availability time | When data became known (e.g., filing date) |
| Revision | Later correction to previously published data |

## The Problem

```python
# WRONG: Using revised GDP when it wasn't available
gdp = fred.get_series("GDP")  # Contains all revisions
signal = gdp.pct_change()     # Uses final values, not initial releases

# Reality: GDP released ~30 days after quarter end, revised 2-3 times
```

## Rules

### Fundamentals

```python
# WRONG: Join on report period
df = prices.join(fundamentals, on='quarter')

# CORRECT: Join on filing date (availability time)
df = prices.join(fundamentals, on='filing_date')
# Only use fundamental data AFTER it was filed
```

### Macro Data

```python
# WRONG: Align by observation date
df['gdp'] = gdp.reindex(df.index, method='ffill')

# CORRECT: Align by release date + lag
release_calendar = get_fred_release_dates('GDP')
df['gdp'] = align_by_availability(gdp, release_calendar, lag_days=1)
```

### SEC Filings

```python
# Key dates for 10-K:
# - period_end: Dec 31 (fiscal year end)
# - filed_date: Feb 28 (when SEC received it)
# - available: Feb 28 + processing time

# Use filed_date, not period_end
features = filings[filings['filed_date'] <= current_date]
```

## Bitemporal Model

Track two time dimensions:
1. **Valid time**: When fact was true (event time)
2. **Transaction time**: When fact became known (availability time)

```python
# Store both timestamps
fundamentals_table = {
    'symbol': 'AAPL',
    'metric': 'revenue',
    'value': 100B,
    'valid_time': '2024-12-31',      # Q4 2024
    'transaction_time': '2025-02-01'  # Filing date
}
```

## Guardrails

- FRED data: Check release calendar, not observation date
- SEC filings: Use `filed_date`, not `period_of_report`
- Earnings: Available after market close on announcement day
- Macro revisions: Initial release often differs 0.5-1% from final

## Checklist

- [ ] All fundamental joins use filing/release date
- [ ] Macro data aligned by availability, not observation
- [ ] No "as-reported" vs "revised" confusion
- [ ] Lag buffer added for data processing time
