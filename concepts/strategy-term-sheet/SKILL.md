---
name: ml4t-strategy-term-sheet
description: "Document strategy hypotheses before backtesting with falsifiable, pre-registered specs. Use when starting a new strategy to prevent post-hoc rationalization."
when_to_use: "Use when starting strategy research, defining a new signal, or preparing for backtest evaluation"
dependencies: [backtest-overfitting]
metadata:
  book_chapters: "1, 6"
  library: ""
---
# Strategy Term Sheet

A version-controlled specification that documents a strategy's hypothesis, implementation, and success criteria BEFORE any backtest is run. Without pre-registration, every positive result is indistinguishable from post-hoc rationalization.

## The Problem

The natural workflow -- explore data, find a pattern, backtest it, then write up the rationale -- guarantees overfitting. After seeing results, humans unconsciously construct narratives that explain why the strategy "should" work. A term sheet written before the backtest forces you to commit to a falsifiable hypothesis. If the hypothesis was wrong, you learn something. If you write the hypothesis after seeing results, you learn nothing.

## The Pattern

### WRONG

```python
# Backtest first, rationalize later
results = backtest(params)
if results.sharpe > 1.5:
    write_report(
        title="Cross-Asset Momentum Strategy",
        rationale="Momentum works because of behavioral underreaction...",
        # Rationalization written AFTER seeing the results
    )
```

### CORRECT

```yaml
# hypothesis.yaml -- committed to git BEFORE any backtest
name: "Cross-Asset ETF Momentum v1.0"
status: pre-registered

hypothesis:
  mechanism: >
    Institutional rebalancing creates short-term momentum in ETF returns.
    Monthly flows into winning asset classes persist for 3-12 months due
    to allocation committee review cycles.
  metric: "Risk-adjusted 6-month return (Sharpe-normalized momentum)"
  outcome: "Top-quintile momentum ETFs outperform bottom quintile by 4%+ annualized"
  durability: >
    Institutional allocation cycles are structural, not arbitrageable by
    fast capital because the flow is driven by policy, not information.

success_criteria:
  min_sharpe: 0.8
  min_ic: 0.03
  max_drawdown: -0.25
  min_backtest_years: 10

kill_conditions:
  - "Sharpe < 0.5 over any rolling 3-year window"
  - "IC turns negative for 6+ consecutive months"
  - "Costs exceed 40% of gross alpha"
```

```bash
git add hypothesis.yaml
git commit -m "Pre-register: Cross-Asset ETF Momentum v1.0"
# NOW run the backtest
```

## Four-Component Hypothesis

Every strategy term sheet must answer four questions:

| Component | Question | Requirement |
|-----------|----------|-------------|
| **Mechanism** | Why does this work? | Economic rationale, not curve fitting |
| **Metric** | What data operationalizes it? | Exact formula, lookback, and thresholds |
| **Outcome** | What are you predicting? | Quantitative, falsifiable success criteria |
| **Durability** | Why will it persist? | Structural reason it is not arbitraged away |

If you cannot fill in all four before backtesting, the idea is not ready to test.

## Implementation Blueprint

The term sheet should also specify enough detail to reproduce the backtest:

```yaml
implementation:
  universe: "Top 100 US ETFs by AUM, excluding leveraged and inverse"
  features:
    - "6-month total return, volatility-adjusted"
    - "3-month flow momentum (estimated from volume)"
  rebalance: "Monthly, last trading day"
  position_sizing: "Equal-weight top quintile long, bottom quintile short"
  costs:
    spread_bps: 3
    impact_model: "square_root"
    safety_margin: "2.5x minimum"
```

## Guardrails

- The term sheet must be committed to version control before any code touches data.
- Success criteria must be quantitative and falsifiable ("Sharpe > 0.8"), not vague ("good risk-adjusted returns").
- Kill conditions must be thresholds you are actually willing to enforce.
- Every formula in the term sheet must translate directly to code -- no ambiguous prose.
- Update the term sheet with results after backtesting, but never change the pre-registered criteria.

## Checklist

- [ ] Four-component hypothesis complete (mechanism, metric, outcome, durability)
- [ ] Success criteria are quantitative and falsifiable
- [ ] Kill conditions defined with specific thresholds
- [ ] Term sheet committed to git BEFORE any backtest code runs
- [ ] Implementation blueprint detailed enough to reproduce the backtest
- [ ] Safety margin >= 2.5x documented in feasibility section
