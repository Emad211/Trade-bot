import json
from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from hybrid_trader.data.yahoo_source import YahooChartSource


def _payload() -> bytes:
    document = {
        "chart": {
            "result": [
                {
                    "timestamp": [1767225600, 1767312000, 1767398400],
                    "indicators": {"quote": [{"close": [2005.0, 2015.0, 2025.0]}]},
                }
            ],
            "error": None,
        }
    }
    return json.dumps(document).encode()


def test_yahoo_source_applies_release_lag_cutoff_and_hash() -> None:
    source = YahooChartSource(
        "GC=F",
        "gold_futures_usd",
        release_lag=timedelta(days=1),
        source_latency=timedelta(minutes=5),
    )
    result = source.fetch(
        start=pd.Timestamp("2026-01-01T00:00:00Z"),
        end=pd.Timestamp("2026-01-03T00:00:00Z"),
        as_of=pd.Timestamp("2026-01-03T00:04:00Z"),
        downloader=lambda url: _payload(),
        retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    assert result.frame["gold_futures_usd"].tolist() == [2005.0]
    assert result.frame["available_at"].iloc[0] == pd.Timestamp("2026-01-02T00:05:00Z")
    assert "GC%3DF" in result.url
    assert len(result.payload_sha256) == 64


def test_yahoo_source_rejects_chart_error() -> None:
    source = YahooChartSource("GC=F", "gold_futures_usd")
    payload = json.dumps({"chart": {"result": None, "error": {"code": "Bad"}}}).encode()
    with pytest.raises(RuntimeError, match="chart error"):
        source.fetch(
            start=pd.Timestamp("2026-01-01T00:00:00Z"),
            end=pd.Timestamp("2026-01-02T00:00:00Z"),
            as_of=pd.Timestamp("2026-01-05T00:00:00Z"),
            downloader=lambda url: payload,
        )
