# ML4T Agent Skills — External Review Prompt

## Your Role

You are reviewing a collection of 66 agent skills for Machine Learning for Trading (ML4T). These skills teach AI coding agents the correct patterns for quantitative ML — preventing common mistakes like lookahead bias, data leakage, overfitting to backtests, and incorrect cross-validation.

Your job is to identify issues across five dimensions: **content correctness**, **book alignment**, **API accuracy**, **skill design quality**, and **structural compliance**. If a skill is wrong, say so. If the book content it references is wrong, say that too. Do not rubber-stamp.

---

## What Was Built

**66 standalone SKILL.md files** organized into 10 categories:

| # | Category | Count | Scope |
|---|----------|-------|-------|
| 1 | `concepts/` | 10 | Foundational pitfalls: lookahead bias, data leakage, survivorship, overfitting |
| 2 | `data/` | 8 | Data sourcing, validation, schema, bars, futures, calendars |
| 3 | `features/` | 10 | Labels, feature engineering, selection, validation, microstructure |
| 4 | `validation/` | 8 | CPCV, walk-forward CV, IC evaluation, SHAP, deflated Sharpe |
| 5 | `backtest/` | 6 | Event-driven simulation, tearsheets, cost models, sensitivity |
| 6 | `portfolio/` | 6 | Position sizing, optimization, risk metrics, stress testing |
| 7 | `advanced-ai/` | 5 | RL execution, RAG, knowledge graphs, agent orchestration |
| 8 | `production/` | 4 | Live trading, MLOps, governance, monitoring |
| 9 | `infrastructure/` | 4 | Canonical schema, registry, Polars patterns, pipelines |
| 10 | `workflows/` | 5 | End-to-end strategy, factor research, model validation |

**Repository**: `~/ml4t/skills/`
**Book**: ML4T 3rd Edition (27 chapters covering quant ML from data through production)

---

## Design Philosophy: Concept-First, Library-Recommended (80/20)

Each skill teaches the **concept and correct pattern** using standard tools (sklearn, polars, numpy, scipy, statsmodels, pytorch, lightgbm). The last ~20% recommends `ml4t-*` libraries as the production-grade implementation.

**Critical invariant**: No `from ml4t.` or `import ml4t` imports may appear before the `## Production Implementation` section. Skills that have no corresponding ml4t library (indicated by `metadata.library: ""`) omit the Production Implementation section entirely — this is correct.

**Why this design**: An agent without the ml4t libraries should still get full value from the skill. The libraries are recommended, not required.

---

## The Template Every Skill Must Follow

```markdown
---
name: ml4t-{skill-name}
description: {What it does}. {When to use it — "Use when..."}.
dependencies: [{prerequisite-skill-names}]
metadata:
  book_chapters: "7, 9"
  library: "ml4t-diagnostic"   # or "" if no library
---

# {Concept Title}

{1-2 sentence problem statement: what goes wrong without this.}

## The Problem

{Why this matters. Concrete failure example. 3-5 sentences.}

## The Pattern

### WRONG
```python
# Naive approach that looks right but fails
```

### CORRECT
```python
# Correct approach using standard tools only (no ml4t.* imports)
```

## {Additional concept-specific sections as needed}

## Guardrails

- {Specific red flag with detection pattern}

## Production Implementation   ← ONLY if metadata.library is non-empty

`ml4t-{library}` provides a validated implementation:

```python
from ml4t.{module} import {Class}
{5-10 lines max}
```

## Checklist

- [ ] {Verification step}
```

### Design Rules

1. **80/20 split**: No `ml4t.*` imports before the Production Implementation section
2. **WRONG/CORRECT pair is mandatory** — the single highest-value pattern for agents
3. **Under 120 lines** (~5000 tokens target). 500 lines is the hard maximum per agentskills.io
4. **Checklist at the end** — agents use these as verification steps
5. **Description is third-person** with trigger keywords ("Use when...")
6. **File named `SKILL.md`** (uppercase, per agentskills.io standard)
7. **Book reference in metadata only** — content must be self-contained
8. **No "QuantLab" branding** — use actual library names (`ml4t-data`, etc.)
9. **`quantlab_module` field is BANNED** — use `metadata.library` instead
10. **Standard tools in examples**: sklearn, polars, numpy, scipy, pytorch, lightgbm, statsmodels

