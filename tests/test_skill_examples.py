"""Execute the ### CORRECT examples straight out of the SKILL.md files.

Everything else in CI reads the skills as text. That let `datetime64[Q]` - a
unit numpy does not have - sit in a CORRECT block that raised TypeError on
every input, and it let two bar-boundary and forward-return bugs ship. These
tests run the published code and assert the numbers it produces, so an example
that cannot run, or that runs and is wrong at a boundary, fails the build.

Third-party dependencies are optional: without them the module skips rather
than failing, so `python -m unittest discover -s tests` still works on a bare
interpreter. The `skill-examples` CI job installs them, so they do run.
"""

from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import numpy as np
    import polars as pl
    import scipy  # noqa: F401
    import sklearn  # noqa: F401

    DEPS = True
except ImportError:  # pragma: no cover - exercised only on a bare interpreter
    DEPS = False


def block(skill: str, index: int) -> str:
    """The index-th ```python fence of a SKILL.md, by `<category>/<skill>` path."""
    text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, re.S)
    if index >= len(blocks):
        raise AssertionError(f"{skill} has {len(blocks)} python blocks, wanted {index}")
    return blocks[index]


def run(skill: str, index: int, **names) -> dict:
    """Execute a block with `names` predefined, and hand back its namespace."""
    namespace = dict(names)
    with contextlib.redirect_stdout(io.StringIO()):  # blocks print their results
        exec(block(skill, index), namespace)  # noqa: S102 - running it is the point
    return namespace


@unittest.skipUnless(DEPS, "numpy, polars, scipy and scikit-learn are required")
class DollarBarsCloseOnTheThreshold(unittest.TestCase):
    def bars(self, sizes, threshold):
        trades = pl.DataFrame({
            "timestamp": list(range(len(sizes))),
            "price": [100.0] * len(sizes),
            "size": [s / 100.0 for s in sizes],
        })
        namespace = run("data/build-bars", 1, trades=trades)
        built = namespace["build_dollar_bars"](trades, threshold)
        return built["dollar_volume"].to_list()

    def test_the_accumulator_resets_after_a_bar_closes(self):
        # Without a reset these are $1,600, $800, $800: the overshoot in the
        # first bar is taken out of the second.
        self.assertEqual([1600.0, 1600.0], self.bars([800] * 4, 1000.0))

    def test_a_bar_is_not_closed_below_the_threshold(self):
        self.assertEqual([1200.0, 1200.0], self.bars([600] * 4, 1000.0))

    def test_a_single_oversized_trade_is_its_own_bar(self):
        self.assertEqual([5000.0, 1000.0], self.bars([5000, 1000], 1000.0))


@unittest.skipUnless(DEPS, "numpy is required")
class KillSwitchLatchesUntilReset(unittest.TestCase):
    HEALTHY = dict(daily_pnl=-0.01, drawdown=-0.02, gross_lev=1.0, max_pos=0.05)
    BREACH = dict(daily_pnl=-0.05, drawdown=-0.02, gross_lev=1.0, max_pos=0.05)

    def switch(self):
        self.breaches: list[str] = []
        cls = run("portfolio/kill-switch", 1)["KillSwitch"]
        return cls(reset_code="s3cret", on_breach=self.breaches.append)

    def test_a_breach_latches_and_calls_the_handler(self):
        switch = self.switch()
        self.assertTrue(switch.check(**self.HEALTHY, position=0.0, qty=100))
        self.assertFalse(switch.check(**self.BREACH, position=0.0, qty=100))
        self.assertEqual(["max_daily_loss"], self.breaches)
        # The metrics are healthy again; a switch that unlatches here is useless.
        self.assertFalse(switch.check(**self.HEALTHY, position=0.0, qty=100))

    def test_a_latched_switch_still_passes_a_risk_reducing_order(self):
        switch = self.switch()
        switch.check(**self.BREACH, position=100.0, qty=1)
        self.assertTrue(switch.check(**self.HEALTHY, position=100.0, qty=-50))
        self.assertTrue(switch.check(**self.HEALTHY, position=-100.0, qty=100))

    def test_reduction_is_derived_from_the_order_not_claimed_by_the_caller(self):
        switch = self.switch()
        switch.check(**self.BREACH, position=100.0, qty=1)
        # Selling 500 against a 100 long crosses zero into a new short.
        self.assertFalse(switch.check(**self.HEALTHY, position=100.0, qty=-500))
        self.assertFalse(switch.check(**self.HEALTHY, position=100.0, qty=25))

    def test_only_the_reset_code_clears_the_latch(self):
        switch = self.switch()
        switch.check(**self.BREACH, position=0.0, qty=1)
        switch.reset("APPROVED")
        self.assertFalse(switch.check(**self.HEALTHY, position=0.0, qty=100))
        switch.reset("s3cret")
        self.assertTrue(switch.check(**self.HEALTHY, position=0.0, qty=100))


