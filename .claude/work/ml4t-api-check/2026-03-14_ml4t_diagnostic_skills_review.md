# ml4t-diagnostic API Review for `~/ml4t/skills`

Date: 2026-03-14
Reviewer: Codex
Scope: Review all usages of `ml4t-diagnostic` in `~/ml4t/skills`, verify API currency and correctness against the checked-in library source in `~/ml4t/libraries/ml4t-diagnostic`, and identify stale, incorrect, or misleading usage.

## Executive Summary

Most `ml4t-diagnostic` references in the skills repo are still directionally correct, but there are several material errors where the documented usage no longer matches the current library behavior.

The most important issues are:

1. `stationarity-tests` recommends the wrong function entirely.
2. `drift-detection` uses a stale `compute_ic_series(...)` calling convention and skips the library's actual drift API.
3. `risk-metrics` passes an equity curve where `PortfolioAnalysis` requires non-cumulative returns.
4. `backtest-overfitting` shows an invalid `compute_pbo(...)` call.
5. `shap-analysis` misstates the return type of `compute_shap_importance(...)`.
6. The repo-level API reference in `AGENTS.md` / `REVIEW_PROMPT.md` is incomplete enough to mislead future maintenance.

## Review Method

I reviewed all files in `~/ml4t/skills` that reference `ml4t-diagnostic` or `ml4t.diagnostic`, then compared each import path and example usage to the current library source, especially:

- `src/ml4t/diagnostic/api.py`
- `src/ml4t/diagnostic/evaluation/__init__.py`
- `src/ml4t/diagnostic/evaluation/metrics/information_coefficient.py`
- `src/ml4t/diagnostic/evaluation/metrics/ic_statistics.py`
- `src/ml4t/diagnostic/evaluation/metrics/importance_shap.py`
- `src/ml4t/diagnostic/evaluation/portfolio_analysis/analysis.py`
- `src/ml4t/diagnostic/evaluation/stats/*`
- `src/ml4t/diagnostic/evaluation/stationarity/analysis.py`
- `src/ml4t/diagnostic/evaluation/drift/__init__.py`
- `src/ml4t/diagnostic/selection/*`

This was a static API review. I did not modify the skills repo.

## Files Reviewed

Repo-level guidance:

- `/home/stefan/ml4t/skills/AGENTS.md`
- `/home/stefan/ml4t/skills/README.md`
- `/home/stefan/ml4t/skills/REVIEW_PROMPT.md`

Skills:

- `/home/stefan/ml4t/skills/concepts/backtest-overfitting/SKILL.md`
- `/home/stefan/ml4t/skills/concepts/data-leakage/SKILL.md`
- `/home/stefan/ml4t/skills/concepts/information-coefficient/SKILL.md`
- `/home/stefan/ml4t/skills/concepts/lookahead-bias/SKILL.md`
- `/home/stefan/ml4t/skills/concepts/non-stationarity/SKILL.md`
- `/home/stefan/ml4t/skills/features/feature-selection/SKILL.md`
- `/home/stefan/ml4t/skills/features/feature-validation/SKILL.md`
- `/home/stefan/ml4t/skills/features/horizon-design/SKILL.md`
- `/home/stefan/ml4t/skills/portfolio/risk-metrics/SKILL.md`
- `/home/stefan/ml4t/skills/validation/cpcv/SKILL.md`
- `/home/stefan/ml4t/skills/validation/deflated-sharpe/SKILL.md`
- `/home/stefan/ml4t/skills/validation/drift-detection/SKILL.md`
- `/home/stefan/ml4t/skills/validation/evaluate-factor/SKILL.md`
- `/home/stefan/ml4t/skills/validation/purging-embargo/SKILL.md`
- `/home/stefan/ml4t/skills/validation/shap-analysis/SKILL.md`
- `/home/stefan/ml4t/skills/validation/stationarity-tests/SKILL.md`
- `/home/stefan/ml4t/skills/validation/walk-forward-cv/SKILL.md`
- `/home/stefan/ml4t/skills/workflows/factor-research/SKILL.md`
- `/home/stefan/ml4t/skills/workflows/model-validation/SKILL.md`

## Findings

### High Severity

#### 1. `stationarity-tests` recommends the wrong API and describes nonexistent behavior

Skill:

- `/home/stefan/ml4t/skills/validation/stationarity-tests/SKILL.md:90`

Current skill snippet:

```python
from ml4t.diagnostic.evaluation.stats import robust_ic

# robust_ic handles non-stationary inputs by auto-detecting
# and applying appropriate transformations before IC computation
ic_result = robust_ic(signal, forward_returns)
```