### Banned Frontmatter Fields

`quantlab_module`, `category`, `type` — these are all implicit from the directory structure.

---

## Verified API Reference (Ground Truth)

These class and method names were verified by reading actual library source code. Any Production Implementation section that uses names not on this list is wrong.

### ml4t-data
- `from ml4t.data import DataManager, ContractSpec, FUTURES_REGISTRY, Config, BaseProvider, AssetClass`
- `DataManager` is the generic fetch/storage manager.
- Use `fetch(...)`, `batch_load(...)`, and `batch_load_universe(...)` for retrieval patterns.
- `DataManager.load(...)` is a storage operation, not a dataset-registry API like `load("etfs")`.
- There is no generic `load("us_equities")` or `load(datasets=[...], as_of_date=...)` API in the library.
- Book-style managers live in subpackages:
  - `from ml4t.data.etfs import ETFDataManager`
  - `from ml4t.data.futures import FuturesDataManager, ContinuousContractBuilder, build_continuous_contract`
- `WikiPricesProvider` is the survivorship-bias-free historical US equities source through 2018.
- `FREDProvider.fetch_ohlcv(..., vintage_date=...)` is the current point-in-time macro API.
- `ContractSpec`, `FUTURES_REGISTRY` — futures contract specs
- `Config`, `BaseProvider`, `AssetClass`

### ml4t-backtest (`from ml4t.backtest import ...`)
- `Strategy` (ABC) — methods: `on_data(timestamp, data, context, broker)`, `on_start(broker)`, `on_end(broker)`
  - **NOT `on_bar()`** — that name does not exist
- `Broker` — `submit_order()`, `get_position()`, `close_position()`, `cancel_order()`, `get_cash()`
- `Engine`, `run_backtest()`, `DataFeed`
- `BacktestConfig`, `BacktestResult`, `CommissionType`
- Current engine usage: `Engine(feed, strategy, config).run()` or `run_backtest(prices=..., strategy=..., signals=..., context=..., config=...)`
- `BacktestConfig` uses primitive commission/slippage fields like `commission_type`, `commission_rate`, `slippage_type`, `slippage_rate`
- `BacktestResult` metrics live under `result.metrics[...]`; use export helpers like `to_equity_dataframe()`, `to_daily_returns()`, and `to_tearsheet()`
- Types: `OrderType`, `OrderSide`, `OrderStatus`, `ExecutionMode`
- Risk: `StopLoss`, `TakeProfit`, `TrailingStop`, `RuleChain`
- Execution: `RebalanceConfig`, `TargetWeightExecutor`
- Commission: `NoCommission`, `PercentageCommission`, `PerShareCommission`, `TieredCommission`, `FuturesCommission`
- Slippage: `NoSlippage`, `FixedSlippage`, `PercentageSlippage`, `VolumeShareSlippage`

### ml4t-engineer (`from ml4t.engineer import ...`)
- `compute_features(data, features)` — main API (accepts list of names, list of dicts, or YAML path)
- `FeatureCatalog`, `feature_catalog` — 120+ feature discovery
- `feature_catalog.list(...)` is the current discovery method
- `MLDatasetBuilder`, `create_dataset_builder(features, labels, dates=None, scaler="standard")`
- Use `builder.split(cv)` for CV folds; older helper patterns like `walk_forward()` / `get_train()` are stale
- Registry feature names are canonical names like `mom`, `rsi`, `realized_volatility`, `adx`
- `compute_features(...)` is safest for single-series or per-symbol pipelines; do not assume it automatically partitions panel data by symbol
- `PreprocessingPipeline`, `StandardScaler`, `MinMaxScaler`, `RobustScaler`
- Feature submodules: `from ml4t.engineer.features.momentum import macd, rsi, adx`
- Labeling:
  - `from ml4t.engineer.config import LabelingConfig`
  - `from ml4t.engineer.labeling import triple_barrier_labels, atr_triple_barrier_labels, meta_labels, compute_bet_size`
