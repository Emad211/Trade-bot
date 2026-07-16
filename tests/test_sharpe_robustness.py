import numpy as np
import pytest

from hybrid_trader.sharpe_robustness import (
    annualized_sharpe_ratio,
    expected_maximum_sharpe,
    probabilistic_sharpe_ratio,
    sample_pearson_kurtosis,
    sample_skewness,
    sharpe_diagnostics,
)


def test_probabilistic_and_deflated_sharpe_are_conservative() -> None:
    rng = np.random.default_rng(7)
    returns = rng.normal(0.0010, 0.0060, size=1200)
    trial_sharpes = np.asarray([-0.2, 0.1, 0.4, 0.8, 1.1], dtype=np.float64)
    diagnostics = sharpe_diagnostics(
        returns,
        trial_annualized_sharpes=trial_sharpes,
        declared_trials=20,
        periods_per_year=2190,
    )
    assert diagnostics.annualized_sharpe > 0
    assert diagnostics.probabilistic_sharpe_ratio > 0.95
    assert 0 <= diagnostics.deflated_sharpe_ratio <= diagnostics.probabilistic_sharpe_ratio
    assert diagnostics.deflated_benchmark_annualized_sharpe > 0


def test_sample_shape_metrics_are_close_to_normal() -> None:
    rng = np.random.default_rng(99)
    returns = rng.normal(0, 0.01, size=50_000)
    assert abs(sample_skewness(returns)) < 0.05
    assert abs(sample_pearson_kurtosis(returns) - 3.0) < 0.08


def test_expected_maximum_sharpe_increases_with_trial_count() -> None:
    few = expected_maximum_sharpe(
        declared_trials=2,
        trial_sharpe_standard_deviation=0.25,
    )
    many = expected_maximum_sharpe(
        declared_trials=100,
        trial_sharpe_standard_deviation=0.25,
    )
    assert many > few > 0


def test_invalid_sharpe_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="zero-variance"):
        annualized_sharpe_ratio(np.ones(10), periods_per_year=2190)
    with pytest.raises(ValueError, match="zero-variance"):
        probabilistic_sharpe_ratio(np.ones(10), periods_per_year=2190)
    with pytest.raises(ValueError, match="declared_trials"):
        sharpe_diagnostics(
            np.linspace(-0.01, 0.02, 100),
            trial_annualized_sharpes=np.asarray([0.1, 0.2, 0.3]),
            declared_trials=2,
            periods_per_year=2190,
        )
