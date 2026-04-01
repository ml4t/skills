---
name: ml4t-model-governance
description: "Model risk management with validation independence and lifecycle controls. Use when implementing governance for production trading models."
when_to_use: "Use when building governance around ML trading models for regulatory compliance or institutional risk management"
dependencies: [model-validation, risk-metrics]
metadata:
  book_chapters: "26"
  library: ""
paths: ["**/*live*.py", "**/*deploy*.py", "**/*monitor*.py", "**/*govern*.py", "**/*mlops*.py", "**/*pipeline*.py"]
---
# Model Governance

Deploying a model and never revisiting it is how firms accumulate silent risk. Governance ensures every model is inventoried, independently validated, periodically challenged, and retired when it no longer works.

## The Problem

A team deploys a model that works well. A year later, market regime shifts, feature distributions change, and the model quietly degrades. Nobody reviews it because there is no process. The firm discovers the problem only after a large drawdown. Regulators (SR 11-7 for banks, MiFID II for EU firms) require documented model risk management. Even without regulation, ungoverned models accumulate hidden risk.

## The Pattern

### WRONG
```python
# Deploy and forget — no validation, no review cycle, no documentation
model = train_best_model(X, y)
deploy_to_production(model)
# ... 18 months later ...
# "Why is this strategy losing money?"
# "Who built this model? What data did it use?"
# "When was it last validated?"
# Nobody knows.
```

### CORRECT
```python
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field

@dataclass
class ModelRecord:
    """Governance record for a production model."""
    model_id: str
    owner: str
    description: str
    deployed_at: datetime
    last_validated: datetime
    next_review: datetime
    status: str  # "active", "under_review", "retired"
    risk_tier: int  # 1=high (P&L), 2=medium (signals), 3=low (research)
    validation_reports: list = field(default_factory=list)

    def needs_review(self) -> bool:
        return datetime.now() > self.next_review

    def add_validation(self, report: dict):
        self.validation_reports.append({
            **report,
            "validated_at": datetime.now().isoformat(),
        })
        self.last_validated = datetime.now()
        # Tier 1: quarterly, Tier 2: semi-annual, Tier 3: annual
        intervals = {1: 90, 2: 180, 3: 365}
        self.next_review = datetime.now() + timedelta(days=intervals[self.risk_tier])
```

## Governance Framework

| Component | Purpose | Frequency |
|-----------|---------|-----------|
| Model inventory | Know every model in production | Continuous |
| Independent validation | Second pair of eyes on methodology | Before deployment |
| Performance monitoring | Detect degradation early | Daily/weekly |
| Challenger models | Benchmark against alternatives | Quarterly |
| Periodic revalidation | Confirm model still works | Per risk tier |
| Change control | Document and approve modifications | Every change |
| Retirement protocol | Remove models that no longer work | When triggered |

## Validation Independence

The person who builds the model must not be the person who validates it. Validation must cover: conceptual soundness, data quality, out-of-sample performance, sensitivity analysis, benchmark comparison (e.g., ridge regression baseline), stress testing (2008, 2020 scenarios), and documentation completeness.

## Challenger Model Protocol

Every production model has at least one challenger. Quarterly, compare champion vs challenger on the same recent live window (e.g., 63 trading days). Promote only if the challenger beats the champion's IC by 10% or more. Log the comparison regardless of outcome.

## Guardrails

- No model goes to production without independent validation sign-off
- Model inventory must be complete — shadow models and "temporary" scripts count
- Review deadlines are hard: miss a review, model goes to reduced-risk mode automatically
- Every model change (retrain, config update, data change) requires a change record
- Retired models stay in the registry with status "retired" — never delete history

## Checklist

- [ ] Model inventory lists every production model with owner and risk tier
- [ ] Independent validation completed before first deployment
- [ ] Challenger model identified and benchmarked quarterly
- [ ] Review schedule set per risk tier (Tier 1: 90d, Tier 2: 180d, Tier 3: 365d)
- [ ] Change control process documented and enforced
- [ ] Retirement criteria defined (max drawdown, IC floor, drift threshold)
