---
name: ml4t-registry-system
description: Content-addressed experiment tracking for ML trading models. Use when running model experiments and need reproducibility, comparison, and audit trail across training runs.
dependencies: []
metadata:
  book_chapters: "11, 12"
  library: ""
---

# Experiment Registry

Without a registry, you overwrite the best model every time you retrain. Content-addressed storage — where hash(config) determines the storage path — makes every experiment reproducible and comparable without manual bookkeeping.

## The Problem

A quant runs 50 model configurations. Results go into `model_v2_final_FINAL.pkl`. Next week, a new run overwrites it. The team cannot answer: which hyperparameters produced the best IC? Was that before or after the feature change? Did we already try alpha=0.01? Without structured tracking, experiments are lost, repeated, and unverifiable.

## The Pattern

### WRONG
```python
import pickle

# Overwrite on every run — no history, no comparison, no provenance
model.fit(X_train, y_train)
with open("best_model.pkl", "wb") as f:
    pickle.dump(model, f)

# Three weeks later: "Which config was this? What data did it use?"
```

### CORRECT
```python
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

def config_hash(config: dict) -> str:
    """Deterministic hash of experiment config."""
    blob = json.dumps(config, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:12]

def register_run(db_path: str, config: dict, metrics: dict, predictions_path: str):
    """Register a training run with full provenance."""
    run_hash = config_hash(config)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS training_runs (
            run_hash TEXT PRIMARY KEY,
            config JSON NOT NULL,
            metrics JSON NOT NULL,
            predictions_path TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute(
        "INSERT OR REPLACE INTO training_runs VALUES (?, ?, ?, ?, ?)",
        (run_hash, json.dumps(config), json.dumps(metrics),
         predictions_path, datetime.now().isoformat()),
    )
    conn.commit()
    return run_hash

# Usage: every config gets a unique, reproducible slot
config = {"model": "ridge", "alpha": 1.0, "features": "momentum_v2"}
run_hash = register_run("registry.db", config, {"ic": 0.04}, f"runs/{config_hash(config)}/predictions.parquet")
# Re-running same config overwrites same slot — idempotent
```

## Registry Schema

Three linked tables capture the full experiment lifecycle:

```
training_runs          prediction_sets         backtest_runs
+------------+        +----------------+       +--------------+
| run_hash   |<------>| pred_hash      |<----->| bt_hash      |
| config     |   1:N  | run_hash (FK)  |  1:N  | pred_hash(FK)|
| metrics    |        | fold           |       | config       |
| created_at |        | path           |       | metrics      |
+------------+        +----------------+       +--------------+
```

- **training_runs**: one row per unique model config (hash of hyperparams)
- **prediction_sets**: one row per fold or time split within a training run
- **backtest_runs**: one row per strategy config applied to a prediction set

## Content-Addressed Storage

```
run_log/
  registry.db              # SQLite: all metadata
  models/{config_hash}/    # hash(config) -> directory
    config.json
    metrics.json
    predictions.parquet
```

The hash is the directory name. Same config always maps to the same directory. No manual naming, no collisions, no "v2_final" suffixes. Query the registry with standard SQL against `registry.db`.

## Guardrails

- Hash must be deterministic: `json.dumps(config, sort_keys=True)` — without `sort_keys`, same config produces different hashes
- Register per-config as they complete, not in bulk after all finish — a crash at config 49 of 50 loses everything otherwise
- Never store model weights in the SQLite database — store paths to artifacts on disk
- Config must capture everything needed to reproduce: model type, hyperparameters, feature version, data version, random seed
- Old runs are never deleted — mark as superseded, keep for audit trail

## Checklist

- [ ] Every experiment has a deterministic config hash
- [ ] Registry stores config, metrics, and artifact paths (not weights in DB)
- [ ] Runs registered incrementally (per-config, not bulk)
- [ ] Same config re-run maps to same hash (idempotent)
- [ ] Top-N query by any metric works against the registry
- [ ] Full provenance: model type, hyperparams, feature version, data version, seed
