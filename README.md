# ML4T Agent Skills

[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

61 standalone skills that teach AI coding assistants the Machine Learning for Trading workflow from [*Machine Learning for Algorithmic Trading, 3rd Edition*](https://ml4trading.io).

This repository turns the book's quant research discipline into runtime guidance for coding agents. Each skill gives an agent the pattern it needs to avoid common ML4T failures: leakage, lookahead bias, overfit backtests, stale data joins, broken cross-validation, unrealistic transaction costs, and unsafe autonomous workflows.

Each skill is a plain `SKILL.md` file with YAML frontmatter and concise procedural guidance. Installing them means putting each individual skill directory where your agent looks for skills, which `scripts/install.sh` does from a clone or from an unpacked [release archive](https://github.com/ml4t/skills/releases).

<!-- offerings:next start -->
> **Next free session:** [Managing Your Strategy Research Process](https://maven.com/p/bc9fd4), a 30-minute live session on **Wednesday, September 2, 2026, 12:00 PM ET / 16:00 UTC**. [All courses, workshops, and free lessons](https://ml4trading.io/courses/?utm_source=github&utm_medium=readme&utm_campaign=skills&utm_content=offerings).
<!-- offerings:next end -->

## Why Use These Skills

Coding agents are strong at writing code, but financial ML has failure modes that are easy to miss and expensive to discover late. These skills package the reviewer-grade checks that should happen before a strategy result is trusted:

- **Method discipline**: every skill teaches a concept-first WRONG/CORRECT pattern.
- **Book alignment**: skills map to the chapters and case-study workflow in *Machine Learning for Algorithmic Trading*.
- **Production handoff**: stable patterns point to the corresponding `ml4t-data`, `ml4t-engineer`, `ml4t-backtest`, `ml4t-diagnostic`, or `ml4t-live` API.
- **Agent portability**: the files are standard Markdown and can be used by Claude Code, Codex/OpenAI agents, or any tool that can discover and read local skill files.

## Installation

The canonical distribution is this Git repository. There is no npm package, Python package, or build step, because the runtime artifact is the Markdown file itself.

Agents discover skills one directory level deep, at `<skills-dir>/<skill-name>/SKILL.md`. This repository groups skills into category directories so it can be read, so cloning it into a skills directory as a single folder will not work: the `SKILL.md` files end up three levels down and nothing finds them. `scripts/install.sh` flattens the categories for you.

```bash
git clone https://github.com/ml4t/skills.git ~/.ml4t-skills
cd ~/.ml4t-skills

./scripts/install.sh                    # ~/.claude/skills, the default
./scripts/install.sh .agents/skills     # Codex, project-local
./scripts/install.sh ~/.claude/skills --copy   # copies instead of symlinking
```

The script symlinks each skill in as `ml4t-<skill-name>`, so `git pull` updates every installed skill at once, and the `ml4t-` prefix keeps them from colliding with skills you already have. It is idempotent and never overwrites a directory it did not create. Pass `--copy` when the install must not depend on the checkout.

Copying by hand works too. Move each of the 61 skill directories, not the category directories, into your agent's skills directory.

### What these files can do

Nothing on their own. Every skill in this repository is Markdown: no executable scripts, no hooks, no MCP servers, no network calls. An empirical study of 31,132 public skills found that [26.1% contained at least one vulnerability](https://arxiv.org/abs/2601.10338), and that skills shipping executable scripts were 2.12 times more likely to be among them. Reading a skill before you install it is a reasonable habit, and here reading it is the whole audit.

## How Skills Work

Every skill follows the same concept-first pattern:

1. **The Problem** - what goes wrong without this knowledge
2. **WRONG code** - the naive approach that looks right but fails
3. **CORRECT code** - the right pattern using standard tools
4. **Guardrails** - specific red flags to watch for
5. **Production Implementation** - optional `ml4t-*` library handoff when a stable API exists
6. **Checklist** - verification steps the agent can follow

The first 80% teaches the method with standard Python tools such as `polars`, `numpy`, `scikit-learn`, `scipy`, `statsmodels`, `pytorch`, and `lightgbm`. The final section, when present, points to the production-grade `ml4t-*` library implementation.

## Skill Catalog

### Concepts (10)

| Skill | What it prevents |
|-------|-----------------|
| [backtest-overfitting](concepts/backtest-overfitting/) | Selecting the best historical result without multiple-testing correction |
| [causal-identification](concepts/causal-identification/) | Treating confounded associations as tradable causal effects |
| [data-leakage](concepts/data-leakage/) | Train-test contamination via preprocessing, features, or labels |
| [information-coefficient](concepts/information-coefficient/) | Miscalculating or misinterpreting factor predictive power |
| [lookahead-bias](concepts/lookahead-bias/) | Using future information in features, labels, or evaluation |
| [non-stationarity](concepts/non-stationarity/) | Ignoring changing statistical properties in financial time series |
| [point-in-time](concepts/point-in-time/) | Using revised data that was not known at decision time |
| [regime-awareness](concepts/regime-awareness/) | Treating regimes as timing signals instead of conditioning variables |
| [survivorship-bias](concepts/survivorship-bias/) | Excluding failed or delisted assets from historical analysis |
| [transaction-costs](concepts/transaction-costs/) | Backtesting signals that cannot survive spread, slippage, and impact |

### Data (7)

| Skill | What it does |
|-------|-------------|
| [build-bars](data/build-bars/) | Aggregates tick data into time, volume, and dollar bars |
| [calendar-ops](data/calendar-ops/) | Aligns data across trading calendars, holidays, and frequencies |
| [continuous-futures](data/continuous-futures/) | Builds roll-adjusted continuous futures series |
| [data-export](data/data-export/) | Exports schema-validated datasets to efficient columnar storage |
| [define-universe](data/define-universe/) | Constructs point-in-time tradeable universes with liquidity filters |
| [fetch-data](data/fetch-data/) | Fetches market data through provider abstractions with schema checks |
| [validate-data](data/validate-data/) | Checks gaps, stale prices, outliers, and OHLCV integrity |

### Features (10)

| Skill | What it does |
|-------|-------------|
| [compute-features](features/compute-features/) | Computes panel-aware financial features without cross-asset leakage |
| [feature-families](features/feature-families/) | Balances momentum, mean-reversion, volatility, carry, and value signals |
| [feature-selection](features/feature-selection/) | Selects features inside CV folds using IC, MI, or RFE |
| [feature-store](features/feature-store/) | Stores versioned features with point-in-time retrieval |
| [feature-validation](features/feature-validation/) | Audits IC significance, stability, redundancy, and leakage |
| [horizon-design](features/horizon-design/) | Chooses prediction horizons from IC decay, turnover, and costs |
| [latent-factors](features/latent-factors/) | Extracts latent factors with PCA, IPCA, or autoencoders |
| [meta-labels](features/meta-labels/) | Uses a secondary model to filter or size primary trading signals |
| [regime-features](features/regime-features/) | Builds stationary volatility, trend, and liquidity regime features |
| [triple-barrier](features/triple-barrier/) | Labels trades with volatility-adaptive profit, stop, and time barriers |

### Validation (8)

| Skill | What it does |
|-------|-------------|
| [cpcv](validation/cpcv/) | Runs Combinatorial Purged Cross-Validation |
| [deflated-sharpe](validation/deflated-sharpe/) | Adjusts Sharpe ratios for multiple testing bias |
| [drift-detection](validation/drift-detection/) | Detects input, prediction, and concept drift |
| [evaluate-factor](validation/evaluate-factor/) | Evaluates factor IC, quantile spreads, turnover, and decay |
| [purging-embargo](validation/purging-embargo/) | Removes overlapping labels and adds embargo buffers |
| [shap-analysis](validation/shap-analysis/) | Explains model predictions with SHAP values |
| [stationarity-tests](validation/stationarity-tests/) | Applies ADF/KPSS tests and transformation decisions |
| [walk-forward-cv](validation/walk-forward-cv/) | Evaluates time-series models with rolling or expanding windows |

### Backtest (5)

| Skill | What it does |
|-------|-------------|
| [cost-model](backtest/cost-model/) | Models commissions, slippage, and market impact |
| [rl-execution](backtest/rl-execution/) | Applies reinforcement learning to execution and hedging |
| [run-backtest](backtest/run-backtest/) | Runs event-driven backtests with Strategy/Broker/Engine contracts |
| [sensitivity-analysis](backtest/sensitivity-analysis/) | Tests parameter robustness and overfitting cliffs |
| [tearsheet](backtest/tearsheet/) | Generates performance reports from backtest returns |

### Portfolio (5)

| Skill | What it does |
|-------|-------------|
| [exposure-analysis](portfolio/exposure-analysis/) | Decomposes portfolios by factor, sector, and concentration exposure |
| [kill-switch](portfolio/kill-switch/) | Adds automated drawdown and loss-limit controls |
| [position-sizing](portfolio/position-sizing/) | Converts signals into volatility-targeted position sizes |
| [risk-metrics](portfolio/risk-metrics/) | Computes drawdown, VaR, CVaR, Sharpe, and tail metrics |
| [stress-test](portfolio/stress-test/) | Tests portfolios against historical and hypothetical shocks |

### Advanced AI (5)

| Skill | What it does |
|-------|-------------|
| [agent-governance](advanced-ai/agent-governance/) | Adds policy, warden, approval, and audit controls around agents |
| [agent-state-memory](advanced-ai/agent-state-memory/) | Designs checkpointable state, evidence memory, and replay traces |
| [agent-tool-contracts](advanced-ai/agent-tool-contracts/) | Defines typed tool schemas, provenance, and execution policies |
| [multi-agent-forecasting](advanced-ai/multi-agent-forecasting/) | Combines agent forecasts with diversity, aggregation, and debate controls |
| [research-operator](advanced-ai/research-operator/) | Builds thin autonomous research operators over tools, skills, and artifacts |

### Production (2)

| Skill | What it does |
|-------|-------------|
| [live-trading](production/live-trading/) | Transitions validated backtest strategies to live trading |
| [monitoring-alerting](production/monitoring-alerting/) | Monitors live data, model drift, risk, execution, and alerts |

### Infrastructure (4)

| Skill | What it does |
|-------|-------------|
| [canonical-schema](infrastructure/canonical-schema/) | Enforces standard market-data columns, types, and index conventions |
| [case-study-pipeline](infrastructure/case-study-pipeline/) | Organizes reproducible case-study artifacts and rerun boundaries |
| [polars-patterns](infrastructure/polars-patterns/) | Uses Polars idioms for grouped, windowed financial data processing |
| [registry-system](infrastructure/registry-system/) | Tracks experiments and artifacts with content-addressed metadata |

### Workflows (5)

| Skill | What it does |
|-------|-------------|
| [case-study-development](workflows/case-study-development/) | Runs a stage-gated case study from hypothesis to backtest |
| [factor-research](workflows/factor-research/) | Develops alpha factors from hypothesis through capacity assessment |
| [model-validation](workflows/model-validation/) | Applies multi-gate validation before production sign-off |
| [production-readiness](workflows/production-readiness/) | Checks data, model, risk, monitoring, and governance before go-live |
| [strategy-workflow](workflows/strategy-workflow/) | Covers the full strategy lifecycle from idea to deployment |

## ML4T Libraries

Some skills reference these optional production libraries:

```bash
uv pip install ml4t-data ml4t-engineer ml4t-backtest ml4t-diagnostic ml4t-live
```

| Package | Purpose |
|---------|---------|
| [ml4t-data](https://pypi.org/project/ml4t-data/) | Data providers, schema enforcement, futures contracts |
| [ml4t-engineer](https://pypi.org/project/ml4t-engineer/) | Feature computation, labeling, feature store |
| [ml4t-backtest](https://pypi.org/project/ml4t-backtest/) | Event-driven backtesting with cost models |
| [ml4t-diagnostic](https://pypi.org/project/ml4t-diagnostic/) | Cross-validation, IC analysis, drift detection |
| [ml4t-live](https://pypi.org/project/ml4t-live/) | Live trading with SafeBroker risk controls |

The libraries are optional for reading the skills. The production snippets show how to move from the teaching pattern to validated library code.

## The Harness These Run In

A skill tells an agent what is correct in quantitative research. It says nothing about how the agent works: how a task gets scoped before any code is written, where state lives across a compaction, how a half-finished job is handed to a different agent. That is a separate concern in a separate repository.

- [coding-agent-toolkit](https://github.com/stefan-jansen/coding-agent-toolkit) gives Claude Code and Codex one set of verbs (align, plan, ship, handoff) over a shared `.workspace/` directory, so work survives a swap between hosts.
- [coding-agent-plugins](https://github.com/stefan-jansen/coding-agent-plugins) packages those verbs, along with memory, transition, and code-quality plugins, as an installable Claude Code marketplace.

## Courses, Workshops, and Free Lessons

The method in these files is also taught live, worked through on a real strategy with feedback on your own research question.

<!-- offerings:all start -->
**Cohorts and workshops.** Live, scheduled, and worked through with direct feedback on your own research.

| Starts | Offering | What you leave with |
|--------|----------|---------------------|
| Sep 16 – Dec 2, 2026 | [Machine Learning for Trading: From Research to Production](https://maven.com/stefan-jansen/research-to-production) | Take one research idea from a question to a costed, monitored strategy, with the evidence trail that makes the result checkable. |
| Sep 19, 2026 | [Engineering a Multi-Agent Forecasting System](https://maven.com/stefan-jansen/agent-engineering) | Build a multi-agent forecasting system whose reasoning is auditable end to end. |
| Oct 10, 2026 | [Loop Engineering: Reliable Work From Coding Agents](https://maven.com/stefan-jansen/loop-engineering) | Get reliable work out of coding agents: harness design, verification, and recovery from a bad run. |

**Free live sessions.** Thirty minutes to an hour, no cost, recording sent to everyone who registers.

| When | Session |
|------|---------|
| Wed, Sep 2, 12:00 PM ET / 16:00 UTC | [Managing Your Strategy Research Process](https://maven.com/p/bc9fd4) |
| Wed, Sep 9, 12:00 PM ET / 16:00 UTC | [How to Engineer a Multi-Agent System](https://maven.com/p/c7565e) |
| Wed, Sep 30, 12:00 PM ET / 16:00 UTC | [How to Be Productive with Coding Agents, Beyond Code](https://maven.com/p/efe730) |
| Wed, Nov 4, 12:00 PM ET / 17:00 UTC | [Why Multi-Agent Systems Break, and How To Fix It](https://maven.com/p/393eee) |

*Between cohorts, the [**Insights** newsletter](https://insights.ml4trading.io/) covers the same ground weekly, source by source.*
<!-- offerings:all end -->

## Contributing

Outside contributions are welcome, and a correction to a skill that is subtly
wrong is the most useful kind. [CONTRIBUTING.md](CONTRIBUTING.md) covers what
belongs here and how to run the checks locally; [AGENTS.md](AGENTS.md) is the
full authoring specification. In short:

- Use `name: ml4t-{directory-name}`
- Include trigger language in `description`
- Keep examples concept-first and library-agnostic until `## Production Implementation`
- Include `### WRONG`, `### CORRECT`, guardrails, and a final checklist
- Keep each `SKILL.md` to 120 lines or fewer
- Do not include local agent state, memory, transitions, credentials, or workspace artifacts

CI enforces all of the above, checks every `ml4t.*` name and every direct call
to one in a Production Implementation snippet against the published packages,
and rejects a stale [SKILL_CHAPTER_MAP.md](SKILL_CHAPTER_MAP.md). That check is
static and does not reach methods called on an instance; see
[CONTRIBUTING.md](CONTRIBUTING.md) for what it does and does not cover.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
Security problems go through [SECURITY.md](SECURITY.md), not a public issue.

## Book

These skills distill techniques from [*Machine Learning for Algorithmic Trading*](https://ml4trading.io), 3rd Edition, by Stefan Jansen. Each skill's `metadata.book_chapters` field maps it to the chapter that develops the method in full, and [SKILL_CHAPTER_MAP.md](SKILL_CHAPTER_MAP.md) is the whole mapping in one table.

- The book: [Amazon](https://amzn.to/44FVkGq), or [ml4trading.io](https://ml4trading.io)
- The code, 27 chapters of executed notebooks: [stefan-jansen/machine-learning-for-trading](https://github.com/stefan-jansen/machine-learning-for-trading)
- Weekly research writing on the same subjects: [ML4T Insights](https://insights.ml4trading.io/)

## License and Citation

This repository is licensed under [Apache-2.0](LICENSE).

The license applies to the repository contents. It does not grant trademark rights
in ML4T, Machine Learning for Algorithmic Trading, or related project branding.

If you use these skills in published work, [CITATION.cff](CITATION.cff) has the
citation metadata for the repository and the book.
