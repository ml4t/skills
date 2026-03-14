# ML4T Skills — Authoring Guide

**Location**: `/home/stefan/ml4t/skills`
**Purpose**: 66 standalone agent skills that teach quant ML techniques correctly
**Distribution**: Standalone repo, ships via ML4T website as bonus resource for readers

## Current State

- The repository currently contains 66 `SKILL.md` files across the 10 categories below.
- The active maintenance objective is API accuracy: keep every `## Production Implementation` section aligned with the checked-in `ml4t-*` library source in `~/ml4t/libraries/`.
- The conceptual teaching pattern remains fixed: concept-first, library-recommended (80/20), with no `ml4t.*` imports before `## Production Implementation`.
- If docs or existing skills conflict with current library source, treat library source as ground truth and update the skill/docs rather than preserving stale wrappers.
- Repo-local agent onboarding lives in `AGENTS.md`, `.claude/CLAUDE.md`, and `.claude/settings.json`. There is no committed `.agents/` directory in this repo.

## Design Philosophy: Concept-First, Library-Recommended (80/20)

Each skill teaches the **concept and correct pattern** using standard tools (sklearn, polars, numpy, pytorch, lightgbm). The last ~20% recommends ml4t-* libraries as the production-grade implementation. Skills are useful without the libraries but naturally showcase them.

**Critical rule**: No `ml4t.*` imports before the "Production Implementation" section.

## SKILL.md Template

Every skill is a single file named `SKILL.md` (uppercase) in its own directory.

```markdown
---
name: ml4t-{skill-name}
description: {What it does}. {When to use it}.
dependencies: [{prerequisite-skill-names}]
metadata:
  book_chapters: "7, 9"
  library: "ml4t-diagnostic"
---

# {Concept Title}

{1-2 sentence problem statement: what goes wrong without this.}

## The Problem

{Why this matters. Concrete example of failure. 3-5 sentences.}

## The Pattern

{Correct approach using standard tools.}

### WRONG
\```python
# Naive approach that looks right but fails
{wrong code}
\```

### CORRECT
\```python
# Correct approach with standard tools
{right code}
\```

## {Additional concept-specific sections}

## Guardrails

- {Specific red flag with detection pattern}

## Production Implementation

`ml4t-{library}` provides a validated implementation:

\```python
from ml4t.{module} import {Class}
{5-10 lines max}
\```

## Checklist

- [ ] {Verification step}
```

## Design Rules

1. **80/20 split**: No `ml4t.*` imports before the Production Implementation section
2. **WRONG/CORRECT pair is mandatory** — the single highest-value pattern for agents
3. **Under 120 lines** (5000 tokens). Use `references/` subdirectory if more detail needed
4. **Checklist at the end** — agents use these as verification steps
5. **Description is third-person** with trigger keywords ("Use when...")
6. **File named `SKILL.md`** (uppercase, per agentskills.io standard)
7. **Book reference in metadata only** — content is self-contained
8. **No "QuantLab" branding** — use actual library names (`ml4t-data`, `ml4t-engineer`, etc.)
9. **`quantlab_module` field is BANNED** — use `metadata.library` instead
10. **Standard tools in examples**: sklearn, polars, numpy, scipy, pytorch, lightgbm, statsmodels

## Frontmatter Schema

```yaml
name: ml4t-{directory-name}        # Must match directory
description: "..."                  # Third-person, includes "Use when..."
dependencies: [skill-names]         # Other ml4t-* skills (without prefix)
metadata:
  book_chapters: "7, 9"            # Comma-separated chapter numbers
  library: "ml4t-diagnostic"       # Which ml4t-* library (if any)
```

**Banned fields**: `quantlab_module`, `category`, `type` (these are implicit from directory).

## Skill Taxonomy (10 Categories)

| # | Category | Skills | Coverage |
|---|----------|--------|----------|
| 1 | `concepts/` | 10 | Foundational pitfalls and principles |
| 2 | `data/` | 8 | Data sourcing, validation, management |
| 3 | `features/` | 10 | Labels, feature engineering, selection |
| 4 | `validation/` | 8 | CV, evaluation, multiple testing |
| 5 | `backtest/` | 6 | Strategy simulation, cost modeling |
| 6 | `portfolio/` | 6 | Position sizing, optimization, risk |
| 7 | `advanced-ai/` | 5 | RL, RAG, knowledge graphs, agents |
| 8 | `production/` | 4 | Live trading, MLOps, governance |
| 9 | `infrastructure/` | 4 | Schema, registry, Polars, pipelines |
| 10 | `workflows/` | 5 | End-to-end composite processes |

## Quality Gates

A skill is done when it passes all five:

