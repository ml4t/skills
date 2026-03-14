# ML4T Agent Skills

66 standalone skills that teach AI coding agents the Machine Learning for Trading workflow from [ML4T 3rd Edition](https://ml4trading.io).

## Current State

- This repo currently contains 66 `SKILL.md` files across 10 categories.
- The active maintenance goal is to keep every skill concept-first and every `## Production Implementation` section aligned with the current checked-in `ml4t-*` library source in `~/ml4t/libraries/`.
- Library source is the ground truth for API names and signatures. If a skill snippet conflicts with library source, the skill should be updated.
- The 80/20 invariant is mandatory: no `ml4t.*` imports before `## Production Implementation`.

## Agent Entry Points

- `AGENTS.md` is the repo-wide onboarding file for OpenAI/Codex-style agents.
- `.claude/CLAUDE.md` is the Claude-specific authoring guide.
- `CLAUDE.md` at repo root is a lightweight entry point that points new agents to the canonical repo guidance.
- `.claude/settings.json` contains Claude plugin settings.
- There is no repo-local `.agents/` directory checked in here.

## Design Philosophy

**Concept-first, library-recommended (80/20).** Each skill teaches the correct pattern using standard tools (sklearn, polars, numpy, pytorch, lightgbm). The last 20% recommends [ml4t-* libraries](https://ml4trading.io/libraries) as the production-grade implementation. Skills are useful without the libraries but naturally showcase them.

Every skill includes:
- **WRONG/CORRECT code pairs** — the single highest-value pattern for preventing agent mistakes
- **Guardrails** — specific red flags with detection patterns
- **Checklist** — actionable verification steps

## Skill Categories

| # | Category | Skills | Description |
|---|----------|--------|-------------|
| 1 | [`concepts/`](concepts/) | 10 | Foundational pitfalls: lookahead bias, data leakage, survivorship, overfitting |
| 2 | [`data/`](data/) | 8 | Data sourcing, validation, schema, bars, futures, calendars |
| 3 | [`features/`](features/) | 10 | Labels, feature engineering, selection, validation, microstructure |
| 4 | [`validation/`](validation/) | 8 | CPCV, walk-forward CV, IC evaluation, SHAP, deflated Sharpe |
| 5 | [`backtest/`](backtest/) | 6 | Event-driven simulation, tearsheets, cost models, sensitivity |
| 6 | [`portfolio/`](portfolio/) | 6 | Position sizing, optimization, risk metrics, stress testing |
| 7 | [`advanced-ai/`](advanced-ai/) | 5 | RL execution, RAG, knowledge graphs, agent orchestration |
| 8 | [`production/`](production/) | 4 | Live trading, MLOps, governance, monitoring |
| 9 | [`infrastructure/`](infrastructure/) | 4 | Canonical schema, registry, Polars patterns, pipelines |
| 10 | [`workflows/`](workflows/) | 5 | End-to-end strategy, factor research, model validation |

## Quick Start

Reference skills when working with an AI agent:

```
"Before computing features, review the lookahead-bias skill to avoid common mistakes"
```

Or invoke directly in Claude Code:

```
/ml4t-lookahead-bias
```

## Priority Skills

Start with these 5 skills that address the most common ML4T failures:

1. **[`concepts/lookahead-bias`](concepts/lookahead-bias/)** — Prevent using future information
2. **[`concepts/data-leakage`](concepts/data-leakage/)** — Avoid feature/target/CV contamination
3. **[`features/triple-barrier`](features/triple-barrier/)** — Volatility-adaptive trade labeling
4. **[`validation/cpcv`](validation/cpcv/)** — Combinatorial Purged Cross-Validation
5. **[`validation/purging-embargo`](validation/purging-embargo/)** — Time-series CV with temporal separation

## Full Skill Index

### Concepts (10)

| Skill | Description |
|-------|-------------|
| [lookahead-bias](concepts/lookahead-bias/) | Detect and prevent future information in features, labels, and evaluation |
| [data-leakage](concepts/data-leakage/) | Prevent train-test contamination, target leakage, temporal leakage |
| [survivorship-bias](concepts/survivorship-bias/) | Account for delisted securities in historical analysis |
| [point-in-time](concepts/point-in-time/) | Use data as available at decision time, not revised values |
| [non-stationarity](concepts/non-stationarity/) | Handle changing statistical properties in financial time series |
| [backtest-overfitting](concepts/backtest-overfitting/) | Detect and prevent overfitting to historical data |
| [information-coefficient](concepts/information-coefficient/) | Measure predictive power with IC, Rank IC, and the Fundamental Law |
| [transaction-costs](concepts/transaction-costs/) | Model spread, slippage, and market impact for realistic backtests |
| [regime-awareness](concepts/regime-awareness/) | Use regime-as-a-feature, not regime-switching timing |
| [strategy-term-sheet](concepts/strategy-term-sheet/) | Pre-register strategy hypotheses before backtesting |

### Data (8)

| Skill | Description |
|-------|-------------|
| [fetch-data](data/fetch-data/) | Reliable data acquisition with schema validation |
| [validate-data](data/validate-data/) | Data quality checks: gaps, outliers, types, staleness |
| [define-universe](data/define-universe/) | Point-in-time tradeable universe with liquidity filters |
| [build-bars](data/build-bars/) | Aggregate trades into time, volume, and dollar bars |
| [continuous-futures](data/continuous-futures/) | Roll futures contracts with back-adjustment |
| [synthetic-data](data/synthetic-data/) | Generate realistic financial data preserving temporal structure |
| [calendar-ops](data/calendar-ops/) | Trading calendar awareness and multi-frequency alignment |
| [data-export](data/data-export/) | Efficient storage with Parquet, partitioning, and versioning |

### Features (10)

| Skill | Description |
|-------|-------------|
| [triple-barrier](features/triple-barrier/) | Label trades using profit target, stop loss, and time barriers |
| [compute-features](features/compute-features/) | Systematic per-symbol feature computation with window functions |
| [feature-families](features/feature-families/) | Five families: momentum, mean-reversion, volatility, carry, value |
| [meta-labels](features/meta-labels/) | Two-stage labeling to filter which signals to act on |
| [regime-features](features/regime-features/) | Volatility, trend, and liquidity regime indicators |
| [microstructure-features](features/microstructure-features/) | Order flow signals: spread, VPIN, imbalance, illiquidity |
| [feature-selection](features/feature-selection/) | IC-based ranking and selection within CV folds |
| [feature-store](features/feature-store/) | Versioned feature storage with schema enforcement |
| [feature-validation](features/feature-validation/) | IC significance, stability, redundancy, and contamination tests |
| [horizon-design](features/horizon-design/) | Choose prediction horizon via IC decay analysis |

### Validation (8)

| Skill | Description |
|-------|-------------|
| [cpcv](validation/cpcv/) | Combinatorial Purged Cross-Validation for robust evaluation |
| [purging-embargo](validation/purging-embargo/) | Remove label overlap and add embargo buffers in time-series CV |
| [deflated-sharpe](validation/deflated-sharpe/) | Adjust Sharpe ratio for multiple testing |
| [walk-forward-cv](validation/walk-forward-cv/) | Rolling/expanding window validation |
| [evaluate-factor](validation/evaluate-factor/) | IC analysis, quantile spreads, turnover, and decay |
| [stationarity-tests](validation/stationarity-tests/) | ADF + KPSS testing before modeling |
| [drift-detection](validation/drift-detection/) | Detect feature, prediction, and concept drift with PSI |
| [shap-analysis](validation/shap-analysis/) | SHAP values for model interpretability |

### Backtest (6)

| Skill | Description |
|-------|-------------|
| [run-backtest](backtest/run-backtest/) | Event-driven backtesting with realistic execution |
| [tearsheet](backtest/tearsheet/) | Standard performance report with drawdown analysis |
| [vectorized-backtest](backtest/vectorized-backtest/) | Fast signal evaluation with matrix operations |
| [cost-model](backtest/cost-model/) | Multi-component cost model with capacity analysis |
| [regime-backtest](backtest/regime-backtest/) | Per-regime performance decomposition |
| [sensitivity-analysis](backtest/sensitivity-analysis/) | Parameter robustness testing |

### Portfolio (6)

| Skill | Description |
|-------|-------------|
| [position-sizing](portfolio/position-sizing/) | Volatility-targeted sizing and Kelly criterion |
| [portfolio-optimize](portfolio/portfolio-optimize/) | Mean-variance with shrinkage and practical constraints |
| [risk-metrics](portfolio/risk-metrics/) | Sharpe, Sortino, VaR, CVaR, drawdown analysis |
| [stress-test](portfolio/stress-test/) | Historical and hypothetical scenario testing |
| [exposure-analysis](portfolio/exposure-analysis/) | Factor, sector, and concentration decomposition |
| [kill-switch](portfolio/kill-switch/) | Automated risk limits that halt trading |

### Advanced AI (5)

| Skill | Description |
|-------|-------------|
| [rl-execution](advanced-ai/rl-execution/) | RL for adaptive trade execution |
| [rag-financial-research](advanced-ai/rag-financial-research/) | RAG systems for financial document analysis |
| [knowledge-graphs](advanced-ai/knowledge-graphs/) | Financial entity relationship modeling |
| [agent-orchestration](advanced-ai/agent-orchestration/) | Multi-agent trading system design |
| [agent-risk-controls](advanced-ai/agent-risk-controls/) | Safety controls for autonomous trading agents |

### Production (4)

| Skill | Description |
|-------|-------------|
| [live-trading](production/live-trading/) | Zero-code-change backtest-to-live deployment |
| [mlops-pipeline](production/mlops-pipeline/) | ML model lifecycle management |
| [model-governance](production/model-governance/) | Model risk management and compliance |
| [monitoring-alerting](production/monitoring-alerting/) | Real-time monitoring with automated alerts |

### Infrastructure (4)

| Skill | Description |
|-------|-------------|
| [canonical-schema](infrastructure/canonical-schema/) | Standardized column names: `symbol`, `timestamp`, `product` |
| [registry-system](infrastructure/registry-system/) | Content-addressed experiment tracking |
| [polars-patterns](infrastructure/polars-patterns/) | Polars-first patterns for financial data processing |
| [case-study-pipeline](infrastructure/case-study-pipeline/) | Structured ML pipeline from data to predictions |

### Workflows (5)

| Skill | Description |
|-------|-------------|
| [strategy-workflow](workflows/strategy-workflow/) | End-to-end strategy development lifecycle |
| [factor-research](workflows/factor-research/) | Systematic multi-factor evaluation process |
| [model-validation](workflows/model-validation/) | Multi-gate validation before deployment |
| [production-readiness](workflows/production-readiness/) | Pre-production checklist |
| [case-study-development](workflows/case-study-development/) | Complete case study from hypothesis to results |

## Supporting Libraries

Skills reference these production libraries in their "Production Implementation" sections:

| Library | Purpose | PyPI |
|---------|---------|------|
| `ml4t-data` | Data providers, schema enforcement | [ml4t-data](https://pypi.org/project/ml4t-data/) |
| `ml4t-engineer` | Feature engineering, labeling | [ml4t-engineer](https://pypi.org/project/ml4t-engineer/) |
| `ml4t-diagnostic` | Cross-validation, evaluation | [ml4t-diagnostic](https://pypi.org/project/ml4t-diagnostic/) |
| `ml4t-backtest` | Event-driven backtesting | [ml4t-backtest](https://pypi.org/project/ml4t-backtest/) |
| `ml4t-live` | Live trading, risk controls | [ml4t-live](https://pypi.org/project/ml4t-live/) |

Notes on current API usage:

- `ml4t-diagnostic.api` is the stable integration surface for IC metrics and validated CV workflows.
- Advanced `ml4t-diagnostic` helpers such as `analyze_stationarity`, `analyze_drift`, `compute_ic_by_horizon`, and `deflated_sharpe_ratio` live under `ml4t.diagnostic.evaluation.*`.
- `ml4t.backtest.models` contains commission and slippage classes.
- `ml4t.data.DataManager` is a generic fetch/storage manager; book-style loaders such as `ETFDataManager` and `FuturesDataManager` live in subpackages.
- `ml4t.data.DataManager.load(...)` is storage-backed ingest, not a dataset loader like `load("etfs")` or `load("us_equities")`.
- `ml4t.engineer.compute_features(...)` is best for single-series or per-symbol pipelines; panel-aware grouping still belongs in explicit Polars logic.
- `ml4t.engineer.store.OfflineFeatureStore` is DuckDB-backed and uses `point_in_time_join(...)` rather than a generic versioned-parquet `as_of` loader.

## Contributing

1. Create directory: `mkdir <category>/<skill-name>/`
2. Write `SKILL.md` following the template in `AGENTS.md` and `.claude/CLAUDE.md`
3. Verify against the 5 quality gates (structure, 80/20 split, content, utility, integration)
4. Ensure dependencies exist and the dependency graph is acyclic
