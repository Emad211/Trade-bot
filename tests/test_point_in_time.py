from datetime import timedelta

import pandas as pd
import pytest

from hybrid_trader.data.point_in_time import (
    add_bar_availability,
    closed_bars_as_of,
    validate_point_in_time_bars,
)
from hybrid_trader.data.schema import MarketDataError


def test_adds_distinct_open_and_close_availability(ohlcv: pd.DataFrame) -> None:
    result = add_bar_availability(
        ohlcv,
        timeframe="4h",
        source_latency=timedelta(seconds=30),
    )
    assert result["open_available_at"].iloc[0] == result.index[0] + pd.Timedelta(seconds=30)
    assert result["available_at"].iloc[0] == result.index[0] + pd.Timedelta(hours=4, seconds=30)


def test_closed_bars_respects_as_of(pit_ohlcv: pd.DataFrame) -> None:
    cutoff = pit_ohlcv["available_at"].iloc[9]
    result = closed_bars_as_of(pit_ohlcv, cutoff)
    assert len(result) == 10
    assert result["available_at"].max() <= cutoff


def test_rejects_irregular_bars(pit_ohlcv: pd.DataFrame) -> None:
    broken = pit_ohlcv.drop(pit_ohlcv.index[10])
    with pytest.raises(MarketDataError, match="Irregular"):
        validate_point_in_time_bars(broken, timeframe="4h")


def test_rejects_availability_before_open(pit_ohlcv: pd.DataFrame) -> None:
    broken = pit_ohlcv.copy()
    broken.loc[broken.index[0], "open_available_at"] = broken.index[0] - pd.Timedelta(seconds=1)
    with pytest.raises(MarketDataError, match="precede"):
        validate_point_in_time_bars(broken, timeframe="4h")


def test_rejects_close_availability_before_open_availability(pit_ohlcv: pd.DataFrame) -> None:
    broken = pit_ohlcv.copy()
    broken.loc[broken.index[0], "available_at"] = broken.loc[broken.index[0], "open_available_at"]
    with pytest.raises(MarketDataError, match="later"):
        validate_point_in_time_bars(broken, timeframe="4h")