- Storage:
  - `from ml4t.engineer.store import OfflineFeatureStore`
  - Current store API is DuckDB-backed: `save_features(...)`, `load_features(...)`, `point_in_time_join(...)`

### ml4t-diagnostic (`from ml4t.diagnostic import ...`)
- Splitters (in `ml4t.diagnostic.splitters`):
  - `CombinatorialCV` — **NOT `CombinatorialPurgedCV`** (that name does not exist)
  - `WalkForwardCV`
- Stable integration surface for metrics/workflows is `ml4t.diagnostic.api`
- Package root reliably exports `Evaluator`, `EvaluationResult`, `ValidatedCrossValidation`, `FeatureSelector`, `SelectionReport`
- Metrics from `ml4t.diagnostic.api`: `compute_ic_series`, `compute_ic_hac_stats`, `compute_permutation_importance`, `compute_shap_importance`
- Advanced evaluation helpers live under submodules:
  - `ml4t.diagnostic.evaluation.metrics`: `compute_ic_by_horizon`
  - `ml4t.diagnostic.evaluation.stationarity`: `analyze_stationarity`
  - `ml4t.diagnostic.evaluation.drift`: `analyze_drift`
  - `ml4t.diagnostic.evaluation.stats`: `benjamini_hochberg_fdr`, `robust_ic`, `compute_pbo`, `deflated_sharpe_ratio`, `deflated_sharpe_ratio_from_statistics`
- Analysis: `TradeAnalysis`, `PortfolioAnalysis`, `BarrierAnalysis`, `TradeShapAnalyzer`, `FeatureDiagnostics`, `FactorAnalysis`

### ml4t-live (`from ml4t.live import ...`)
- `LiveEngine` — live trading engine
- Brokers: `AlpacaBroker`, `IBBroker`
- Feeds: `AlpacaDataFeed`, `IBDataFeed`, `DataBentoFeed`, `CryptoFeed`, `OKXFundingFeed`
- Safety: `SafeBroker`, `LiveRiskConfig`, `VirtualPortfolio`
- **Key design**: Reuses `Strategy` from `ml4t.backtest` — zero code changes from backtest to live

---

## What You Should Check

### 1. Content Correctness (Most Important)

For each skill, evaluate whether the **WRONG code actually demonstrates a real mistake** and the **CORRECT code actually fixes it**. Specifically:

- **Is the WRONG pattern genuinely wrong?** Not just "suboptimal" — it should produce incorrect results or silently introduce bias. If the WRONG pattern is actually fine in many contexts, the skill is misleading agents.
- **Is the CORRECT pattern genuinely correct?** Does it actually solve the problem the skill claims to address? Are there edge cases where it would still fail?
- **Is the problem statement accurate?** Does lookahead bias really inflate Sharpe by 0.5-2.0? Does survivorship bias really add 1-2% per year? Are the quantitative claims defensible?
- **Are the code examples syntactically valid Python?** Would they run (given appropriate data)?
- **Are standard library APIs used correctly?** e.g., `sklearn.model_selection.KFold`, `scipy.stats.spearmanr`, `polars` expressions, `statsmodels` tests.
- **Are financial concepts correct?** e.g., Is the triple-barrier labeling method described accurately? Is the Deflated Sharpe Ratio formula correct? Is the CPCV combinatorial logic right?

**Flag if**: A WRONG example is actually acceptable practice, a CORRECT example has a bug, a quantitative claim is unsupported, or a financial concept is misrepresented.

### 2. Book Alignment

Each skill references specific book chapters via `metadata.book_chapters`. Check:

