---
name: ml4t-mlops-pipeline
description: Automated ML pipeline for model retraining, versioning, and deployment. Use when moving from ad-hoc model updates to a reproducible production workflow.
dependencies: [drift-detection, feature-store]
metadata:
  book_chapters: "27"
  library: ""
---

# MLOps for Trading Models

Manual model updates — retrain on a laptop, copy weights to production — break reproducibility and create silent model drift. Automated pipelines ensure the same code and data always produce the same model.

## The Problem

A quant retrains a model locally, eyeballs the metrics, copies the pickle to the production server. Three months later, nobody can reproduce the model. The training data has changed, the feature code has drifted, and the model version in production does not match any known configuration. When performance degrades, the team cannot tell if the market changed or the model is stale.

## The Pattern

### WRONG
```python
# Ad-hoc retraining — no versioning, no reproducibility
import pickle
from sklearn.linear_model import Ridge

model = Ridge(alpha=1.0)
model.fit(X_train, y_train)
print(f"R2: {model.score(X_test, y_test):.3f}")  # Looks good enough

# Copy to production manually
with open("/production/model.pkl", "wb") as f:
    pickle.dump(model, f)  # Which data? Which features? Which code version?
```

### CORRECT
```python
import hashlib
import json
from datetime import datetime
from pathlib import Path
from sklearn.linear_model import Ridge

def train_and_register(config: dict, X_train, y_train, X_test, y_test):
    """Train model with full provenance tracking."""
    # Deterministic config hash
    config_hash = hashlib.sha256(
        json.dumps(config, sort_keys=True).encode()
    ).hexdigest()[:12]

    model = Ridge(**config["model_params"])
    model.fit(X_train, y_train)

    metrics = {
        "r2_test": float(model.score(X_test, y_test)),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }

    # Register: config + metrics + timestamp + data hash
    artifact_dir = Path(f"models/{config_hash}")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    json.dump({
        "config": config,
        "metrics": metrics,
        "trained_at": datetime.now().isoformat(),
        "code_version": get_git_hash(),
    }, open(artifact_dir / "manifest.json", "w"), indent=2)
    return model, config_hash
```

## Pipeline Stages

1. **Data Snapshot** -- versioned, immutable copy of training data
2. **Feature Build** -- deterministic feature pipeline, schema-validated
3. **Train** -- config-driven, seeded, reproducible
4. **Evaluate** -- challenger vs champion on holdout + live window
5. **Gate** -- automated: must beat champion by threshold
6. **Deploy** -- blue/green swap, monitoring active
7. **Monitor** -- drift detection, performance tracking, alerts

## Retraining Triggers

| Trigger | Detection | Action |
|---------|-----------|--------|
| Calendar | Weekly/monthly schedule | Full retrain |
| Drift | PSI > 0.25 on key features | Retrain + investigate |
| Performance | Rolling IC below 50% of baseline | Retrain with recent data |

## Champion-Challenger Protocol

Never deploy a new model without comparing it to the current one. Promote only if the challenger meaningfully beats the champion on the same holdout period (IC improvement > 0.005 and Sharpe improvement > 0.1).

## Guardrails

- Every model artifact must record: config, data hash, code version, training timestamp
- Retraining must be triggered by schedule or drift, never by "it feels stale"
- Champion-challenger comparison on the same holdout period, never different windows
- Rollback plan: keep previous N model versions, switch back in under 5 minutes
- Never deploy Friday afternoon — schedule retrains for Monday/Tuesday

## Checklist

- [ ] Training pipeline is automated and scheduled
- [ ] Every model artifact has config hash, data hash, and code version
- [ ] Champion-challenger evaluation runs before every deployment
- [ ] Drift detection triggers retraining automatically
- [ ] Rollback to previous model version possible in under 5 minutes
- [ ] Pipeline reproduces same model from same inputs (verified with seed)
