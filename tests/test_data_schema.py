import numpy as np
import pandas as pd
import pytest

from hybrid_trader.data.schema import MarketDataError, normalize_ohlcv


def test_normalize_sorts_and_indexes(ohlcv: pd.DataFrame) -> None:
    normalized = normalize_ohlcv(ohlcv.sample(frac=1.0, random_state=1))
    assert normalized.index.is_monotonic_increasing
    assert str(normalized.index.tz) == "UTC"
    assert list(normalized.columns) == ["open", "high", "low", "close", "volume"]


def test_rejects_impossible_high(ohlcv: pd.DataFrame) -> None:
    broken = ohlcv.copy()
    broken.loc[0, "high"] = broken.loc[0, "low"] / 2
    with pytest.raises(MarketDataError, match="High"):
        normalize_ohlcv(broken)


def test_rejects_impossible_low(ohlcv: pd.DataFrame) -> None:
    broken = ohlcv.copy()
    broken.loc[0, "high"] = max(broken.loc[0, "open"], broken.loc[0, "close"]) * 1.02
    broken.loc[0, "low"] = max(broken.loc[0, "open"], broken.loc[0, "close"]) * 1.01
    with pytest.raises(MarketDataError, match="Low"):
        normalize_ohlcv(broken)


def test_rejects_duplicates(ohlcv: pd.DataFrame) -> None:
    duplicate = pd.concat([ohlcv, ohlcv.iloc[[0]]], ignore_index=True)
    with pytest.raises(MarketDataError, match="Duplicate"):
        normalize_ohlcv(duplicate)


def test_rejects_non_finite_values(ohlcv: pd.DataFrame) -> None:
    broken = ohlcv.copy()
    broken.loc[0, "close"] = np.inf
    with pytest.raises(MarketDataError, match="non-finite"):
        normalize_ohlcv(broken)