Why this is wrong:

- `robust_ic` is not a stationarity testing utility.
- It does not auto-detect non-stationarity.
- It does not transform inputs for stationarity.
- It computes bootstrap-robust IC inference.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/stats/hac_standard_errors.py:28`
- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/stationarity/analysis.py:311`

Implication:

An agent following this skill would use the wrong tool and would not run stationarity diagnostics at all.

Recommended fix:

Replace the production section with either:

```python
from ml4t.diagnostic.evaluation.stationarity import analyze_stationarity

result = analyze_stationarity(feature_series, include_tests=["adf", "kpss"])
print(result.consensus)
print(result.summary_df)
```

Or, if the intent is a broader feature health check:

```python
from ml4t.diagnostic.config import DiagnosticConfig
from ml4t.diagnostic.evaluation import FeatureDiagnostics

diagnostics = FeatureDiagnostics(DiagnosticConfig())
result = diagnostics.run_diagnostics(feature_series, name="feature")
print(result.stationarity.consensus)
```

#### 2. `drift-detection` uses a stale `compute_ic_series(...)` calling convention and omits the actual drift API

Skill:

- `/home/stefan/ml4t/skills/validation/drift-detection/SKILL.md:96`

Current skill snippet:

```python
from ml4t.diagnostic.evaluation.metrics import compute_ic_series

ic_series = compute_ic_series(predictions, actuals, timestamps)
recent_ic = np.mean(ic_series[-63:])
baseline_ic = np.mean(ic_series[:252])
```

Why this is wrong:

- The current `compute_ic_series(...)` API does not accept `(predictions, actuals, timestamps)` positional arrays.
- It expects prediction and return DataFrames with column names and date/entity join keys.
- It returns a DataFrame, not a 1D array.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/metrics/information_coefficient.py:152`

Additional issue:

- The skill is about drift detection, but the library has a dedicated drift module exporting `compute_psi`, `compute_wasserstein_distance`, `compute_domain_classifier_drift`, and `analyze_drift`.
- That surface is the most relevant production implementation and is not shown.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/drift/__init__.py:125`

Recommended fix:

Split the production section into two short examples:

1. Feature drift:

```python
from ml4t.diagnostic.evaluation.drift import analyze_drift

result = analyze_drift(reference_df, current_df, methods=["psi", "wasserstein"])
print(result.summary())
```

2. Concept drift via IC:

```python
from ml4t.diagnostic.api import compute_ic_series

ic_df = compute_ic_series(
    prediction_frame,
    return_frame,
    pred_col="prediction",
    ret_col="forward_return",
    date_col="date",
    entity_col="symbol",
)
recent_ic = ic_df.tail(63)["ic"].mean()
```

#### 3. `risk-metrics` passes an equity curve where `PortfolioAnalysis` requires return series

Skill:

- `/home/stefan/ml4t/skills/portfolio/risk-metrics/SKILL.md:92`

Current skill snippet:

```python
from ml4t.diagnostic.api import PortfolioAnalysis

pa = PortfolioAnalysis(returns=equity_curve, benchmark=benchmark_curve)
metrics = pa.compute_summary_stats()
report = metrics.summary()
```

Why this is wrong:

- `PortfolioAnalysis` expects non-cumulative return series.
- Passing an equity curve or benchmark equity curve would corrupt Sharpe, Sortino, drawdown, VaR, CVaR, and all derived metrics.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/portfolio_analysis/analysis.py:75`

Recommended fix:

```python
from ml4t.diagnostic.api import PortfolioAnalysis

pa = PortfolioAnalysis(
    returns=strategy_returns,
    benchmark=benchmark_returns,
)
metrics = pa.compute_summary_stats()
print(metrics.summary())
```

Optional better example for this skill:

```python
tear_sheet = pa.create_tear_sheet()
tear_sheet.save_html("risk_report.html")
```

That would better showcase the library’s pyfolio-replacement positioning.

#### 4. `backtest-overfitting` shows an invalid `compute_pbo(...)` call

Skill:

- `/home/stefan/ml4t/skills/concepts/backtest-overfitting/SKILL.md:96`

Current skill snippet:

```python
from ml4t.diagnostic.evaluation.stats import compute_pbo, benjamini_hochberg_fdr
from ml4t.diagnostic.splitters import CombinatorialCV

