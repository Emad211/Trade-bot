"""Point-in-time market-data contracts."""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from hybrid_trader.data.schema import MarketDataError, normalize_ohlcv
from hybrid_trader.data.timeframe import timeframe_to_timedelta

PIT_COLUMNS = ("open_available_at", "available_at")


def add_bar_availability(
    frame: pd.DataFrame,
    *,
    timeframe: str,
    source_latency: timedelta = timedelta(0),
) -> pd.DataFrame:
    """Normalize OHLCV and attach conservative observation timestamps."""

    if source_latency < timedelta(0):
        raise ValueError("source_latency cannot be negative")
    normalized = normalize_ohlcv(frame.reset_index() if "timestamp" not in frame else frame)
    interval = timeframe_to_timedelta(timeframe)
    result = normalized.copy()
    result["open_available_at"] = result.index + source_latency
    result["available_at"] = result.index + interval + source_latency
    return result


def validate_point_in_time_bars(
    frame: pd.DataFrame,
    *,
    timeframe: str,
    require_regular: bool = True,
) -> pd.DataFrame:
    """Validate a UTC-indexed point-in-time OHLCV frame."""

    missing = set(PIT_COLUMNS).difference(frame.columns)
    if missing:
        raise MarketDataError(f"Missing point-in-time columns: {sorted(missing)}")
    result = frame.copy()
    if not isinstance(result.index, pd.DatetimeIndex):
        result.index = pd.to_datetime(result.index, utc=True, errors="coerce")
    else:
        result.index = pd.to_datetime(result.index, utc=True, errors="coerce")
    if np.asarray(pd.isna(result.index), dtype=bool).any():
        raise MarketDataError("Point-in-time index contains invalid timestamps")
    for column in PIT_COLUMNS:
        values = pd.to_datetime(result[column], utc=True, errors="coerce", format="mixed")
        if values.isna().any():
            raise MarketDataError(f"{column} contains invalid timestamps")
        result[column] = values
    if not result.index.is_monotonic_increasing:
        raise MarketDataError("Point-in-time bars must be sorted")
    if result.index.has_duplicates:
        raise MarketDataError("Point-in-time bars cannot contain duplicate timestamps")
    if (result["open_available_at"] < result.index).any():
        raise MarketDataError("open_available_at cannot precede the bar open")
    if (result["available_at"] <= result["open_available_at"]).any():
        raise MarketDataError("available_at must be later than open_available_at")
    if not result["available_at"].is_monotonic_increasing:
        raise MarketDataError("available_at must be monotonic")
    if require_regular and len(result) > 1:
        expected = pd.Timedelta(timeframe_to_timedelta(timeframe))
        observed = result.index.to_series().diff().dropna()
        if not observed.eq(expected).all():
            examples = observed.loc[~observed.eq(expected)].head(3).astype(str).tolist()
            raise MarketDataError(f"Irregular bar spacing; expected {expected}, got {examples}")
    return result


def closed_bars_as_of(frame: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Return only bars whose full OHLCV was observable by ``as_of``."""

    cutoff = pd.Timestamp(as_of)
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    if "available_at" not in frame:
        raise MarketDataError("available_at is required")
    return frame.loc[pd.to_datetime(frame["available_at"], utc=True) <= cutoff].copy()
