"""Predeclared market-regime labels and descriptive performance summaries."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from hybrid_trader.bootstrap_robustness import compounded_return
from hybrid_trader.sharpe_robustness import FloatVector, finite_returns


def classify_market_regimes(
    realized_volatility: FloatVector,
    ema_ratio: FloatVector,
    *,
    low_volatility_threshold: float,
    high_volatility_threshold: float,
    trend_band: float,
) -> NDArray[np.str_]:
    volatility = finite_returns(
        realized_volatility,
        name="realized_volatility",
        minimum_size=1,
    )
    trend = finite_returns(ema_ratio, name="ema_ratio", minimum_size=1)
    if volatility.size != trend.size:
        raise ValueError("Volatility and trend vectors must have equal length")
    if low_volatility_threshold >= high_volatility_threshold:
        raise ValueError("Low-volatility threshold must be below high-volatility threshold")
    if trend_band < 0:
        raise ValueError("trend_band cannot be negative")

    volatility_bucket = np.where(
        volatility < low_volatility_threshold,
        "low_vol",
        np.where(volatility >= high_volatility_threshold, "high_vol", "mid_vol"),
    )
    trend_bucket = np.where(
        trend > trend_band,
        "up",
        np.where(trend < -trend_band, "down", "flat"),
    )
    return np.char.add(np.char.add(volatility_bucket.astype(str), "_"), trend_bucket.astype(str))


def regime_performance(
    returns: FloatVector,
    regimes: NDArray[np.str_],
    *,
    periods_per_year: int,
) -> pd.DataFrame:
    values = finite_returns(returns, minimum_size=1)
    labels = np.asarray(regimes, dtype=str)
    if labels.ndim != 1 or labels.size != values.size:
        raise ValueError("Regime labels and returns must be aligned one-dimensional vectors")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")

    rows: list[dict[str, float | int | str]] = []
    for label in sorted(set(labels.tolist())):
        subset = values[labels == label]
        standard_deviation = float(subset.std(ddof=1)) if subset.size > 1 else 0.0
        sharpe = (
            float(subset.mean() / standard_deviation * math.sqrt(periods_per_year))
            if standard_deviation > 0
            else 0.0
        )
        rows.append(
            {
                "regime": label,
                "observations": int(subset.size),
                "compounded_return": compounded_return(subset),
                "mean_return": float(subset.mean()),
                "annualized_sharpe": sharpe,
                "positive_return_ratio": float(np.mean(subset > 0)),
            }
        )
    return pd.DataFrame(rows).sort_values("regime").reset_index(drop=True)