cpcv = CombinatorialCV(n_groups=8, n_test_groups=2, embargo_size=5)
pbo = compute_pbo(sharpe_matrix)               # from CPCV fold results
rejected = benjamini_hochberg_fdr(p_values, alpha=0.05)
```

Why this is wrong:

- `compute_pbo(...)` requires two inputs: in-sample performance and out-of-sample performance.
- The one-argument call is invalid for the current API.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/stats/backtest_overfitting.py:98`

Recommended fix:

```python
from ml4t.diagnostic.evaluation.stats import compute_pbo, deflated_sharpe_ratio

pbo = compute_pbo(is_performance, oos_performance)
print(pbo.interpret())

# Multiple strategies -> DSR
result = deflated_sharpe_ratio(strategy_return_series_list, frequency="daily")
print(result.probability)
```

This also aligns the example more tightly with the skill’s stated focus on overfitting and multiple testing.

### Medium Severity

#### 5. `shap-analysis` misstates the return type of `compute_shap_importance(...)`

Skill:

- `/home/stefan/ml4t/skills/validation/shap-analysis/SKILL.md:94`

Current skill text:

- “Returns DataFrame with mean_shap, std_shap, rank per feature”

Why this is wrong:

- The current function returns a dict, not a DataFrame.
- The documented keys are `shap_values`, `importances`, `feature_names`, `base_value`, `n_features`, `n_samples`, `model_type`, `explainer_type`, and `additivity_verified`.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/metrics/importance_shap.py:468`

Recommended fix:

```python
from ml4t.diagnostic.evaluation.metrics import compute_shap_importance

shap_report = compute_shap_importance(model, X_test, feature_names=feature_names)
for name, imp in zip(shap_report["feature_names"], shap_report["importances"]):
    print(name, imp)
```

If you want a trading-specific hook, add one sentence pointing readers to `TradeShapAnalyzer` for post-trade diagnostics.

#### 6. Repo-level API reference is incomplete and can cause stale reviews to pass

Files:

- `/home/stefan/ml4t/skills/AGENTS.md:171`
- `/home/stefan/ml4t/skills/REVIEW_PROMPT.md:143`

Problem:

These files label their lists as “verified API reference” / “ground truth,” but they omit several current and relevant `ml4t-diagnostic` surfaces:

- `deflated_sharpe_ratio`
- `deflated_sharpe_ratio_from_statistics`
- `analyze_stationarity`
- `analyze_drift`
- `TradeShapAnalyzer`
- `compute_ic_by_horizon`
- `FeatureDiagnostics`
- `FactorAnalysis`

Because `REVIEW_PROMPT.md` explicitly says any Production Implementation section using names not on the list is wrong, the reference itself is now too incomplete to serve as review ground truth.

Current library source examples:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/__init__.py:44`
- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/__init__.py:119`
- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/stats/__init__.py:68`
- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/stats/__init__.py:144`

Recommended fix:

Update the repo-level API sections to distinguish:

- stable integration surface: `ml4t.diagnostic.api`
- common advanced surfaces: `ml4t.diagnostic.evaluation`, `ml4t.diagnostic.evaluation.stats`, `ml4t.diagnostic.evaluation.drift`, `ml4t.diagnostic.evaluation.stationarity`

#### 7. `model-validation` is under-specified around PBO

Skill:

- `/home/stefan/ml4t/skills/workflows/model-validation/SKILL.md:96`

Current snippet:

```python
from ml4t.diagnostic.api import ValidatedCrossValidation
from ml4t.diagnostic.config import ValidatedCrossValidationConfig
from ml4t.diagnostic.evaluation.stats import compute_pbo

config = ValidatedCrossValidationConfig(n_groups=10, n_test_groups=2, embargo_pct=0.01)
vcv = ValidatedCrossValidation(config)
result = vcv.fit_evaluate(X, y, model, times=timestamps)
pbo = compute_pbo(np.array(is_sharpes), np.array(oos_sharpes))
```

Issue:

- The imports are current and the config usage is current.
- But the example never defines how `is_sharpes` / `oos_sharpes` are derived, and they are not outputs of `fit_evaluate(...)`.
- That makes the snippet hard to follow and easy to misuse.

Recommended fix:

Either:

- drop the PBO line from this workflow skill and keep it focused on `ValidatedCrossValidation`, or
- show a minimal explicit strategy grid / IS-OOS matrix construction before calling `compute_pbo(...)`.

### Low Severity / Improvement Opportunities

#### 8. `deflated-sharpe` demonstrates PSR in a DSR-focused skill

Skill:

- `/home/stefan/ml4t/skills/validation/deflated-sharpe/SKILL.md:102`

Current snippet:

```python
from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio

