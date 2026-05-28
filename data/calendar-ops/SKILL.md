---
name: ml4t-calendar-ops
description: "Trading calendar awareness for correct date alignment and rolling windows. Use when aligning data across markets or computing holiday-aware windows."
when_to_use: "Use when computing rolling statistics, aligning multi-market data, or handling holidays"
dependencies: []
metadata:
  book_chapters: "2, 3"
  library: ""
paths: ["**/*data*.py", "**/*fetch*.py", "**/*bars*.py", "**/*universe*.py", "**/*calendar*.py", "**/*futures*.py", "**/*export*.py", "**/*synthetic*.py"]
---
# Calendar Operations

Using calendar days instead of trading days for a 20-day rolling window includes weekends and holidays, producing a window that covers 28 calendar days but only 20 observations — silently misaligning your features with your labels.

## The Problem

Markets are closed on weekends and holidays. A "20-day momentum" signal should use 20 trading days (~4 weeks), not 20 calendar days (~2.8 weeks). When you mix calendar-day math with trading-day data, rolling windows span wrong periods, cross-market joins misalign (NYSE is closed on Presidents Day but LSE is open), and date arithmetic produces gaps your model interprets as missing data. These errors are invisible until you compare strategy behavior across markets or time zones.

## The Pattern

### WRONG
```python
import polars as pl
from datetime import timedelta

# Calendar days for rolling window — includes weekends, holidays
df = df.with_columns(
    momentum=pl.col("close") / pl.col("close").shift(20) - 1  # shift(20) = 20 rows
)
# If data has gaps (holidays), shift(20) is NOT 20 trading days — it skips over them unevenly

# Date arithmetic for label alignment
df = df.with_columns(
    target_date=(pl.col("timestamp") + timedelta(days=21))  # 21 calendar days != 21 trading days
)
```

### CORRECT
```python
import polars as pl
import exchange_calendars as xcals

def get_trading_sessions(
    calendar_code: str, start: str, end: str,
) -> pl.Series:
    """Get valid trading sessions for an exchange."""
    cal = xcals.get_calendar(calendar_code)
    sessions = cal.sessions_in_range(start, end)
    return pl.Series("timestamp", sessions.to_list())

def add_trading_day_offset(
    df: pl.DataFrame, calendar_code: str, offset: int,
) -> pl.DataFrame:
    """Shift dates by N trading days (not calendar days)."""
    cal = xcals.get_calendar(calendar_code)
    sessions = sorted(cal.sessions_in_range(
        df["timestamp"].min(), df["timestamp"].max() + timedelta(days=offset * 2)
    ).to_list())
    idx = {d: i for i, d in enumerate(sessions)}
    return df.with_columns(
        pl.col("timestamp").map_elements(
            lambda d: sessions[idx[d] + offset] if d in idx else None,
            return_dtype=pl.Date,
        ).alias(f"timestamp_offset_{offset}d")
    )

# Align data to NYSE trading calendar
nyse_sessions = get_trading_sessions("XNYS", "2020-01-01", "2024-12-31")
df = df.filter(pl.col("timestamp").is_in(nyse_sessions))
```

## Multi-Market Alignment

When combining data from different exchanges, find common trading days.

```python
import exchange_calendars as xcals

def common_trading_days(*calendar_codes: str, start: str, end: str) -> list:
    """Find dates when ALL specified exchanges are open."""
    session_sets = []
    for code in calendar_codes:
        cal = xcals.get_calendar(code)
        session_sets.append(set(cal.sessions_in_range(start, end).to_list()))
    common = sorted(set.intersection(*session_sets))
    return common

# US + Europe common trading days (excludes US-only and EU-only holidays)
common = common_trading_days("XNYS", "XLON", "XETR", start="2020-01-01", end="2024-12-31")
```

## Holiday Forward-Fill

For cross-market features that need a value every trading day, build a DataFrame of all sessions from the target calendar, left-join your data onto it, and forward-fill. This ensures no gaps without inventing data — each missing day carries the last known value.

## Guardrails

- Crypto markets trade 24/7 — no calendar needed, but be aware of exchange maintenance windows
- Early closes (half-days) are separate from holidays — `exchange_calendars` tracks both
- CME and ICE have different holiday schedules than NYSE — always use exchange-specific calendars
- Timezone matters: NYSE closes at 16:00 ET, which is 21:00 UTC — a "daily" bar's date depends on the timezone

## Checklist

- [ ] Exchange-specific calendar used (not generic business day)
- [ ] Rolling windows count trading days, not calendar days
- [ ] Multi-market data aligned to common sessions
- [ ] Holidays forward-filled or excluded (not left as gaps)
- [ ] Timezones explicit throughout the pipeline
