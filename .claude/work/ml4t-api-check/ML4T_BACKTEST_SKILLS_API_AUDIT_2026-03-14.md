# Audit Report: `ml4t-backtest` Usage in `~/ml4t/skills`

Date: 2026-03-14

Scope:

- `/home/stefan/ml4t/skills`
- All `SKILL.md` files and repo guidance files that reference `ml4t-backtest`
- Current `ml4t-backtest` source in `/home/stefan/ml4t/libraries/ml4t-backtest`

Method:

- Static API audit only
- No snippets were executed
- Library source was treated as ground truth over skill prose

## Executive Summary

The skills repo has several stale `ml4t-backtest` examples. The high-level framing is mostly still
right, but multiple Production Implementation snippets use an older API shape and would not work as
written against the current library.

The main drift pattern is consistent:

- examples construct `BacktestConfig` with model objects like `commission=` and `slippage=`, but the
  current config uses primitive fields such as `commission_type`, `commission_rate`,
  `slippage_type`, and `slippage_rate`
- examples instantiate `Engine` with the wrong signature
- examples call `run_backtest()` without the required `prices` argument
- examples assume `BacktestResult` exposes convenience attributes like `.sharpe` that are not part
  of the current surface
- one portfolio sizing example uses nonexistent `TargetWeightExecutor` / `RebalanceConfig` fields

So the repo does not need a conceptual rewrite, but it does need a pass to bring every
`ml4t-backtest` snippet onto the current API.

## Findings

### 1. High: several skills use an obsolete engine/config construction pattern

The current library expects:

- `Engine(feed, strategy, config)`
- or `run_backtest(prices=..., strategy=..., signals=..., context=..., config=...)`
- `BacktestConfig` fields like `commission_type`, `commission_rate`, `slippage_type`,
  `slippage_rate`

But these skills still use the old style:

- [backtest/run-backtest/SKILL.md](./backtest/run-backtest/SKILL.md)
- [backtest/cost-model/SKILL.md](./backtest/cost-model/SKILL.md)
- [concepts/transaction-costs/SKILL.md](./concepts/transaction-costs/SKILL.md)
- [workflows/case-study-development/SKILL.md](./workflows/case-study-development/SKILL.md)
- [workflows/strategy-workflow/SKILL.md](./workflows/strategy-workflow/SKILL.md)
- [advanced-ai/rl-execution/SKILL.md](./advanced-ai/rl-execution/SKILL.md)

Typical stale patterns:

- `BacktestConfig(commission=PercentageCommission(...), slippage=...)`
- `Engine(config).run(strategy, feed)`
- `run_backtest(strategy=..., config=...)`

Current ground truth:

- `/home/stefan/ml4t/libraries/ml4t-backtest/src/ml4t/backtest/config.py`
- `/home/stefan/ml4t/libraries/ml4t-backtest/src/ml4t/backtest/engine.py`

### 2. High: the `run-backtest` skill uses the feed payload incorrectly

In:

- [backtest/run-backtest/SKILL.md](./backtest/run-backtest/SKILL.md)

the example reads `bar["momentum"]`, but signal data is nested under `bar["signals"]`. It also
passes `DataFeed(prices)` positionally, even though the current constructor expects `prices_df=...`
or `prices_path=...`.

Current ground truth:

- `/home/stefan/ml4t/libraries/ml4t-backtest/src/ml4t/backtest/datafeed.py`

### 3. High: tearsheet/result examples assume convenience attributes that do not exist

These skills treat `BacktestResult` as if it exposes:

- `result.sharpe`
- `result.max_drawdown`
- `result.calmar`
- `result.returns`

Affected files:

- [backtest/run-backtest/SKILL.md](./backtest/run-backtest/SKILL.md)
- [backtest/tearsheet/SKILL.md](./backtest/tearsheet/SKILL.md)

Current result usage should instead rely on:

- `result.metrics[...]`
- `result.to_equity_dataframe()`
- `result.to_daily_returns()`
- `result.to_tearsheet()`

Current ground truth:

- `/home/stefan/ml4t/libraries/ml4t-backtest/src/ml4t/backtest/result.py`

### 4. High: the position-sizing skill uses nonexistent rebalancer parameters

In:

- [portfolio/position-sizing/SKILL.md](./portfolio/position-sizing/SKILL.md)

the example uses:

- `TargetWeightExecutor(rebalance=...)`
- `RebalanceConfig(frequency="weekly")`
- `max_position_weight=...`
- `max_leverage=...`

Those are not current `ml4t-backtest` fields. The actual API is:

- `TargetWeightExecutor(config=RebalanceConfig(...))`
- `RebalanceConfig.max_single_weight`
- `RebalanceConfig.max_gross_leverage`

Current ground truth:

- `/home/stefan/ml4t/libraries/ml4t-backtest/src/ml4t/backtest/execution/rebalancer.py`

