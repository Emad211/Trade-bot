"""Execution-aligned forward return, volatility, drawdown and liquidity targets."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RiskTargetSpec:
    execution_delay_bars: int = 1
    horizon_bars: int = 6
    periods_per_year: int = 2190
    liquidity_lookback_bars: int = 42

    def __post_init__(self) -> None:
        if self.execution_delay_bars < 0:
            raise ValueError("execution_delay_bars cannot be negative")
        if self.horizon_bars <= 0:
            raise ValueError("horizon_bars must be positive")
        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        if self.liquidity_lookback_bars <= 1:
            raise ValueError("liquidity_lookback_bars must be greater than one")

    @property
    def entry_offset(self) -> int:
        return 1 + self.execution_delay_bars

    @property
    def exit_offset(self) -> int:
        return self.entry_offset + self.horizon_bars


def add_forward_risk_targets(
    frame: pd.DataFrame,
    spec: RiskTargetSpec | None = None,
) -> pd.DataFrame:
    """Add continuous forward targets with explicit target-availability timestamps."""

    settings = spec or RiskTargetSpec()
    required = {"open", "volume", "open_available_at", "available_at"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Risk target frame missing columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Risk target frame cannot be empty")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Risk target frame index must be unique and sorted")

    result = frame.copy()
    result["decision_time"] = pd.to_datetime(result["available_at"], utc=True)
    open_price = pd.to_numeric(result["open"], errors="coerce").astype(float)
    volume = pd.to_numeric(result["volume"], errors="coerce").astype(float)
    if (open_price.dropna() <= 0).any():
        raise ValueError("Open prices must be positive")
    if (volume.dropna() < 0).any():
        raise ValueError("Volume cannot be negative")

    entry = open_price.shift(-settings.entry_offset)
    exit_price = open_price.shift(-settings.exit_offset)
    result["risk_entry_time"] = pd.Series(result.index, index=result.index).shift(
        -settings.entry_offset
    )
    result["risk_exit_time"] = pd.Series(result.index, index=result.index).shift(
        -settings.exit_offset
    )
    result["risk_entry_available_at"] = result["open_available_at"].shift(-settings.entry_offset)
    result["risk_label_available_at"] = result["open_available_at"].shift(-settings.exit_offset)
    result["target_return_horizon"] = exit_price / entry - 1.0
    result["target_log_return_horizon"] = np.log(exit_price / entry)
    result["target_abs_return_horizon"] = result["target_return_horizon"].abs()

    future_return_series: list[pd.Series] = []
    for offset in range(settings.entry_offset + 1, settings.exit_offset + 1):
        ratio = open_price.shift(-offset) / open_price.shift(-(offset - 1))
        future_return_series.append(
            pd.Series(
                np.log(ratio.to_numpy(dtype=float)),
                index=result.index,
                name=f"future_open_return_{offset}",
                dtype=float,
            )
        )
    future_log_returns = pd.concat(future_return_series, axis=1)
    squared = future_log_returns.pow(2)
    result["target_realized_volatility"] = np.sqrt(
        squared.mean(axis=1, skipna=False) * settings.periods_per_year
    )
    downside = future_log_returns.clip(upper=0.0).pow(2)
    result["target_downside_volatility"] = np.sqrt(
        downside.mean(axis=1, skipna=False) * settings.periods_per_year
    )

    future_paths = pd.concat(
        [
            (open_price.shift(-(settings.entry_offset + step)) / entry - 1.0).rename(
                f"future_path_{step}"
            )
            for step in range(settings.horizon_bars + 1)
        ],
        axis=1,
    )
    result["target_max_drawdown"] = future_paths.min(axis=1, skipna=False)
    result["target_max_runup"] = future_paths.max(axis=1, skipna=False)

    future_volume = pd.concat(
        [
            volume.shift(-(settings.entry_offset + step)).rename(f"future_volume_{step}")
            for step in range(settings.horizon_bars)
        ],
        axis=1,
    )
    result["target_mean_volume"] = future_volume.mean(axis=1, skipna=False)
    known_volume = volume.rolling(
        settings.liquidity_lookback_bars,
        min_periods=settings.liquidity_lookback_bars,
    ).mean()
    result["target_volume_ratio"] = result["target_mean_volume"] / known_volume.replace(0.0, np.nan)
    volume_available_at = result["available_at"].shift(-(settings.exit_offset - 1))
    result["risk_label_available_at"] = pd.concat(
        [
            pd.to_datetime(result["risk_label_available_at"], utc=True),
            pd.to_datetime(volume_available_at, utc=True),
        ],
        axis=1,
    ).max(axis=1)

    valid = result["risk_label_available_at"].notna()
    if (
        pd.to_datetime(result.loc[valid, "risk_entry_available_at"], utc=True)
        < result.loc[valid, "decision_time"]
    ).any():
        raise ValueError("Risk target contract permits entry before the decision")
    if (
        pd.to_datetime(result.loc[valid, "risk_label_available_at"], utc=True)
        <= pd.to_datetime(result.loc[valid, "risk_entry_available_at"], utc=True)
    ).any():
        raise ValueError("Risk targets must become available after entry")
    return result