- **Do the chapter numbers make sense?** e.g., a skill about cross-validation should reference Ch7 (Defining the Learning Task) or Ch11 (ML Pipeline), not Ch2 (Financial Data).
- **Does the skill's content match what the book actually teaches?** The book may teach a technique differently than how the skill presents it. If so, which is correct?
- **If the book is wrong, flag it.** The book is in its 3rd edition and some techniques have evolved. If a skill corrects the book (intentionally or not), that should be noted.

Book chapter mapping for reference:
```
Ch1:  Process Is Edge (philosophy)
Ch2:  Financial Data Universe (data sources, schema)
Ch3:  Market Microstructure (tick data, order books)
Ch4:  Fundamental & Alternative Data
Ch5:  Synthetic Data (GAN, simulation)
Ch6:  Strategy Definition (universe, setup, hypothesis)
Ch7:  Defining the Learning Task (labels, CV, evaluation, multiple testing)
Ch8:  Feature Engineering (momentum, volatility, carry, value features)
Ch9:  Time Series Analysis (ARIMA, GARCH, HMM)
Ch10: Text Feature Engineering (NLP, embeddings)
Ch11: ML Pipeline (linear models, regularization)
Ch12: Advanced Tabular Models (GBM, TabDL)
Ch13: Deep Learning for Time Series
Ch14: Latent Factors (PCA, autoencoders, SDF)
Ch15: Causal Estimation
Ch16: Strategy Simulation (backtesting)
Ch17: Portfolio Construction
Ch18: Transaction Costs
Ch19: Risk Management
Ch20: Strategy Synthesis
Ch21-24: Advanced AI (RL, RAG, KG, Agents)
Ch25-27: Production (Live, MLOps, Governance)
```

### 3. API Accuracy

Every `## Production Implementation` section must use class/method names from the verified API reference above. Check:

- **Does every import path resolve?** e.g., `from ml4t.diagnostic.splitters import CombinatorialCV` is correct; `from ml4t.diagnostic import CombinatorialPurgedCV` is wrong.
- **Are method signatures plausible?** e.g., `CombinatorialCV(n_groups=8, n_test_groups=2, embargo_pct=0.01)` — do these parameter names match the actual API?
- **Is `on_data()` used (not `on_bar()`)?** The Strategy ABC uses `on_data`, not `on_bar`.
- **Are any fabricated classes or functions present?** If a class name doesn't appear in the verified API reference, it may be hallucinated.

**Flag if**: An import path is wrong, a class name doesn't exist, a method name is fabricated, or parameter names don't match the real API.

### 4. Skill Design Quality (agentskills.io Best Practices)

From the official Claude/agentskills.io skill authoring guidelines:

- **Conciseness**: Every token should earn its place. Is the skill bloated with explanations Claude already knows? Could sections be shorter without losing information?
- **Degrees of freedom**: WRONG/CORRECT is low-freedom (good for fragile correctness patterns). Guardrails are medium-freedom. Is the freedom level appropriate?
- **Description quality**: Third-person, includes "Use when..." trigger, specific enough to activate on relevant prompts, not so broad it activates on irrelevant ones.
- **Progressive disclosure**: SKILL.md should be self-contained. References to external files are acceptable via `references/` subdirectories but shouldn't be required.
- **No time-sensitive information**: Skills shouldn't reference specific dates or versions that will become stale.
- **Consistent terminology**: Does the skill use one term consistently (e.g., always "symbol" not alternating with "ticker")?
- **Actionable guardrails**: Are guardrails specific enough to detect ("Sharpe > 2 on daily data → investigate") rather than vague ("be careful")?
- **Useful checklist**: Would an agent actually use these items to verify its work?

**Flag if**: A skill is over-explained, under-explained, has vague guardrails, has a useless checklist item, or has a description that would cause false triggers.

### 5. Structural Compliance

Mechanical checks (most can be automated):

