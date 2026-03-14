---
name: ml4t-strategy-term-sheet
description: Document strategies before testing with falsifiable hypotheses
category: concepts
type: conceptual
dependencies: [backtest-overfitting]
book_chapters: [2]
---

# Strategy Term Sheet

Version-controlled specification documenting strategy BEFORE backtesting.

## Purpose

| Audience | Use |
|----------|-----|
| You | Verify implementation matches intent |
| Teams | Shared spec for PM, data, ML |
| Risk | MRM audit trail |
| Future self | "Why did I build this?" |

## Structure

### 1. Header
```yaml
name: "Cross-Asset ETF Momentum v1.0"
classification: Price-Based | Fundamental | Structural | ML-Driven
lifecycle_stage: Discovery | Publication | Crowding | Decay
status: Research | Backtesting | Paper Trading | Live | Retired
```

### 2. Four-Component Hypothesis

| Component | Question | Requirement |
|-----------|----------|-------------|
| Mechanism | Why does it work? | Economic rationale (not curve fit) |
| Metric | What data operationalizes it? | Exact formula, lookback, thresholds |
| Outcome | What are you predicting? | Pre-defined success criteria |
| Durability | Why will it persist? | Why not arbitraged away |

### 3. Implementation Blueprint
- Universe definition (precise filters)
- Feature formulas (code-ready)
- Signal generation logic
- Position sizing method
- Rebalancing rules

### 4. Feasibility
- Transaction cost breakdown (bps)
- Safety margin: gross_alpha / costs >= 2.5x
- Maximum AUM with justification

### 5. Risk Framework
- OOS testing periods (train/test/holdout)
- Performance thresholds (pre-committed)
- Kill conditions (when to retire)

## Rules

```python
# WRONG: Backtest first, document later
results = backtest(params)
if results.sharpe > 1.5:
    write_term_sheet(params)  # Post-hoc rationalization

# CORRECT: Document first, commit, then test
term_sheet.write("hypothesis.md")
git.commit("Pre-registered hypothesis")
results = backtest(params)
term_sheet.update("results.md")
```

## Guardrails

- Write success thresholds BEFORE seeing results
- All formulas must translate directly to code
- Kill conditions you're actually willing to enforce
- Version control with atomic commits

## Checklist

- [ ] Mechanism explains WHY (not just WHAT)
- [ ] Hypothesis is falsifiable
- [ ] Success criteria pre-committed
- [ ] Term sheet committed to git before backtest
- [ ] Safety margin >= 2.5x
