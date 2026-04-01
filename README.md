# ML4T Agent Skills

70 agent skills that teach AI coding assistants the Machine Learning for Trading workflow from [*Machine Learning for Algorithmic Trading, 3rd Edition*](https://ml4trading.io).

Each skill is a standalone `SKILL.md` file that an AI assistant can read and follow. Skills work with [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Codex](https://openai.com/index/codex/), and any agent that supports the [Agent Skills](https://agentskills.io) standard.

## Install

### Claude Code

```bash
# Clone into your user-level skills directory
git clone git@github.com:ml4t/skills.git ~/.claude/skills/ml4t
```

Skills are available in all your projects immediately. Claude Code loads skill descriptions at startup and activates the full instructions when a skill matches your task.

### Codex

```bash
# Clone into your project's agent skills directory
git clone git@github.com:ml4t/skills.git .agents/skills/ml4t
```

Codex discovers skills from `.agents/skills/` in any directory up to your repo root. Use `$skill-name` to invoke explicitly, or let Codex match skills implicitly from your prompt.

### Manual

Download a [release archive](https://github.com/ml4t/skills/releases) and copy the category directories into your agent's skill location.

## How Skills Work

Every skill follows the same structure:

1. **The Problem** -- what goes wrong without this knowledge
2. **WRONG code** -- the naive approach that looks right but fails
3. **CORRECT code** -- the right pattern using standard tools (sklearn, polars, numpy, pytorch)
4. **Guardrails** -- specific red flags to watch for
5. **Production Implementation** -- the `ml4t-*` library equivalent (optional, last 20%)
6. **Checklist** -- verification steps the agent can follow

Skills are useful without the ml4t libraries. The Production Implementation section shows how `ml4t-data`, `ml4t-engineer`, `ml4t-backtest`, `ml4t-diagnostic`, and `ml4t-live` handle the same pattern with validated, tested code.

## Skill Catalog

### Concepts (11) -- Foundational pitfalls and principles

| Skill | What it prevents |
|-------|-----------------|
| [lookahead-bias](concepts/lookahead-bias/) | Using future information in features, labels, or evaluation |
| [data-leakage](concepts/data-leakage/) | Train-test contamination via preprocessing or CV |
| [survivorship-bias](concepts/survivorship-bias/) | Excluding failed assets from historical analysis |
| [point-in-time](concepts/point-in-time/) | Using revised data that wasn't available at decision time |
| [non-stationarity](concepts/non-stationarity/) | Ignoring changing statistical properties in time series |
| [backtest-overfitting](concepts/backtest-overfitting/) | Reporting the best Sharpe from many trials without correction |
| [information-coefficient](concepts/information-coefficient/) | Misinterpreting or miscalculating factor predictive power |
| [transaction-costs](concepts/transaction-costs/) | Backtesting without realistic cost assumptions |
| [regime-awareness](concepts/regime-awareness/) | Treating regime as a timing signal instead of a conditioning feature |
| [strategy-term-sheet](concepts/strategy-term-sheet/) | Running backtests without a pre-registered hypothesis |
| [systematic-edge](concepts/systematic-edge/) | Skipping the disciplined process that separates signal from noise |

### Data (8) -- Data sourcing, validation, and management

| Skill | What it does |
|-------|-------------|
| [fetch-data](data/fetch-data/) | Schema-validated data loading with retry and gap detection |
| [validate-data](data/validate-data/) | OHLCV integrity checks, corporate action detection, staleness |
| [define-universe](data/define-universe/) | Point-in-time tradeable universe with liquidity filters |
| [build-bars](data/build-bars/) | Time, volume, and dollar bar construction from tick data |
| [continuous-futures](data/continuous-futures/) | Roll contracts with Panama canal or ratio back-adjustment |
| [synthetic-data](data/synthetic-data/) | GBM, GARCH, and bootstrap generators preserving time structure |
| [calendar-ops](data/calendar-ops/) | Trading calendar alignment across frequencies and exchanges |
| [data-export](data/data-export/) | Partitioned Parquet storage with schema versioning |

### Features (12) -- Labels, engineering, selection, and validation

| Skill | What it does |
|-------|-------------|
| [triple-barrier](features/triple-barrier/) | Volatility-adaptive trade labeling with profit/stop/time barriers |
| [compute-features](features/compute-features/) | Per-symbol windowed features without cross-contamination |
| [feature-families](features/feature-families/) | Momentum, mean-reversion, volatility, carry, and value features |
| [meta-labels](features/meta-labels/) | Secondary model to filter which primary signals to act on |
| [regime-features](features/regime-features/) | Stationary regime indicators (VIX percentile, vol z-score) |
| [microstructure-features](features/microstructure-features/) | Order flow signals: VPIN, Kyle's lambda, Amihud illiquidity |
| [feature-selection](features/feature-selection/) | IC ranking and selection within CV folds |
| [feature-store](features/feature-store/) | DuckDB-backed versioned storage with point-in-time joins |
| [feature-validation](features/feature-validation/) | IC stability, leakage screening, redundancy checks |
| [horizon-design](features/horizon-design/) | Choose prediction horizon via IC decay analysis |
| [text-features](features/text-features/) | NLP feature engineering with walk-forward model fitting |
| [latent-factors](features/latent-factors/) | PCA and autoencoder factors with Marchenko-Pastur noise filtering |

### Validation (8) -- Cross-validation, evaluation, and testing

| Skill | What it does |
|-------|-------------|
| [cpcv](validation/cpcv/) | Combinatorial Purged Cross-Validation for backtest robustness |
| [purging-embargo](validation/purging-embargo/) | Remove label overlap and add embargo buffers in time-series CV |
| [walk-forward-cv](validation/walk-forward-cv/) | Rolling or expanding window validation preserving temporal order |
| [deflated-sharpe](validation/deflated-sharpe/) | Adjust Sharpe ratio for the number of trials tested |
| [evaluate-factor](validation/evaluate-factor/) | IC analysis, quantile spreads, turnover, and signal decay |
| [stationarity-tests](validation/stationarity-tests/) | ADF + KPSS decision matrix for feature stationarity |
| [drift-detection](validation/drift-detection/) | PSI and rolling IC to detect feature and concept drift |
| [shap-analysis](validation/shap-analysis/) | SHAP values for feature importance and model explanation |

### Backtest (6) -- Strategy simulation and analysis

| Skill | What it does |
|-------|-------------|
| [run-backtest](backtest/run-backtest/) | Event-driven backtesting with Strategy/Broker/Engine pattern |
| [tearsheet](backtest/tearsheet/) | Performance reports with cumulative returns, drawdowns, rolling Sharpe |
| [vectorized-backtest](backtest/vectorized-backtest/) | Fast signal evaluation with shift-aligned returns |
| [cost-model](backtest/cost-model/) | Commission, slippage, and market impact stacking |
| [regime-backtest](backtest/regime-backtest/) | Per-regime performance decomposition |
| [sensitivity-analysis](backtest/sensitivity-analysis/) | Parameter sweep with robustness scoring and cliff detection |

### Portfolio (6) -- Position sizing, optimization, and risk

| Skill | What it does |
|-------|-------------|
| [position-sizing](portfolio/position-sizing/) | Volatility targeting and Kelly criterion with half-Kelly default |
| [portfolio-optimize](portfolio/portfolio-optimize/) | Mean-variance with shrinkage, risk parity, and Black-Litterman |
| [risk-metrics](portfolio/risk-metrics/) | Sharpe, Sortino, VaR, CVaR, max drawdown, Calmar |
| [stress-test](portfolio/stress-test/) | Historical and hypothetical scenario analysis |
| [exposure-analysis](portfolio/exposure-analysis/) | Factor, sector, and concentration decomposition |
| [kill-switch](portfolio/kill-switch/) | Automated drawdown and loss limits that halt trading |

### Advanced AI (6) -- Deep learning, RL, and agent systems

| Skill | What it does |
|-------|-------------|
| [rl-execution](advanced-ai/rl-execution/) | RL-based adaptive trade execution beyond TWAP/VWAP |
| [rag-financial-research](advanced-ai/rag-financial-research/) | RAG pipelines for SEC filings and financial documents |
| [knowledge-graphs](advanced-ai/knowledge-graphs/) | Entity relationship modeling for supply chain and sector analysis |
| [agent-orchestration](advanced-ai/agent-orchestration/) | Multi-agent trading system design with protocol-based coordination |
| [agent-risk-controls](advanced-ai/agent-risk-controls/) | Defense-in-depth safety controls for autonomous trading agents |
| [dl-time-series](advanced-ai/dl-time-series/) | Deep learning baselines with walk-forward discipline |

### Production (4) -- Live trading and operations

| Skill | What it does |
|-------|-------------|
| [live-trading](production/live-trading/) | Zero-code-change transition from backtest to live via broker APIs |
| [mlops-pipeline](production/mlops-pipeline/) | Model versioning, retraining triggers, and deployment pipelines |
| [model-governance](production/model-governance/) | Risk tiering, review gates, and audit trails |
| [monitoring-alerting](production/monitoring-alerting/) | Real-time data staleness, drawdown, and fill rate monitoring |

### Infrastructure (4) -- Data standards and patterns

| Skill | What it does |
|-------|-------------|
| [canonical-schema](infrastructure/canonical-schema/) | Standard columns (`symbol`, `timestamp`) enforced at load time |
| [registry-system](infrastructure/registry-system/) | Content-addressed experiment and artifact tracking |
| [polars-patterns](infrastructure/polars-patterns/) | Polars idioms for financial panel data |
| [case-study-pipeline](infrastructure/case-study-pipeline/) | Structured ML pipeline from data through predictions |

### Workflows (5) -- End-to-end composite processes

| Skill | What it does |
|-------|-------------|
| [strategy-workflow](workflows/strategy-workflow/) | Full strategy lifecycle: idea, backtest, validate, deploy |
| [factor-research](workflows/factor-research/) | Systematic multi-factor evaluation from IC through portfolio |
| [model-validation](workflows/model-validation/) | Multi-gate validation: statistical, economic, operational |
| [production-readiness](workflows/production-readiness/) | Pre-deployment checklist: data, model, risk, monitoring |
| [case-study-development](workflows/case-study-development/) | Complete case study from hypothesis to documented results |

## ML4T Libraries

Skills reference these Python packages in their Production Implementation sections. Install them via pip:

```bash
pip install ml4t-data ml4t-engineer ml4t-backtest ml4t-diagnostic ml4t-live
```

| Package | Purpose |
|---------|---------|
| [ml4t-data](https://pypi.org/project/ml4t-data/) | Data providers, schema enforcement, futures contracts |
| [ml4t-engineer](https://pypi.org/project/ml4t-engineer/) | Feature computation, labeling, feature store |
| [ml4t-backtest](https://pypi.org/project/ml4t-backtest/) | Event-driven backtesting with cost models |
| [ml4t-diagnostic](https://pypi.org/project/ml4t-diagnostic/) | Cross-validation, IC analysis, drift detection |
| [ml4t-live](https://pypi.org/project/ml4t-live/) | Live trading with SafeBroker risk controls |

The libraries are optional. Every skill teaches the concept with standard tools first.

## Book

These skills distill techniques from [*Machine Learning for Algorithmic Trading*](https://ml4trading.io) (3rd Edition) by Stefan Jansen. Each skill's `metadata.book_chapters` field maps to the relevant chapters.

## Contributing

1. Create a directory: `mkdir <category>/<skill-name>/`
2. Write `SKILL.md` following the template in [`AGENTS.md`](AGENTS.md)
3. Verify the 5 quality gates: structure, 80/20 split, content accuracy, agent utility, integration
4. All `from ml4t.*` imports must be in `## Production Implementation` only
5. Keep skills under 120 lines

## License

Copyright (c) 2026 Stefan Jansen. All rights reserved.
