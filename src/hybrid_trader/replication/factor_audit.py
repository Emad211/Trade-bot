"""Audits for published factor files and volatility-management formulas."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VintageComparison:
    column: str
    overlap_count: int
    correlation: float
    mean_absolute_difference: float
    max_absolute_difference: float
    changed_count: int


def _clean_returns(values: pd.Series) -> pd.Series:
    result = pd.to_numeric(values, errors="coerce").dropna().astype(float)
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError("Returns contain non-finite values")
    return result


def annualized_metrics(returns: pd.Series, *, periods_per_year: int = 12) -> dict[str, float | int]:
    clean = _clean_returns(returns)
    if len(clean) < 2:
        raise ValueError("At least two returns are required")
    mean = float(clean.mean())
    volatility = float(clean.std(ddof=1))
    annual_mean = mean * periods_per_year
    annual_volatility = volatility * math.sqrt(periods_per_year)
    sharpe = annual_mean / annual_volatility if annual_volatility > 0 else float("nan")
    wealth = (1.0 + clean).cumprod()
    drawdown = wealth / wealth.cummax() - 1.0
    return {
        "count": len(clean),
        "annualized_mean": annual_mean,
        "annualized_volatility": annual_volatility,
        "annualized_sharpe": float(sharpe),
        "maximum_drawdown": float(drawdown.min()),
        "skewness": float(cast(float, clean.skew())),
        "excess_kurtosis": float(cast(float, clean.kurt())),
        "positive_fraction": float((clean > 0).mean()),
    }


def compare_factor_vintages(
    original: pd.DataFrame,
    maintained: pd.DataFrame,
    *,
    date_column: str = "date",
    value_columns: Iterable[str] | None = None,
    tolerance: float = 1e-12,
) -> list[VintageComparison]:
    if date_column not in original or date_column not in maintained:
        raise ValueError(f"Both inputs must contain {date_column!r}")
    if original[date_column].duplicated().any() or maintained[date_column].duplicated().any():
        raise ValueError("Factor vintages contain duplicate dates")

    merged = original.merge(maintained, on=date_column, suffixes=("_original", "_maintained"))
    if merged.empty:
        raise ValueError("Factor vintages have no overlapping dates")

    if value_columns is None:
        column_names = [str(column) for column in merged.columns]
        left = {
            column.removesuffix("_original")
            for column in column_names
            if column.endswith("_original")
        }
        right = {
            column.removesuffix("_maintained")
            for column in column_names
            if column.endswith("_maintained")
        }
        selected = sorted(left & right)
    else:
        selected = list(value_columns)
    if not selected:
        raise ValueError("No common factor columns were selected")

    results: list[VintageComparison] = []
    for column in selected:
        first = pd.to_numeric(merged[f"{column}_original"], errors="coerce")
        second = pd.to_numeric(merged[f"{column}_maintained"], errors="coerce")
        valid = first.notna() & second.notna()
        if valid.sum() < 2:
            continue
        difference = (first.loc[valid] - second.loc[valid]).abs()
        results.append(
            VintageComparison(
                column=column,
                overlap_count=int(valid.sum()),
                correlation=float(first.loc[valid].corr(second.loc[valid])),
                mean_absolute_difference=float(difference.mean()),
                max_absolute_difference=float(difference.max()),
                changed_count=int((difference > tolerance).sum()),
            )
        )
    if not results:
        raise ValueError("No factor column had sufficient overlap")
    return results


def volatility_managed_returns(
    returns: pd.Series,
    *,
    variance_lookback: int = 12,
    calibration_observations: int,
    max_leverage: float | None = None,
) -> pd.DataFrame:
    """Construct a recursive inverse-variance overlay.

    The scaling constant is estimated only on the declared calibration window and
    then frozen. This is a baseline formula audit, not a claim of exact replication
    for every specification in the literature.
    """

    if variance_lookback < 2:
        raise ValueError("variance_lookback must be at least 2")
    if calibration_observations <= variance_lookback:
        raise ValueError("calibration_observations must exceed variance_lookback")
    if max_leverage is not None and max_leverage <= 0:
        raise ValueError("max_leverage must be positive")

    clean = pd.to_numeric(returns, errors="coerce").astype(float)
    lagged_variance = clean.rolling(variance_lookback, min_periods=variance_lookback).var(ddof=1).shift(1)
    raw_weight = 1.0 / lagged_variance.replace(0.0, np.nan)
    calibration = pd.DataFrame({"return": clean, "raw_weight": raw_weight}).iloc[
        :calibration_observations
    ].dropna()
    if len(calibration) < 2:
        raise ValueError("Insufficient calibration observations")

    raw_managed_calibration = calibration["return"] * calibration["raw_weight"]
    target_vol = calibration["return"].std(ddof=1)
    raw_vol = raw_managed_calibration.std(ddof=1)
    if not np.isfinite(raw_vol) or raw_vol <= 0:
        raise ValueError("Cannot calibrate inverse-variance scaling")
    scale = float(target_vol / raw_vol)
    weight = raw_weight * scale
    if max_leverage is not None:
        weight = weight.clip(lower=-max_leverage, upper=max_leverage)
    managed = weight * clean
    return pd.DataFrame(
        {
            "base_return": clean,
            "lagged_variance": lagged_variance,
            "weight": weight,
            "managed_return": managed,
            "calibration": np.arange(len(clean)) < calibration_observations,
        },
        index=returns.index,
    )
