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


def test_rejects_duplicates(ohlcv: pd.DataFrame) -> None:
    duplicate = pd.concat([ohlcv, ohlcv.iloc[[0]]], ignore_index=True)
    with pytest.raises(MarketDataError, match="Duplicate"):
        normalize_ohlcv(duplicate)
