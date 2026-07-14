from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from hybrid_trader.data.ccxt_source import CCXTOHLCVSource


class FakeSpotExchange:
    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        del symbol, timeframe, since, limit
        base = 1_700_000_000_000
        step = 4 * 60 * 60 * 1000
        return [
            [base + index * step, 100 + index, 102 + index, 99 + index, 101 + index, 10]
            for index in range(4)
        ]


def test_fetch_drops_forming_bar(monkeypatch: pytest.MonkeyPatch) -> None:
    source = CCXTOHLCVSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: FakeSpotExchange())
    base = pd.Timestamp(1_700_000_000_000, unit="ms", tz="UTC")
    now = (base + pd.Timedelta(hours=13)).to_pydatetime()
    result = source.fetch("BTC/USD", "4h", max_pages=1, now=now)
    assert len(result) == 3


def test_fetch_point_in_time_applies_source_latency(monkeypatch: pytest.MonkeyPatch) -> None:
    source = CCXTOHLCVSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: FakeSpotExchange())
    base = pd.Timestamp(1_700_000_000_000, unit="ms", tz="UTC")
    now = (base + pd.Timedelta(hours=20)).to_pydatetime()
    result = source.fetch_point_in_time(
        "BTC/USD", "4h", source_latency=timedelta(seconds=30), max_pages=1, now=now
    )
    assert result["available_at"].iloc[0] == result.index[0] + pd.Timedelta(hours=4, seconds=30)


def test_fetch_rejects_empty_exchange_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class Empty:
        def fetch_ohlcv(self, symbol, timeframe, since, limit):
            del symbol, timeframe, since, limit
            return []

    source = CCXTOHLCVSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: Empty())
    with pytest.raises(RuntimeError, match="no OHLCV"):
        source.fetch("BTC/USD", "4h", max_pages=1, now=datetime.now(UTC))
