"""Leakage-safe derivatives and market-regime feature engineering."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DerivativesRegimeSpec:
    """Backward-looking windows and thresholds for deterministic regime features."""

    short_window: int = 6
    medium_window: int = 24
    long_window: int = 126
    crowding_threshold: float = 1.5
    deleveraging_threshold: float = 1.25
    high_volatility_threshold: float = 1.0

    def __post_init__(self) -> None:
        if not 1 <= self.short_window < self.medium_window < self.long_window:
            raise ValueError("Regime windows must satisfy 1 <= short < medium < long")
        if self.crowding_threshold <= 0:
            raise ValueError("crowding_threshold must be positive")
        if self.deleveraging_threshold <= 0:
            raise ValueError("deleveraging_threshold must be positive")
        if self.high_volatility_threshold <= 0:
            raise ValueError("high_volatility_threshold must be positive")


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(frame[column], errors="coerce").astype(float)
    finite_or_missing = np.isfinite(values.to_numpy(dtype=float)) | values.isna().to_numpy()
    if not finite_or_missing.all():
        raise ValueError(f"{column} contains non-finite values")
    return values


def _rolling_zscore(values: pd.Series, window: int) -> pd.Series:
    mean = values.rolling(window, min_periods=window).mean()
    std = values.rolling(window, min_periods=window).std(ddof=0).replace(0.0, np.nan)
    return (values - mean) / std


def _mean_available(components: list[pd.Series], index: pd.Index) -> pd.Series:
    if not components:
        return pd.Series(np.nan, index=index, dtype=float)
    return pd.concat(components, axis=1).mean(axis=1, skipna=True)


def add_derivatives_regime_features(
    frame: pd.DataFrame,
    spec: DerivativesRegimeSpec | None = None,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Add derivatives crowding and market-regime features using current/past data only.

    Missing optional source columns remain absent. At least one derivatives source
    (`funding_rate`, `open_interest`, or `basis`) is required so a regime experiment
    cannot silently degrade into the market-only baseline.
    """

    settings = spec or DerivativesRegimeSpec()
    if frame.empty:
        raise ValueError("Regime feature frame cannot be empty")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Regime feature frame index must be unique and sorted")
    derivatives = {"funding_rate", "open_interest", "basis"}.intersection(frame.columns)
    if not derivatives:
        raise ValueError("At least one derivatives feature source is required")

    result = frame.copy()
    features: list[str] = []
    long_components: list[pd.Series] = []
    short_components: list[pd.Series] = []
    deleveraging_components: list[pd.Series] = []

    if "funding_rate" in result:
        funding = _numeric(result, "funding_rate")
        result["funding_mean"] = funding.rolling(
            settings.medium_window, min_periods=settings.medium_window
        ).mean()
        result["funding_change"] = funding.diff(settings.short_window)
        result["funding_zscore"] = _rolling_zscore(funding, settings.long_window)
        features.extend(("funding_mean", "funding_change", "funding_zscore"))
        long_components.append(result["funding_zscore"].clip(lower=0.0))
        short_components.append((-result["funding_zscore"]).clip(lower=0.0))

    if "basis" in result:
        basis = _numeric(result, "basis")
        result["basis_mean"] = basis.rolling(
            settings.medium_window, min_periods=settings.medium_window
        ).mean()
        result["basis_change"] = basis.diff(settings.short_window)
        result["basis_zscore"] = _rolling_zscore(basis, settings.long_window)
        features.extend(("basis_mean", "basis_change", "basis_zscore"))
        long_components.append(result["basis_zscore"].clip(lower=0.0))
        short_components.append((-result["basis_zscore"]).clip(lower=0.0))

    if "open_interest" in result:
        open_interest = _numeric(result, "open_interest")
        if (open_interest.dropna() < 0).any():
            raise ValueError("open_interest cannot be negative")
        log_open_interest = np.log(open_interest.where(open_interest > 0))
        result["open_interest_log_change_1"] = log_open_interest.diff()
        result["open_interest_log_change_short"] = log_open_interest.diff(settings.short_window)
        result["open_interest_log_change_medium"] = log_open_interest.diff(settings.medium_window)
        result["open_interest_change_zscore"] = _rolling_zscore(
            result["open_interest_log_change_1"], settings.long_window
        )
        features.extend(
            (
                "open_interest_log_change_1",
                "open_interest_log_change_short",
                "open_interest_log_change_medium",
                "open_interest_change_zscore",
            )
        )
        buildup = result["open_interest_change_zscore"].clip(lower=0.0)
        long_components.append(buildup)
        short_components.append(buildup)
        deleveraging_components.append((-result["open_interest_change_zscore"]).clip(lower=0.0))

    if "realized_volatility" in result:
        volatility = _numeric(result, "realized_volatility")
        result["volatility_zscore"] = _rolling_zscore(volatility, settings.long_window)
        features.append("volatility_zscore")
        deleveraging_components.append(result["volatility_zscore"].clip(lower=0.0))

    result["long_crowding_score"] = _mean_available(long_components, result.index)
    result["short_crowding_score"] = _mean_available(short_components, result.index)
    result["deleveraging_score"] = _mean_available(deleveraging_components, result.index)
    features.extend(("long_crowding_score", "short_crowding_score", "deleveraging_score"))

    result["regime_crowded_long"] = (
        result["long_crowding_score"] >= settings.crowding_threshold
    ).astype(float)
    result["regime_crowded_short"] = (
        result["short_crowding_score"] >= settings.crowding_threshold
    ).astype(float)
    result["regime_deleveraging"] = (
        result["deleveraging_score"] >= settings.deleveraging_threshold
    ).astype(float)
    features.extend(("regime_crowded_long", "regime_crowded_short", "regime_deleveraging"))

    if "volatility_zscore" in result:
        result["regime_high_volatility"] = (
            result["volatility_zscore"] >= settings.high_volatility_threshold
        ).astype(float)
        features.append("regime_high_volatility")
    if "ema_ratio" in result:
        trend = _numeric(result, "ema_ratio")
        result["regime_trend_up"] = (trend > 0).astype(float)
        result["regime_trend_down"] = (trend < 0).astype(float)
        features.extend(("regime_trend_up", "regime_trend_down"))

    return result, tuple(features)