result = deflated_sharpe_ratio(strategy_returns, frequency="daily")
print(f"Prob(true SR > 0): {result.probability:.3f}")
print(f"Deflated Sharpe: {result.deflated_sharpe:.3f}")
```

Issue:

- This is valid.
- But the skill teaches multiple-testing-adjusted DSR, while the example shows the single-series PSR path.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/stats/deflated_sharpe_ratio.py:233`

Recommended improvement:

Show both modes briefly, with emphasis on the list-of-strategies case.

#### 9. `horizon-design` should use `compute_ic_by_horizon(...)`

Skill:

- `/home/stefan/ml4t/skills/features/horizon-design/SKILL.md:109`

Current snippet uses repeated `compute_ic_series(...)` calls.

Issue:

- It is valid, but the library now has a more direct helper for multi-horizon IC analysis.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/metrics/information_coefficient.py:262`

Recommended improvement:

```python
from ml4t.diagnostic.evaluation.metrics import compute_ic_by_horizon

ic_by_horizon = compute_ic_by_horizon(
    predictions=prediction_frame,
    prices=price_frame,
    horizons=[1, 5, 10, 20, 60],
    pred_col="prediction",
    price_col="close",
    date_col="date",
    group_col="symbol",
)
```

#### 10. `shap-analysis` misses the trade-level ML4T workflow

Skill:

- `/home/stefan/ml4t/skills/validation/shap-analysis/SKILL.md:89`

Issue:

- The global SHAP helper is relevant.
- But for ML4T specifically, the library also offers `TradeShapAnalyzer` for understanding bad trades and error patterns.

Current library source:

- `/home/stefan/ml4t/libraries/ml4t-diagnostic/src/ml4t/diagnostic/evaluation/__init__.py:69`

Recommended improvement:

Add one sentence or a second mini-snippet that points to `TradeShapAnalyzer` for post-trade attribution rather than generic model interpretation only.

## Files That Appear Current

The following skill usages are materially current and require no urgent API corrections:

- `/home/stefan/ml4t/skills/validation/cpcv/SKILL.md`
- `/home/stefan/ml4t/skills/validation/purging-embargo/SKILL.md`
- `/home/stefan/ml4t/skills/validation/walk-forward-cv/SKILL.md`
- `/home/stefan/ml4t/skills/validation/evaluate-factor/SKILL.md`
- `/home/stefan/ml4t/skills/workflows/factor-research/SKILL.md`
- `/home/stefan/ml4t/skills/concepts/information-coefficient/SKILL.md`
- `/home/stefan/ml4t/skills/concepts/non-stationarity/SKILL.md`
- `/home/stefan/ml4t/skills/concepts/lookahead-bias/SKILL.md`
- `/home/stefan/ml4t/skills/concepts/data-leakage/SKILL.md`
- `/home/stefan/ml4t/skills/validation/cpcv/SKILL.md`

## Recommended Remediation Order

1. Fix the incorrect production sections in:
   - `validation/stationarity-tests`
   - `validation/drift-detection`
   - `portfolio/risk-metrics`
   - `concepts/backtest-overfitting`
   - `validation/shap-analysis`
2. Update repo-level `ml4t-diagnostic` API guidance in:
   - `AGENTS.md`
   - `README.md` if needed
   - `REVIEW_PROMPT.md`
3. Improve examples in:
   - `validation/deflated-sharpe`
   - `features/horizon-design`
   - `validation/shap-analysis`
   - `workflows/model-validation`

## Suggested Minimal Patch Set

If the goal is a tight, high-value cleanup without broader rewrites, the minimum useful set is:

- Replace `stationarity-tests` production example with `analyze_stationarity(...)`
- Replace `drift-detection` production example with `analyze_drift(...)` plus a correct DataFrame-based IC example
- Replace `equity_curve` / `benchmark_curve` with return series in `risk-metrics`
- Replace one-arg `compute_pbo(sharpe_matrix)` with two-input `compute_pbo(is_perf, oos_perf)` in `backtest-overfitting`
- Fix `shap-analysis` to describe the dict return value of `compute_shap_importance(...)`
- Expand the repo-level API reference so future reviews do not propagate stale assumptions

## Bottom Line

The skills repo is still broadly aligned with `ml4t-diagnostic`, but a handful of high-visibility production snippets are now wrong enough to mislead users and agents.

The highest-value correction is to treat `AGENTS.md` and `REVIEW_PROMPT.md` as first-class maintenance targets. Several skill errors appear to be downstream of those repo-level “ground truth” sections lagging behind the library.
