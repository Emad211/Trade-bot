import numpy as np

from hybrid_trader.bootstrap_robustness import (
    circular_block_bootstrap,
    fold_concentration,
)
from hybrid_trader.regime_robustness import classify_market_regimes, regime_performance


def test_block_bootstrap_detects_persistent_improvement() -> None:
    rng = np.random.default_rng(11)
    benchmark = rng.normal(0.0, 0.002, size=1200)
    candidate = benchmark + rng.normal(0.0005, 0.0003, size=1200)
    result = circular_block_bootstrap(
        candidate,
        benchmark,
        samples=1000,
        block_length=6,
        random_seed=42,
    )
    assert result.observed_mean_difference > 0
    assert result.one_sided_pvalue < 0.05
    assert result.confidence_interval_low > 0


def test_block_bootstrap_does_not_promote_equal_returns() -> None:
    rng = np.random.default_rng(17)
    returns = rng.normal(0.0, 0.002, size=600)
    result = circular_block_bootstrap(
        returns,
        returns,
        samples=500,
        block_length=6,
        random_seed=3,
    )
    assert result.observed_mean_difference == 0
    assert result.one_sided_pvalue == 1.0
    assert result.confidence_interval_low == 0
    assert result.confidence_interval_high == 0


def test_fold_concentration_reports_dominant_profit() -> None:
    result = fold_concentration(np.asarray([0.10, 0.01, -0.02, 0.01]))
    assert result.positive_fold_ratio == 0.75
    assert result.top_fold_profit_share > 0.8
    assert result.top_three_fold_profit_share == 1.0


def test_fixed_regimes_are_descriptive_and_aligned() -> None:
    volatility = np.asarray([0.2, 0.6, 1.1, 0.2])
    trend = np.asarray([0.1, -0.1, 0.0, 0.0])
    regimes = classify_market_regimes(
        volatility,
        trend,
        low_volatility_threshold=0.45,
        high_volatility_threshold=0.90,
        trend_band=0.01,
    )
    assert regimes.tolist() == ["low_vol_up", "mid_vol_down", "high_vol_flat", "low_vol_flat"]
    summary = regime_performance(
        np.asarray([0.01, -0.01, 0.02, 0.0]),
        regimes,
        periods_per_year=2190,
    )
    assert set(summary["regime"]) == set(regimes)
    assert int(summary["observations"].sum()) == 4
