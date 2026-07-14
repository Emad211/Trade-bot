"""Strict OHLCV schema validation."""

from collections.abc import Iterable

import numpy as np
import pandas as pd

REQUIRED_OHLCV_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


class MarketDataError(ValueError):
    """Raised when market data violates a required invariant."""


def _missing_columns(columns: Iterable[str]) -> set[str]:
    return set(REQUIRED_OHLCV_COLUMNS).difference(columns)


def normalize_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate OHLCV bars and return a UTC-indexed, sorted copy."""

    missing = _missing_columns(frame.columns)
    if missing:
        raise MarketDataError(f"Missing OHLCV columns: {sorted(missing)}")

    data = frame.loc[:, list(REQUIRED_OHLCV_COLUMNS)].copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    if data["timestamp"].isna().any():
        raise MarketDataError("At least one timestamp is invalid")

    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    if data[numeric_columns].isna().any().any():
        raise MarketDataError("OHLCV contains non-numeric or missing values")
    if not np.isfinite(data[numeric_columns].to_numpy(dtype=float)).all():
        raise MarketDataError("OHLCV contains non-finite values")

    if (data[["open", "high", "low", "close"]] <= 0).any().any():
        raise MarketDataError("Prices must be strictly positive")
    if (data["volume"] < 0).any():
        raise MarketDataError("Volume cannot be negative")

    bar_max = data[["open", "close", "low"]].max(axis=1)
    bar_min = data[["open", "close", "high"]].min(axis=1)
    if (data["high"] < bar_max).any():
        raise MarketDataError("High is below another bar price")
    if (data["low"] > bar_min).any():
        raise MarketDataError("Low is above another bar price")

    data = data.sort_values("timestamp")
    if data["timestamp"].duplicated().any():
        raise MarketDataError("Duplicate timestamps are not allowed")

    data = data.set_index("timestamp")
    data.index.name = "timestamp"
    return data.astype(float)
