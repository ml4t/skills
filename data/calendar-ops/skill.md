---
name: ml4t-calendar-ops
description: Handle trading calendars and market hours
category: data
type: operational
dependencies: []
book_chapters: [3, 4]
---

# Calendar Operations

Trading calendars define valid trading times and align data correctly.

## API

```python
import exchange_calendars as xcals

# Get calendar
nyse = xcals.get_calendar('XNYS')  # NYSE
cme = xcals.get_calendar('CMES')   # CME

# Trading sessions
sessions = nyse.sessions_in_range('2020-01-01', '2024-12-31')

# Check if trading day
is_trading = nyse.is_session('2024-12-25')  # False (Christmas)
```

## Common Calendars

| Exchange | Code | Hours (ET) |
|----------|------|------------|
| NYSE | XNYS | 9:30-16:00 |
| CME Equity | CMES | 17:00-16:00 |
| CME FX | CMES | 17:00-16:00 |
| LSE | XLON | 8:00-16:30 GMT |

## Alignment

```python
# Align data to trading calendar
def align_to_calendar(
    data: pl.DataFrame,
    calendar_code: str = 'XNYS'
) -> pl.DataFrame:
    cal = xcals.get_calendar(calendar_code)
    sessions = cal.sessions_in_range(
        data['date'].min(),
        data['date'].max()
    )
    return data.filter(pl.col('date').is_in(sessions))
```

## Holiday Handling

```python
# Forward fill for holidays
def ffill_holidays(df: pl.DataFrame, calendar_code: str) -> pl.DataFrame:
    cal = xcals.get_calendar(calendar_code)
    all_sessions = cal.sessions_in_range(
        df['date'].min(),
        df['date'].max()
    )

    return (
        pl.DataFrame({'date': all_sessions})
        .join(df, on='date', how='left')
        .with_columns(pl.all().forward_fill())
    )
```

## Multi-Market Sync

```python
# Find common trading days
def common_sessions(*calendars: str) -> list:
    cals = [xcals.get_calendar(c) for c in calendars]
    sessions = set(cals[0].sessions)
    for cal in cals[1:]:
        sessions &= set(cal.sessions)
    return sorted(sessions)

# US + Europe common days
common = common_sessions('XNYS', 'XLON', 'XETR')
```

## Guardrails

- Always use exchange-specific calendars
- Crypto trades 24/7 (no calendar needed)
- Different markets have different holidays
- Early closes are separate from holidays

## Checklist

- [ ] Calendar matches instrument exchange
- [ ] Holidays handled (fill or exclude)
- [ ] Multi-market alignment if needed
- [ ] Timezone specified explicitly