@unittest.skipUnless(DEPS, "numpy is required")
class PurgingRespectsBothBoundaries(unittest.TestCase):
    def split(self, **kwargs):
        namespace = run("validation/purging-embargo", 1, np=np)
        return namespace["purged_split"](**kwargs)

    def test_no_training_label_reaches_into_the_test_window(self):
        train, test = self.split(n_samples=500, train_end=100, test_start=100,
                                 test_end=111, label_horizon=5, embargo_size=2)
        before = train[train < test[0]]
        self.assertEqual(94, before.max())  # 95 + 5 would close on test bar 100
        self.assertEqual(113, train[train > test[-1]].min())  # 111 test end + 2

    def test_train_end_bounds_the_split_when_it_is_the_tighter_limit(self):
        train, _ = self.split(n_samples=500, train_end=80, test_start=200,
                              test_end=211, label_horizon=5, embargo_size=2)
        self.assertEqual(79, train[train < 200].max())


@unittest.skipUnless(DEPS, "numpy and scipy are required")
class DriftDetectionSeesTheTails(unittest.TestCase):
    def psi(self, reference, current):
        # The block ends by looping over a feature matrix, so seed one.
        namespace = run("validation/drift-detection", 1, np=np,
                        X_train=reference.reshape(-1, 1), X_live=current.reshape(-1, 1),
                        feature_names=["f"])
        return namespace["calculate_psi"](reference, current)

    def test_a_shift_outside_the_reference_range_is_not_discarded(self):
        rng = np.random.default_rng(0)
        reference = rng.normal(0, 1, 5000)
        # Every observation lands past the reference maximum. Percentile bin
        # edges would drop them all and report no drift whatsoever.
        self.assertGreater(self.psi(reference, rng.normal(0, 1, 5000) + 8), 1.0)

    def test_an_unshifted_sample_is_not_flagged(self):
        rng = np.random.default_rng(1)
        self.assertLess(self.psi(rng.normal(0, 1, 5000), rng.normal(0, 1, 5000)), 0.10)


@unittest.skipUnless(DEPS, "numpy and scipy are required")
class FeatureValidationRunsOnRealDates(unittest.TestCase):
    def sample(self, n=800):
        rng = np.random.default_rng(7)
        dates = np.datetime64("2020-01-01") + np.arange(n).astype("timedelta64[D]")
        return rng.normal(size=n), rng.normal(size=n), dates

    def test_quarterly_bucketing_works_on_a_datetime64_array(self):
        # datetime64[Q] is not a numpy unit; this raised TypeError for every input.
        feature, target, dates = self.sample()
        result = run("features/feature-validation", 1, np=np)["validate_feature"](
            feature, target, dates)
        self.assertEqual({"ic", "p_value", "ic_ir", "leakage_flag",
                          "pct_positive_quarters"}, set(result))
        self.assertTrue(np.isfinite(result["ic"]))
        self.assertTrue(0.0 <= result["pct_positive_quarters"] <= 1.0)

    def test_missing_values_in_either_series_do_not_make_the_ic_nan(self):
        feature, target, dates = self.sample()
        feature[::37] = np.nan
        target[5::53] = np.nan
        result = run("features/feature-validation", 1, np=np)["validate_feature"](
            feature, target, dates)
        self.assertTrue(np.isfinite(result["ic"]))
        self.assertTrue(np.isfinite(result["ic_ir"]))

    def decay(self, feature, returns, horizons):
        from scipy.stats import spearmanr
        namespace = run("features/feature-validation", 2, np=np, spearmanr=spearmanr)
        return namespace["ic_decay"](feature, returns, horizons)

    def test_one_missing_return_does_not_poison_every_later_window(self):
        rng = np.random.default_rng(3)
        returns = rng.normal(0, 0.01, 300)
        returns[50] = np.nan
        # A plain cumprod left 49 of 299 rows usable from this single gap.
        self.assertTrue(all(np.isfinite(v) for v in self.decay(
            rng.normal(size=300), returns, [1, 5, 21]).values()))

    def test_a_horizon_longer_than_the_sample_reports_nan_instead_of_raising(self):
        rng = np.random.default_rng(4)
        decay = self.decay(rng.normal(size=50), rng.normal(0, 0.01, 50), [1, 63])
        self.assertTrue(np.isfinite(decay[1]))
        self.assertTrue(np.isnan(decay[63]))

    def test_the_forward_return_is_the_compounded_product(self):
        rng = np.random.default_rng(5)
        returns = rng.normal(0, 0.01, 200)
        feature = np.arange(200, dtype=float)
        namespace = run("features/feature-validation", 2, np=np,
                        spearmanr=lambda a, b: (float(np.corrcoef(a, b)[0, 1]), 0.0))
        namespace["ic_decay"](feature, returns, [5])  # must not raise
        expected = np.prod(1 + returns[101:106]) - 1
        gaps = np.r_[0, np.cumsum(np.isnan(returns))]
        cum = np.r_[1.0, np.cumprod(1.0 + np.nan_to_num(returns))]
        self.assertAlmostEqual(expected, (cum[6:201] / cum[1:196] - 1.0)[100], places=12)
        self.assertEqual(0, gaps[-1])


