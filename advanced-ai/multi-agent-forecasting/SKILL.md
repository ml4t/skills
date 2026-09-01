---
name: ml4t-multi-agent-forecasting
description: "Multi-agent probability forecasting with diversity, aggregation, and debate controls. Use when combining several agent forecasts or evaluating forecast ensembles."
when_to_use: "Use when building multi-agent research, Neyman aggregation, adversarial debate, or resolved-question forecast evaluation"
dependencies: [agent-state-memory]
metadata:
  book_chapters: "24"
  library: ""
paths: ["**/*multi_agent*.py", "**/*forecasting_pipeline*.py", "**/*adversarial_debate*.py"]
---
# Multi-Agent Forecasting

Multiple agents help only when they add independent information or structured disagreement. Re-running the same prompt at higher temperature usually produces correlated forecasts, not a useful ensemble.

## The Problem

Forecast pipelines often report "agent consensus" from several identical agents. On well-specified macro questions, those agents read the same evidence and return nearly identical probabilities. Averaging correlated forecasts gives false confidence unless the system measures diversity, calibrates probabilities, and stress-tests the consensus with opposing arguments.

## The Pattern

### WRONG
```python
forecasts = [agent.run(question, temperature=0.7) for _ in range(5)]
p_yes = sum(f.p_yes for f in forecasts) / len(forecasts)
print(f"consensus={p_yes:.2%}")
```

### CORRECT
```python
import math
from statistics import mean


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def inv_logit(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def neyman_aggregate(probs: list[float], diversity: float) -> float:
    avg_logit = mean(logit(p) for p in probs)
    return inv_logit(avg_logit * diversity)


forecasts = [
    bull_agent.run(question),
    bear_agent.run(question),
    base_rate_agent.run(question),
]
divergence = max(f.p_yes for f in forecasts) - min(f.p_yes for f in forecasts)
aggregate = neyman_aggregate([f.p_yes for f in forecasts], diversity=1.2)

if divergence < 0.05:
    aggregate = run_adversarial_debate(question, forecasts).p_yes
```

## Forecast Controls

- Use role, evidence-source, or method diversity; do not rely on temperature alone
- Preserve each forecast's evidence, confidence, rationale, and uncertainty list
- Aggregate in logit space when probabilities are far from 50%
- Evaluate resolved questions with Brier score, log score, calibration, and sharpness
- Run ablations: no debate, no supervisor, simple mean, weighted aggregation

## Guardrails

- **Identical-agent ensemble** - check probability spread before claiming diversity
- **Consensus without calibration** - low disagreement is not the same as accuracy
- **Free-text handoff** - downstream aggregation needs typed `p_yes` fields
- **Leaky evaluation** - only score questions resolved after the forecast timestamp

## Checklist

- [ ] Forecast artifacts contain probability, confidence, evidence, and timestamp
- [ ] Agent diversity is structural, not only sampling noise
- [ ] Aggregation method and diversity factor are recorded
- [ ] Debate or supervisor stages are evaluated with ablations
- [ ] Resolved-question scoring uses proper scoring rules
