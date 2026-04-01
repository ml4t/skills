---
name: ml4t-systematic-edge
description: "The durable edge in quantitative investing comes from disciplined process, not clever models. Use when designing research workflows or reviewing strategy development practices."
when_to_use: "Use when starting a new research program, reviewing process discipline, or onboarding to quantitative workflows"
dependencies: [strategy-term-sheet, backtest-overfitting]
metadata:
  book_chapters: "27"
  library: ""
---
# The Systematic Edge

The researcher who runs 200 backtests and reports the best one has no edge. The researcher who pre-registers one hypothesis, tests it once, and documents the result — even if negative — is building a compounding advantage. Process is the edge, not the model.

## The Problem

Technical skill is necessary but not sufficient. Two researchers with identical tools produce different outcomes because one follows a disciplined process and the other does not. The undisciplined researcher:

- Explores parameters until something works, then rationalizes the choice
- Reports the best of many backtests without adjusting for multiple testing
- Skips the holdout set "just this once" because the signal looks strong
- Reuses stale features without checking for drift

Each shortcut feels minor. Compounded across a research program, they guarantee that nothing survives live deployment.

## The Pattern

### WRONG
```python
# Explore until something looks good, then ship it
best_sharpe = 0
for lookback in range(5, 260, 5):
    for threshold in [0.01, 0.02, 0.05, 0.1]:
        result = backtest(lookback=lookback, threshold=threshold)
        if result["sharpe"] > best_sharpe:
            best_sharpe = result["sharpe"]
            best_params = (lookback, threshold)

# No correction, no pre-registration, no holdout
print(f"Deploying with Sharpe {best_sharpe:.2f}")  # Fiction
```

### CORRECT
```python
# 1. Pre-register hypothesis BEFORE any backtest
hypothesis = """
Momentum(63d) long-short on S&P 500, monthly rebalance.
Success: Sharpe > 0.5 after costs, PBO < 0.50, deflated Sharpe > 0.
Failure: any gate below threshold → reject and document.
"""

# 2. Run the pre-registered configuration exactly once
result = backtest(lookback=63, threshold=0.0, universe="sp500", costs=True)

# 3. Apply statistical corrections (see backtest-overfitting skill)
# With a single pre-registered config, n_trials = 1 → no inflation correction needed
dsr = result["sharpe"]  # No deflation needed for single trial

# 4. Record outcome regardless of result
log_result(hypothesis, result, dsr, outcome="pass" if dsr > 0 else "reject")
```

## The Five-Stage Discipline

| Stage | Gate | Anti-Pattern |
|-------|------|-------------|
| 1. Hypothesis | Is it falsifiable? | Vague goals with no rejection criteria |
| 2. Data + Features | PIT-correct, stationary? | Using future data, stale features |
| 3. Model | Beats baseline on purged CV? | Reporting best of many models |
| 4. Backtest | Survives costs and turnover? | Zero-cost simulation |
| 5. Review | Documented, reproducible? | "It worked on my machine" |

Each stage must earn the right to proceed to the next. A failed gate produces a documented rejection, not a workaround.

## Guardrails

- **Pre-register before running**: write the hypothesis, success criteria, and rejection criteria in version control before any code runs
- **Count all trials**: every parameter you tried, every feature you tested, every filter you adjusted — each one is a trial for multiple-testing correction
- **Protect the holdout**: the holdout set is touched exactly once, at the very end — no exceptions
- **Document rejections**: a rejected hypothesis is more valuable than a lucky success because it narrows the search space for the next researcher
- **Review your own cognitive state**: fatigue and confirmation bias are the most common sources of process breakdown

## Production Implementation

No library implements process discipline — it lives in research habits and team norms. The skills in this repo are the implementation:

- `strategy-term-sheet` — pre-registration
- `backtest-overfitting` — multiple testing correction
- `cpcv` — distribution-based evaluation
- `case-study-development` — stage-gated workflow

## Checklist

- [ ] Hypothesis pre-registered with falsifiable success criteria before any backtest
- [ ] Total trial count documented for deflated Sharpe correction
- [ ] Holdout set preserved and used exactly once
- [ ] Failed hypotheses documented with rejection reasons
- [ ] Research process reviewed periodically for discipline drift