### 5. Medium: cost-model skills no longer show the most current execution API

The cost-oriented skills present slippage models as the main production implementation:

- [backtest/cost-model/SKILL.md](./backtest/cost-model/SKILL.md)
- [concepts/transaction-costs/SKILL.md](./concepts/transaction-costs/SKILL.md)
- [advanced-ai/rl-execution/SKILL.md](./advanced-ai/rl-execution/SKILL.md)

That is not wrong in spirit, but it is incomplete for the current library. The engine now also
accepts:

- `market_impact_model=...`
- `execution_limits=...`

through `Engine(...)` and `run_backtest(...)`. If the goal is to illustrate realistic execution and
market impact, the current snippets under-demonstrate the evolved API.

Current ground truth:

- `/home/stefan/ml4t/libraries/ml4t-backtest/src/ml4t/backtest/engine.py`
- `/home/stefan/ml4t/libraries/ml4t-backtest/src/ml4t/backtest/execution/impact.py`

### 6. Medium: `BacktestConfig.from_yaml("setup.yaml")` is oversold in workflow skills

In:

- [workflows/case-study-development/SKILL.md](./workflows/case-study-development/SKILL.md)

the example implies that a generic project `setup.yaml` can be loaded directly as a backtest config.
That is misleading. `BacktestConfig.from_yaml(...)` expects a backtest-config-shaped YAML document,
not an arbitrary workflow-level setup file.

Current ground truth:

- `/home/stefan/ml4t/libraries/ml4t-backtest/src/ml4t/backtest/config.py`

## Files Reviewed With `ml4t-backtest` Usage

Direct or substantive `ml4t-backtest` usage appeared in:

- `backtest/run-backtest/SKILL.md`
- `backtest/cost-model/SKILL.md`
- `backtest/tearsheet/SKILL.md`
- `backtest/regime-backtest/SKILL.md`
- `concepts/transaction-costs/SKILL.md`
- `portfolio/position-sizing/SKILL.md`
- `advanced-ai/rl-execution/SKILL.md`
- `workflows/case-study-development/SKILL.md`
- `workflows/strategy-workflow/SKILL.md`
- `README.md`
- `AGENTS.md`
- `REVIEW_PROMPT.md`

Of these, `README.md`, `AGENTS.md`, and `REVIEW_PROMPT.md` are mostly directionally correct. The
main problems are in the executable-looking code snippets inside the skills themselves.

## Recommended Fixes

### Immediate content fixes

1. Rewrite all stale construction snippets to the current API:

- `feed = DataFeed(prices_df=prices_df, signals_df=signals_df, context_df=context_df)`
- `result = Engine(feed, strategy, config).run()`
- or `run_backtest(prices=prices_df, strategy=strategy, signals=..., context=..., config=config)`

2. Replace object-valued config examples like:

- `BacktestConfig(commission=PercentageCommission(...), slippage=...)`

with current config fields such as:

- `commission_type=CommissionType.PERCENTAGE`
- `commission_rate=...`
- `slippage_type=SlippageType.VOLUME_BASED`
- `slippage_rate=...`

or explicitly document when the example is only conceptual and not literal current code.

3. Rewrite `BacktestResult` examples to use:

- `result.metrics["sharpe"]`
- `result.metrics["max_drawdown"]`
- `result.to_equity_dataframe()`
- `result.to_daily_returns()`
- `result.to_tearsheet()`

4. Rewrite the `position-sizing` skill around:

- `TargetWeightExecutor(config=RebalanceConfig(...))`
- `max_single_weight`
- `max_gross_leverage`

### Demonstration improvements

1. In cost-model and RL-execution skills, add a small example showing:

- `market_impact_model=...`
- optional `execution_limits=...`

so the skills reflect the current execution surface rather than only older slippage-only patterns.

2. In workflow skills, avoid implying that one generic `setup.yaml` can be fed directly into
`BacktestConfig.from_yaml(...)` unless the YAML is explicitly backtest-config-shaped.

### Repo-level authoring guardrail

Add one explicit authoring rule to:

- `AGENTS.md`
- `REVIEW_PROMPT.md`

Recommended rule:

> Verify every `ml4t-backtest` snippet against current `config.py`, `engine.py`, `datafeed.py`, and
> `result.py`. Do not assume `BacktestConfig` accepts commission/slippage model objects, and do not
> assume `BacktestResult` exposes convenience attributes unless they exist in source.

## Bottom Line

The `~/ml4t/skills` repo is conceptually sound, but its `ml4t-backtest` examples have visible API
drift. The most important corrections are mechanical and localized: update how configs, engines,
feeds, rebalancers, and results are shown. Once those snippets are brought onto the current API, the
skills should again illustrate `ml4t-backtest` correctly and concisely.