@unittest.skipUnless(DEPS, "numpy and scikit-learn are required")
class WalkForwardPCAUsesOnlyItsOwnFold(unittest.TestCase):
    def factors(self, returns):
        from sklearn.decomposition import PCA
        namespace = run("features/latent-factors", 1, np=np, PCA=PCA, returns=returns)
        return namespace["factors"]

    def panel(self, n_periods=560, n_assets=40):
        rng = np.random.default_rng(11)
        market = rng.normal(0, 0.01, n_periods)
        return (market[:, None] * rng.uniform(0.5, 1.5, n_assets)
                + rng.normal(0, 0.01, (n_periods, n_assets)))

    def test_nothing_is_scored_before_the_first_training_window_is_full(self):
        factors = self.factors(self.panel())
        self.assertTrue(np.isnan(factors[:504]).all())
        self.assertFalse(np.isnan(factors[504:, 0]).all())

    def test_noise_components_are_dropped_rather_than_returned(self):
        # One factor drives the panel, so most components sit under the bound.
        factors = self.factors(self.panel())
        kept = np.mean(np.any(~np.isnan(factors), axis=0))
        self.assertLess(kept, 0.5)


@unittest.skipUnless(DEPS, "numpy and scipy are required")
class DeflatedSharpeIsAProbability(unittest.TestCase):
    def dsr(self, **kwargs):
        from scipy import stats
        # The block ends by deflating a search; seed a plausible one.
        namespace = run("validation/deflated-sharpe", 1, np=np, stats=stats,
                        sharpes=list(np.linspace(0.2, 1.6, 50)))
        return namespace["deflated_sharpe_ratio"](**kwargs)

    def test_a_per_period_sharpe_produces_an_interior_probability(self):
        value = self.dsr(observed_sr=0.09, n_trials=50, sr_std=0.02, n_obs=252 * 5)
        self.assertTrue(0.0 < value < 1.0, value)

    def test_more_trials_lower_the_probability_for_the_same_observation(self):
        few = self.dsr(observed_sr=0.09, n_trials=10, sr_std=0.02, n_obs=252 * 5)
        many = self.dsr(observed_sr=0.09, n_trials=500, sr_std=0.02, n_obs=252 * 5)
        self.assertGreater(few, many)


@unittest.skipUnless(DEPS, "numpy is required")
class CostsScaleWithParticipation(unittest.TestCase):
    def costs(self, weights, adv_shares, nav=1e8):
        namespace = run("backtest/cost-model", 1, np=np)
        n = len(weights)
        return namespace["net_returns_with_costs"](
            weights=np.asarray(weights, dtype=float),
            asset_returns=np.zeros(n),
            prices=np.full(n, 100.0),
            adv_shares=np.full(n, float(adv_shares)),
            daily_vol=np.full(n, 0.02),
            nav=nav,
        )

    def test_impact_keeps_growing_past_one_times_adv(self):
        # Clipping participation at 1.0 priced a 500x-ADV order like an ADV one.
        small = self.costs([0.0, 0.5], adv_shares=1e6)[1]
        huge = self.costs([0.0, 0.5], adv_shares=1e3)[1]
        self.assertLess(huge, small)

    def test_holding_a_position_costs_nothing_to_trade(self):
        held = self.costs([0.5, 0.5], adv_shares=1e6)[1]
        self.assertEqual(0.0, held)
