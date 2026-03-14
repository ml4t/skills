---
name: ml4t-feature-families
description: Taxonomy of alpha factor types and their characteristics
category: features
type: conceptual
dependencies: []
book_chapters: [7]
---

# Feature Families

Organize features by source and mechanism for diversity.

## Taxonomy

| Family | Source | Horizon | Example |
|--------|--------|---------|---------|
| Momentum | Price | Medium-term | 12-month return |
| Mean-reversion | Price | Short-term | RSI, z-score |
| Value | Fundamentals | Long-term | P/E, P/B |
| Quality | Fundamentals | Long-term | ROE, accruals |
| Low-risk | Price | Medium-term | Beta, volatility |
| Microstructure | Order flow | Intraday | Spread, OFI |
| Sentiment | Alt data | Variable | News score |
| Macro | Economic | Long-term | Yield curve |

## Feature vs Signal

| Term | Definition |
|------|------------|
| Feature | Raw predictive variable |
| Alpha factor | Feature with economic hypothesis |
| Signal | Processed factor for trading |

## Diversity Principles

```python
# WRONG: All momentum variants
features = [
    'mom_1m', 'mom_3m', 'mom_6m', 'mom_12m',  # Same family
    'tsmom', 'xsmom'  # Same family
]

# CORRECT: Multi-family
features = [
    'mom_12m',        # Momentum
    'reversal_5d',    # Mean-reversion
    'pe_ratio',       # Value
    'roe',            # Quality
    'realized_vol',   # Low-risk
    'ofi',            # Microstructure
]
```

## Trade-offs

| Dimension | Simple Feature | Complex Feature |
|-----------|----------------|-----------------|
| Computation | Fast | Slow/expensive |
| Interpretability | High | Low |
| Overfitting risk | Low | High |
| Adaptivity | Low | High |

## Guardrails

- Maximize family diversity, not feature count
- Each family captures different information
- Correlated features waste model capacity
- Start simple, add complexity if needed

## Checklist

- [ ] Features span multiple families
- [ ] Family coverage documented
- [ ] Correlation between features analyzed
- [ ] Economic hypothesis per family
