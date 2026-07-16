"""Probabilistic and deflated Sharpe diagnostics for sealed returns."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatVector = NDArray[np.float64]


@dataclass(frozen=True)
class SharpeDiagnostics:
    observations: int
    annualized_sharpe: float
    skewness: float
    pearson_kurtosis: float
    probabilistic_sharpe_ratio: float
    deflated_sharpe_ratio: float
    deflated_benchmark_annualized_sharpe: float


def finite_vector(
    values: NDArray[np.floating[Any]] | list[float] | tuple[float, ...],
    *,
    name: str,
    minimum_size: int,
) -> FloatVector:
    vector = np.asarray(values, dtype=np.float64)
    if vector.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if vector.size < minimum_size:
        raise ValueError(f"{name} requires at least {minimum_size} observations")
    if not np.isfinite(vector).all():
        raise ValueError(f"{name} must contain only finite values")
    return vector


def finite_returns(
    values: NDArray[np.floating[Any]] | list[float] | tuple[float, ...],
    *,
    name: str = "returns",
    minimum_size: int = 3,
) -> FloatVector:
    vector = finite_vector(values, name=name, minimum_size=minimum_size)
    if (vector <= -1.0).any():
        raise ValueError(f"{name} cannot contain returns at or below -100%")
    return vector


def sample_skewness(returns: FloatVector) -> float:
    values = finite_returns(returns, minimum_size=3)
    observations = values.size
    standard_deviation = float(values.std(ddof=1))
    if standard_deviation == 0:
        return 0.0
    standardized = (values - values.mean()) / standard_deviation
    correction = observations / ((observations - 1) * (observations - 2))
    return float(correction * np.sum(standardized**3))


def sample_pearson_kurtosis(returns: FloatVector) -> float:
    values = finite_returns(returns, minimum_size=4)
    observations = values.size
    centered = values - values.mean()
    second_moment = float(np.mean(centered**2))
    if second_moment == 0:
        return 3.0
    fourth_moment = float(np.mean(centered**4))
    biased_excess = fourth_moment / second_moment**2 - 3.0
    unbiased_excess = (
        (observations - 1)
        / ((observations - 2) * (observations - 3))
        * ((observations + 1) * biased_excess + 6.0)
    )
    return float(unbiased_excess + 3.0)


def annualized_sharpe_ratio(returns: FloatVector, *, periods_per_year: int) -> float:
    values = finite_returns(returns)
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    standard_deviation = float(values.std(ddof=1))
    if standard_deviation == 0:
        raise ValueError("Sharpe ratio is undefined for zero-variance returns")
    return float(values.mean() / standard_deviation * math.sqrt(periods_per_year))


def probabilistic_sharpe_ratio(
    returns: FloatVector,
    *,
    benchmark_annualized_sharpe: float = 0.0,
    periods_per_year: int,
) -> float:
    """Estimate the probability that the true Sharpe exceeds a benchmark."""

    values = finite_returns(returns, minimum_size=4)
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    standard_deviation = float(values.std(ddof=1))
    if standard_deviation == 0:
        raise ValueError("Probabilistic Sharpe is undefined for zero-variance returns")
    observed_sharpe = float(values.mean() / standard_deviation)
    benchmark_sharpe = benchmark_annualized_sharpe / math.sqrt(periods_per_year)
    skewness = sample_skewness(values)
    kurtosis = sample_pearson_kurtosis(values)
    denominator_squared = (
        1.0 - skewness * observed_sharpe + ((kurtosis - 1.0) / 4.0) * observed_sharpe**2
    )
    if denominator_squared <= 0:
        return float(observed_sharpe > benchmark_sharpe)
    statistic = (
        (observed_sharpe - benchmark_sharpe)
        * math.sqrt(values.size - 1)
        / math.sqrt(denominator_squared)
    )
    return float(NormalDist().cdf(statistic))


def expected_maximum_sharpe(
    *, declared_trials: int, trial_sharpe_standard_deviation: float
) -> float:
    """Expected maximum Sharpe under repeated trials, in the supplied units."""

    if declared_trials < 2:
        raise ValueError("declared_trials must be at least two")
    if not math.isfinite(trial_sharpe_standard_deviation) or trial_sharpe_standard_deviation < 0:
        raise ValueError("trial_sharpe_standard_deviation must be finite and non-negative")
    if trial_sharpe_standard_deviation == 0:
        return 0.0
    euler_gamma = 0.5772156649015329
    normal = NormalDist()
    first = normal.inv_cdf(1.0 - 1.0 / declared_trials)
    second = normal.inv_cdf(1.0 - 1.0 / (declared_trials * math.e))
    return float(
        trial_sharpe_standard_deviation * ((1.0 - euler_gamma) * first + euler_gamma * second)
    )


def sharpe_diagnostics(
    returns: FloatVector,
    *,
    trial_annualized_sharpes: FloatVector,
    declared_trials: int,
    periods_per_year: int,
) -> SharpeDiagnostics:
    values = finite_returns(returns, minimum_size=4)
    trial_sharpes = finite_vector(
        trial_annualized_sharpes,
        name="trial_annualized_sharpes",
        minimum_size=2,
    )
    if declared_trials < trial_sharpes.size:
        raise ValueError("declared_trials cannot be smaller than the supplied trial count")
    annualized_sharpe = annualized_sharpe_ratio(values, periods_per_year=periods_per_year)
    trial_per_period = trial_sharpes / math.sqrt(periods_per_year)
    trial_standard_deviation = float(trial_per_period.std(ddof=1))
    deflated_benchmark_per_period = expected_maximum_sharpe(
        declared_trials=declared_trials,
        trial_sharpe_standard_deviation=trial_standard_deviation,
    )
    deflated_benchmark_annualized = deflated_benchmark_per_period * math.sqrt(periods_per_year)
    return SharpeDiagnostics(
        observations=int(values.size),
        annualized_sharpe=annualized_sharpe,
        skewness=sample_skewness(values),
        pearson_kurtosis=sample_pearson_kurtosis(values),
        probabilistic_sharpe_ratio=probabilistic_sharpe_ratio(
            values,
            benchmark_annualized_sharpe=0.0,
            periods_per_year=periods_per_year,
        ),
        deflated_sharpe_ratio=probabilistic_sharpe_ratio(
            values,
            benchmark_annualized_sharpe=deflated_benchmark_annualized,
            periods_per_year=periods_per_year,
        ),
        deflated_benchmark_annualized_sharpe=float(deflated_benchmark_annualized),
    )
