from datetime import timedelta
from typing import ClassVar

import pandas as pd
import pytest

from hybrid_trader.data.derivatives import CCXTDerivativesSource, UnsupportedPublicEndpoint


class FakeDerivativesExchange:
    id = "fake"
    has: ClassVar[dict[str, bool]] = {
        "fetchFundingRateHistory": True,
        "fetchOpenInterestHistory": True,
        "fetchMarkOHLCV": True,
        "fetchIndexOHLCV": True,
    }

    def fetch_funding_rate_history(
        self, symbol: str, since: int | None, limit: int, params: dict[str, object]
    ) -> list[dict[str, object]]:
        del symbol, since, limit, params
        return [
            {"timestamp": 1_700_000_000_000, "fundingRate": 0.0001},
            {"timestamp": 1_700_028_800_000, "fundingRate": -0.0002},
        ]

    def fetch_open_interest_history(
        self,
        symbol: str,
        timeframe: str,
        since: int | None,
        limit: int,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        del symbol, timeframe, since, limit, params
        return [
            {"timestamp": 1_700_000_000_000, "openInterestValue": 1_000_000.0},
            {"timestamp": 1_700_014_400_000, "openInterestAmount": 100.0},
        ]

    def fetch_mark_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int | None,
        limit: int,
        params: dict[str, object],
    ) -> list[list[float]]:
        del symbol, timeframe, since, limit, params
        return [
            [1_700_000_000_000, 100, 102, 99, 101, 0],
            [1_700_014_400_000, 101, 103, 100, 102, 0],
        ]

    def fetch_index_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int | None,
        limit: int,
        params: dict[str, object],
    ) -> list[list[float]]:
        del symbol, timeframe, since, limit, params
        return [
            [1_700_000_000_000, 99, 101, 98, 100, 0],
            [1_700_014_400_000, 100, 102, 99, 101, 0],
        ]


def test_funding_availability_includes_latency(monkeypatch: pytest.MonkeyPatch) -> None:
    source = CCXTDerivativesSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: FakeDerivativesExchange())
    result = source.fetch_funding_history("BTC/USDT:USDT", source_latency=timedelta(minutes=2))
    assert result["available_at"].iloc[0] == result["event_time"].iloc[0] + pd.Timedelta(minutes=2)


def test_open_interest_waits_until_interval_close(monkeypatch: pytest.MonkeyPatch) -> None:
    source = CCXTDerivativesSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: FakeDerivativesExchange())
    result = source.fetch_open_interest_history(
        "BTC/USDT:USDT", "4h", source_latency=timedelta(minutes=1)
    )
    assert result["available_at"].iloc[0] == result["event_time"].iloc[0] + pd.Timedelta(
        hours=4, minutes=1
    )
    assert (result["open_interest"] >= 0).all()


def test_basis_uses_mark_and_index_close(monkeypatch: pytest.MonkeyPatch) -> None:
    source = CCXTDerivativesSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: FakeDerivativesExchange())
    result = source.fetch_basis_history("BTC/USDT:USDT", "4h")
    assert result["basis"].iloc[0] == pytest.approx(0.01)
    assert result["available_at"].iloc[0] > result["event_time"].iloc[0]


def test_missing_capability_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    exchange = FakeDerivativesExchange()
    exchange.has = {"fetchFundingRateHistory": False}
    source = CCXTDerivativesSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: exchange)
    with pytest.raises(UnsupportedPublicEndpoint):
        source.fetch_funding_history("BTC/USDT:USDT")


def test_negative_source_latency_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    source = CCXTDerivativesSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: FakeDerivativesExchange())
    with pytest.raises(ValueError, match="negative"):
        source.fetch_funding_history("BTC/USDT:USDT", source_latency=timedelta(seconds=-1))


def test_derivative_pagination_continues_under_server_side_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = 1_700_000_000_000
    step = 8 * 60 * 60 * 1000

    class CappedFunding(FakeDerivativesExchange):
        def fetch_funding_rate_history(self, symbol, since, limit, params):
            del symbol, limit, params
            start = 0 if since is None else max(0, int((since - base + step - 1) // step))
            if start >= 6:
                return []
            return [
                {"timestamp": base + index * step, "fundingRate": 0.0001 * (index + 1)}
                for index in range(start, min(start + 2, 6))
            ]

    source = CCXTDerivativesSource("fake")
    monkeypatch.setattr(source, "_build_exchange", lambda: CappedFunding())
    result = source.fetch_funding_history(
        "BTC/USDT:USDT",
        since_ms=base,
        until_ms=base + 5 * step,
        limit=200,
        max_pages=10,
    )
    assert len(result) == 6
