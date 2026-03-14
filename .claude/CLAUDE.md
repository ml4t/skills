# ML4T Skills Development

**Location**: `/home/stefan/ml4t/skills`

## Critical: Skill Design for Agent Consumption

Skills are reference material for AI agents, NOT human documentation.

### Size Target
- **<2KB per skill** (~500 tokens max)
- Verify with `wc -c` after writing

### Content Rules
**Include:**
- WRONG/CORRECT code patterns (minimal)
- API signatures with key parameters
- Guardrails (what to check)
- Checklist (actionable items)

**Exclude:**
- Lengthy explanations of "why"
- Multiple examples showing same pattern
- Prose descriptions
- Verbose comments in code

### Skill Template
```markdown
---
name: ml4t-<skill-name>
description: One line
category: concepts|data|features|validation|backtest|portfolio|workflows
type: conceptual|operational|workflow
dependencies: [list]
book_chapters: [numbers]
quantlab_module: ml4t.x.y (if operational)
---

# Title

One sentence purpose.

## [Concepts OR API] (pick one)

## Rules (WRONG/CORRECT)

## Guardrails

## Checklist
```

## Source Material

- **Book**: `/home/stefan/ml4t/book/` - Chapter outlines in `manuscript/outline.md`
- **Code**: `/home/stefan/ml4t/code/` - Reference implementations
- **QuantLab**: `/home/stefan/ml4t/software/` - API source code

Always verify skill content against book chapters before writing.

## Directory Structure

- `concepts/` - 10 skills: Domain pitfalls and principles
- `data/` - 8 skills: ml4t-data API wrappers
- `features/` - 10 skills: ml4t-engineer API wrappers
- `validation/` - 8 skills: ml4t-diagnostic API wrappers
- `backtest/` - 6 skills: ml4t-backtest API wrappers
- `portfolio/` - 6 skills: Portfolio optimization and risk
- `workflows/` - 4 skills: Composite end-to-end workflows

## Progress Tracking

**ALL SKILLS COMPLETE** (52/52)

### Concepts (10/10)
lookahead-bias, data-leakage, point-in-time, survivorship-bias, non-stationarity,
backtest-overfitting, information-coefficient, transaction-costs, regime-awareness, strategy-term-sheet

### Data (8/8)
fetch-data, define-universe, validate-data, build-bars, continuous-futures,
synthetic-data, calendar-ops, data-export

### Features (10/10)
compute-features, triple-barrier, feature-families, meta-labels, regime-features,
microstructure-features, feature-selection, feature-store, feature-validation, horizon-design

### Validation (8/8)
cpcv, purging-embargo, deflated-sharpe, walk-forward-cv, evaluate-factor,
stationarity-tests, drift-detection, shap-analysis

### Backtest (6/6)
run-backtest, tearsheet, vectorized-backtest, cost-model, regime-backtest, sensitivity-analysis

### Portfolio (6/6)
position-sizing, portfolio-optimize, risk-metrics, stress-test, exposure-analysis, kill-switch

### Workflows (4/4)
strategy-workflow, factor-research, model-validation, production-readiness