- [ ] File is named `SKILL.md` (uppercase)
- [ ] Valid YAML frontmatter with: `name`, `description`, `dependencies`, `metadata.book_chapters`, `metadata.library`
- [ ] `name` matches `ml4t-{directory-name}`
- [ ] No banned fields: `quantlab_module`, `category`, `type`
- [ ] Has `## The Problem` section
- [ ] Has `### WRONG` and `### CORRECT` subsections under `## The Pattern`
- [ ] Has `## Guardrails` section
- [ ] Has `## Checklist` section with `- [ ]` items
- [ ] No `ml4t.*` imports before `## Production Implementation` (80/20 rule)
- [ ] Under 500 lines (target: ~120 lines)
- [ ] All dependencies listed in frontmatter have corresponding directories
- [ ] If `metadata.library` is non-empty, a `## Production Implementation` section exists
- [ ] If `metadata.library` is empty (`""`), no Production Implementation section is needed

---

## How to Report Findings

For each issue found, report:

```
### [CATEGORY] skill-path — Brief Issue Title

**Severity**: CRITICAL / MAJOR / MINOR / SUGGESTION
**Gate**: Content / Book Alignment / API / Design / Structure

Description of the issue.

**Current** (what the skill says):
> quoted text or code

**Expected** (what it should say):
> corrected text or code

**Rationale**: Why this is wrong and how you know.
```

Severity guide:
- **CRITICAL**: Would cause an agent to produce incorrect code or apply a wrong technique. Must fix before publication.
- **MAJOR**: Meaningful quality issue — misleading claim, wrong API name, significant omission. Should fix.
- **MINOR**: Imprecise wording, suboptimal example, style inconsistency. Nice to fix.
- **SUGGESTION**: Enhancement idea, not a defect.

---

## Review Approach

**Recommended order** (highest impact first):

1. **Priority 5 skills** (most commonly used, highest stakes):
   - `concepts/lookahead-bias`
   - `concepts/data-leakage`
   - `features/triple-barrier`
   - `validation/cpcv`
   - `validation/purging-embargo`

2. **All `concepts/` skills** (10) — foundational, all other skills build on these

3. **`validation/` and `features/` skills** (18) — where most technical mistakes happen

4. **`backtest/` and `portfolio/` skills** (12) — where financial domain knowledge matters most

5. **Everything else** (26) — `data/`, `advanced-ai/`, `production/`, `infrastructure/`, `workflows/`

For each skill:
1. Read the full SKILL.md
2. Check content correctness (WRONG/CORRECT patterns)
3. Verify API accuracy in Production Implementation
4. Assess description quality and checklist usefulness
5. Verify structural compliance
6. Record any issues found

---

## Source Material for Verification

If you have access to the following, use them to verify content:

- **Book chapters**: `~/ml4t/third_edition/book/` — chapter prose and sections
- **Code repo**: `~/ml4t/third_edition/code/` — canonical publication notebooks
- **Library source**: `~/ml4t/libraries/` — actual Python source for ml4t-data, ml4t-engineer, ml4t-backtest, ml4t-diagnostic, ml4t-live
- **Case studies**: `~/ml4t/third_edition/code/case_studies/` — 9 end-to-end ML pipelines

If you do NOT have access to these, note in your review which findings are "high confidence" (based on general quant ML knowledge) vs "needs verification" (requires checking against specific book content or library source).

---

## Output Format

Produce a structured review report with:

1. **Executive Summary**: Overall quality assessment, number of issues by severity
2. **Per-Skill Findings**: Grouped by category, one entry per issue found
3. **Cross-Cutting Observations**: Patterns that affect multiple skills (e.g., "all backtest skills use the same wrong commission model parameter name")
4. **Skills Approved Without Issues**: List skills that pass all checks cleanly
5. **Recommendations**: Prioritized list of fixes

---

## Important Notes

- These skills are designed for **AI coding agents**, not human developers. The audience is Claude, GPT, Codex, etc. The skills should be optimized for how agents consume instructions, not how humans read documentation.
- The canonical data schema uses `symbol` as the entity identifier and `timestamp` as the time column. Exception: CME futures use `product` instead of `symbol`. Skills should reflect this.
- The `ml4t-*` libraries are real, published on PyPI, and maintained alongside the book. They are not hypothetical.
- Some skills legitimately have `metadata.library: ""` because no ml4t library covers that topic. This is not an error.
