# ML4T Skills for Claude Code

Skills that teach AI agents the Machine Learning for Trading workflow from the [ML4T 3rd Edition](https://ml4trading.io) book.

## Overview

This is the first "agent-first" approach to quantitative finance education. These skills enable AI coding agents to:

1. **Understand critical ML4T concepts** (lookahead bias, data leakage, regime shifts)
2. **Use QuantLab APIs correctly** (ml4t-data, ml4t-engineer, ml4t-backtest)
3. **Avoid common pitfalls** that trip up both humans and machines
4. **Execute complete workflows** from strategy definition to production deployment

## Skill Categories

| Category | Count | Description |
|----------|-------|-------------|
| `concepts/` | 10 | Foundational ML4T concepts and pitfalls |
| `data/` | 8 | Data sourcing, validation, and management |
| `features/` | 10 | Feature engineering and labeling |
| `validation/` | 8 | Cross-validation and evaluation metrics |
| `backtest/` | 6 | Strategy simulation and analysis |
| `portfolio/` | 6 | Portfolio optimization and risk management |
| `workflows/` | 4 | End-to-end composite workflows |

## Quick Start

### Using a Skill

In a Claude Code session:
```
/ml4t-lookahead-bias
```

Or reference skills when working:
```
"Before computing features, review the lookahead-bias skill to avoid common mistakes"
```

### Skill Dependencies

Skills declare prerequisites. For example, `triple-barrier` depends on `lookahead-bias`:

```yaml
dependencies:
  - lookahead-bias
```

## Skill Types

### Conceptual Skills
Teach understanding of ML4T domain concepts. Focus on:
- The problem: What goes wrong without this knowledge
- The pattern: How to recognize the issue
- The solution: How to prevent or fix it

Example: `concepts/lookahead-bias/`

### Operational Skills
Wrap QuantLab library APIs with guardrails. Include:
- API reference with parameters and returns
- Example usage patterns
- Common mistakes to avoid

Example: `features/triple-barrier/`

### Workflow Skills
Compose atomic skills into complete workflows:
- `strategy-workflow` - Full strategy development cycle
- `factor-research` - Complete factor research process
- `model-validation` - Comprehensive model validation
- `production-readiness` - Pre-production checklist

## Priority Skills

Start with these 5 critical skills that address the most common ML4T failures:

1. **`concepts/lookahead-bias`** - Prevent using future information
2. **`concepts/data-leakage`** - Avoid feature/target/CV contamination
3. **`features/triple-barrier`** - Core ML4T labeling method
4. **`validation/cpcv`** - Combinatorial Purged Cross-Validation
5. **`validation/purging-embargo`** - Time-series CV design

## Directory Structure

```
skills/
├── concepts/           # TIER 1: Foundational concepts
│   ├── lookahead-bias/
│   ├── data-leakage/
│   └── ...
├── data/               # TIER 2: Data operations
│   ├── fetch-data/
│   └── ...
├── features/           # TIER 3: Feature engineering
│   ├── triple-barrier/
│   └── ...
├── validation/         # TIER 4: Validation & evaluation
│   ├── cpcv/
│   └── ...
├── backtest/           # TIER 5: Backtesting
│   ├── run-backtest/
│   └── ...
├── portfolio/          # TIER 6: Portfolio & risk
│   ├── position-sizing/
│   └── ...
└── workflows/          # TIER 7: Composite workflows
    ├── strategy-workflow/
    └── ...
```

## Related Resources

- **Book**: `/home/stefan/ml4t/book/` - ML4T 3rd Edition manuscript
- **Code**: `/home/stefan/ml4t/code/` - Jupyter notebooks by chapter
- **QuantLab**: `/home/stefan/ml4t/software/` - Production libraries
  - `ml4t-data` - Data providers
  - `ml4t-engineer` - Feature engineering
  - `ml4t-backtest` - Backtesting engine
  - `ml4t-diagnostic` - Evaluation tools

## The ML4T Workflow

Skills are organized around the 5-stage ML4T workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ML4T WORKFLOW                                │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│ HYPOTHESIS│   DATA   │ MODELING │SIMULATION│    DEPLOYMENT      │
├──────────┼──────────┼──────────┼──────────┼────────────────────┤
│ strategy-│ fetch-   │ compute- │ run-     │ production-        │
│ term-    │ data     │ features │ backtest │ readiness          │
│ sheet    │          │          │          │                    │
│          │ validate-│ triple-  │ tearsheet│ drift-detection    │
│          │ data     │ barrier  │          │                    │
│          │          │          │ regime-  │ kill-switch        │
│          │ define-  │ feature- │ backtest │                    │
│          │ universe │ selection│          │                    │
└──────────┴──────────┴──────────┴──────────┴────────────────────┘
```

## Contributing

When adding new skills:

1. Create directory: `mkdir skills/<category>/<skill-name>/`
2. Write `skill.md` following the template
3. Include book chapter references
4. Add API examples for operational skills
5. Document dependencies on other skills