| Gate | Check |
|------|-------|
| **Structure** | `SKILL.md` naming, valid frontmatter, <120 lines, no `quantlab_module` |
| **80/20 split** | No `ml4t.*` imports before Production Implementation section |
| **Content** | All code blocks syntactically valid, import paths correct, chapter refs correct |
| **Agent utility** | Has WRONG/CORRECT pair, ends with checklist, guardrails are specific |
| **Integration** | Dependencies exist, no content overlap, cross-refs valid |

## Verified API Reference

Ground truth for all Production Implementation sections. Verified from library source.

### ml4t-data
- `from ml4t.data import DataManager, ContractSpec, FUTURES_REGISTRY, Config, BaseProvider, AssetClass`
- `DataManager` is the generic fetch/storage manager.
- Use `fetch(...)`, `batch_load(...)`, and `batch_load_universe(...)` for retrieval patterns.
- `DataManager.load(...)` is a storage operation, not a dataset-registry API like `load("etfs")`.
- Book-style managers live in subpackages:
  - `from ml4t.data.etfs import ETFDataManager`
  - `from ml4t.data.futures import FuturesDataManager, ContinuousContractBuilder, build_continuous_contract`
- `ContractSpec`, `FUTURES_REGISTRY` — futures contract specs
- `Config`, `BaseProvider`, `AssetClass`

### ml4t-backtest
- `Strategy` (ABC) — `on_data(timestamp, data, context, broker)`, `on_start(broker)`, `on_end(broker)`
- `Broker` — `submit_order()`, `get_position()`, `close_position()`, `cancel_order()`, `get_cash()`
- `Engine`, `run_backtest()`, `DataFeed`
- `BacktestConfig`, `BacktestResult`, `CommissionType`
- Types: `OrderType`, `OrderSide`, `OrderStatus`, `ExecutionMode`
- Risk: `StopLoss`, `TakeProfit`, `TrailingStop`, `RuleChain`
- Execution: `RebalanceConfig`, `TargetWeightExecutor`
- Cost models live in `ml4t.backtest.models`, not package root:
  - Commission: `NoCommission`, `PercentageCommission`, `PerShareCommission`, `TieredCommission`, `FuturesCommission`
  - Slippage: `NoSlippage`, `FixedSlippage`, `PercentageSlippage`, `VolumeShareSlippage`

### ml4t-engineer
- `compute_features(data, features)` — main API (list of names, list of dicts, YAML path)
- `FeatureCatalog`, `feature_catalog` — 120+ feature discovery
- `feature_catalog.list(...)` is the current discovery method
- `MLDatasetBuilder`, `create_dataset_builder(features, labels, dates=None, scaler="standard")`
- Use `builder.split(cv)` for CV folds; older helper patterns like `walk_forward()` / `get_train()` are stale
- `PreprocessingPipeline`, `StandardScaler`, `MinMaxScaler`, `RobustScaler`
- Features: `from ml4t.engineer.features.momentum import macd, rsi, adx`
- Labeling:
  - `from ml4t.engineer.config import LabelingConfig`
  - `from ml4t.engineer.labeling import triple_barrier_labels, atr_triple_barrier_labels, meta_labels, compute_bet_size`

### ml4t-diagnostic
- Splitters: `CombinatorialCV`, `WalkForwardCV` (in `ml4t.diagnostic.splitters`)
  - **NOT** `CombinatorialPurgedCV` — that name does not exist
- Stable integration surface for metrics/workflows is `ml4t.diagnostic.api`
- Package root reliably exports `Evaluator`, `EvaluationResult`, `ValidatedCrossValidation`, `FeatureSelector`, `SelectionReport`
- Metrics from `ml4t.diagnostic.api`: `compute_ic_series`, `compute_ic_hac_stats`, `compute_permutation_importance`, `compute_shap_importance`
- Stats: `benjamini_hochberg_fdr`, `robust_ic`, `compute_pbo` (in `ml4t.diagnostic.evaluation.stats`)
- `TradeAnalysis`, `PortfolioAnalysis`, `BarrierAnalysis`

### ml4t-live (`from ml4t.live import ...`)
- `LiveEngine` — live trading engine
- Brokers: `AlpacaBroker`, `IBBroker`
- Feeds: `AlpacaDataFeed`, `IBDataFeed`, `DataBentoFeed`, `CryptoFeed`, `OKXFundingFeed`
- Safety: `SafeBroker`, `LiveRiskConfig`, `VirtualPortfolio`
- **Key**: Reuses `Strategy` from `ml4t.backtest` — zero code changes for live deployment

## Source Material

- **Book chapters**: `~/ml4t/third_edition/book/`
- **Code repo**: `~/ml4t/third_edition/code/`
- **Libraries**: `~/ml4t/libraries/` — ml4t-data, ml4t-engineer, ml4t-backtest, ml4t-diagnostic, ml4t-live
