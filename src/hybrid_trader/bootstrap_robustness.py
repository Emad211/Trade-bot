"""Dependence-aware bootstrap and fold-concentration diagnostics."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from hybrid_trader.sharpe_robustness import FloatVector, finite_returns


@dataclass(frozen=True)
class BootstrapResult:
    observations: int
    samples: int
    block_length: int
    observed_mean_difference: float
    one_sided_pvalue: float
    confidence_interval_low: float
    confidence_interval_high: float


@dataclass(frozen=True)
class FoldConcentration:
    folds: int
    positive_fold_ratio: float
    total_compounded_return: float
    total_positive_fold_profit: float
    top_fold_profit_share: float
    top_three_fold_profit_share: float
    positive_profit_hhi: float


def circular_block_bootstrap(
    candidate_returns: FloatVector,
    benchmark_returns: FloatVector,
    *,
    samples: int,
    block_length: int,
    random_seed: int,
    batch_size: int = 256,
) -> BootstrapResult:
    """Test candidate-minus-benchmark mean returns using circular blocks.

    Centered return differentials produce the one-sided null distribution. The
    uncentered bootstrap distribution provides a descriptive 95% confidence interval.
    Work is batched to avoid allocating a samples-by-history-sized index matrix.
    """

    candidate = finite_returns(candidate_returns, name="candidate_returns", minimum_size=30)
    benchmark = finite_returns(benchmark_returns, name="benchmark_returns", minimum_size=30)
    if candidate.size != benchmark.size:
        raise ValueError("Candidate and benchmark returns must have equal length")
    if samples < 100:
        raise ValueError("samples must be at least 100")
    if block_length < 1 or block_length > candidate.size:
        raise ValueError("block_length must be inside [1, observations]")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    differential = candidate - benchmark
    observed_mean = float(differential.mean())
    centered = differential - observed_mean
    observations = differential.size
    block_count = math.ceil(observations / block_length)
    offsets = np.arange(block_length, dtype=np.int64)
    rng = np.random.default_rng(random_seed)
    centered_means = np.empty(samples, dtype=np.float64)
    raw_means = np.empty(samples, dtype=np.float64)

    written = 0
    while written < samples:
        current = min(batch_size, samples - written)
        starts = rng.integers(0, observations, size=(current, block_count), dtype=np.int64)
        indices = (starts[:, :, None] + offsets[None, None, :]) % observations
        flattened = indices.reshape(current, -1)[:, :observations]
        centered_means[written : written + current] = centered[flattened].mean(axis=1)
        raw_means[written : written + current] = differential[flattened].mean(axis=1)
        written += current

    pvalue = float((1 + int(np.count_nonzero(centered_means >= observed_mean))) / (samples + 1))
    lower, upper = np.quantile(raw_means, [0.025, 0.975])
    return BootstrapResult(
        observations=int(observations),
        samples=samples,
        block_length=block_length,
        observed_mean_difference=observed_mean,
        one_sided_pvalue=pvalue,
        confidence_interval_low=float(lower),
        confidence_interval_high=float(upper),
    )


def compounded_return(returns: FloatVector) -> float:
    values = finite_returns(returns, minimum_size=1)
    return float(np.prod(1.0 + values) - 1.0)


def fold_concentration(fold_compounded_returns: FloatVector) -> FoldConcentration:
    fold_returns = finite_returns(
        fold_compounded_returns,
        name="fold_compounded_returns",
        minimum_size=1,
    )
    positive = np.clip(fold_returns, 0.0, None)
    positive_total = float(positive.sum())
    if positive_total > 0:
        shares = np.sort(positive / positive_total)[::-1]
        top_one = float(shares[0])
        top_three = float(shares[:3].sum())
        hhi = float(np.sum(shares**2))
    else:
        top_one = 1.0
        top_three = 1.0
        hhi = 1.0
    return FoldConcentration(
        folds=int(fold_returns.size),
        positive_fold_ratio=float(np.mean(fold_returns > 0)),
        total_compounded_return=float(np.prod(1.0 + fold_returns) - 1.0),
        total_positive_fold_profit=positive_total,
        top_fold_profit_share=top_one,
        top_three_fold_profit_share=top_three,
        positive_profit_hhi=hhi,
    )
