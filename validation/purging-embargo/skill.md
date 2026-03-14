---
name: ml4t-purging-embargo
description: Remove training samples that leak information into test set
category: validation
type: conceptual
dependencies: [lookahead-bias]
book_chapters: [10]
---

# Purging and Embargo

Standard CV fails for time series because labels overlap in time.

## The Problem

5-day forward return at day 98 uses prices 98-103.
Test set starts at day 100.
Training sample 98 leaks info about test prices → invalid CV.

## Purging

Remove training samples whose labels overlap with test set.

```
Test starts at t=100, label_horizon=5
Purge training samples where t > 100 - 5 = 95
Keep samples 0-95, test on 100+
```

## Embargo

Additional buffer after test set for autocorrelation.

```
Test ends at t=110, embargo_size=2
Also remove training samples 111-112
```

## Visual

```
Timeline:    [==TRAIN==][PURGE][==TEST==][EMBARGO][==TRAIN==]
Samples:         0-95    96-99   100-110   111-112   113+
```

## Parameters

| Label Type | label_horizon | embargo_size |
|------------|---------------|--------------|
| 5-day return | 5 | 1-2 |
| 10-day return | 10 | 2-3 |
| Triple-barrier 20d | 20 | 3-5 |

Rule: embargo ≈ 10-20% of label_horizon

## Implementation

```python
from ml4t.diagnostic.splitters import CombinatorialPurgedCV

cv = CombinatorialPurgedCV(
    n_groups=8,
    n_test_groups=2,
    label_horizon=5,    # Must match label construction
    embargo_size=2
)
```

## Mistakes

```python
# WRONG: label_horizon doesn't match actual labels
y = df['close'].pct_change(10).shift(-10)  # 10-day labels
cv = CombinatorialPurgedCV(label_horizon=5)  # Wrong!

# CORRECT
cv = CombinatorialPurgedCV(label_horizon=10)  # Matches labels
```

## Checklist

- [ ] label_horizon matches your label construction
- [ ] embargo_size > 0 for autocorrelated data
- [ ] Verify training set size after purging is sufficient
