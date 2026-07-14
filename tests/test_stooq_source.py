from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from hybrid_trader.data.stooq_source import StooqCsvSource


def test_stooq_source_applies_release_lag_cutoff_and_hash() -> None:
    payload = (
        b"Date,Open,High,Low,Close\n"
        b"2026-01-01,2000,2010,1990,2005\n"
        b"2026-01-02,2005,2020,2000,2015\n"
        b"2026-01-03,2015,2030,2010,2025\n"
    )
    source = StooqCsvSource(
        "xauusd",
        "gold_usd",
        release_lag=timedelta(days=1),
        source_latency=timedelta(minutes=5),
    )
    result = source.fetch(
        start=pd.Timestamp("2026-01-01T00:00:00Z"),
        end=pd.Timestamp("2026-01-03T00:00:00Z"),
        as_of=pd.Timestamp("2026-01-03T00:04:00Z"),
        downloader=lambda url: payload,
        retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    assert result.frame["gold_usd"].tolist() == [2005.0]
    assert result.frame["available_at"].iloc[0] == pd.Timestamp("2026-01-02T00:05:00Z")
    assert "s=xauusd" in result.url
    assert "d1=20260101" in result.url
    assert len(result.payload_sha256) == 64


def test_stooq_source_rejects_nonpositive_reference_price() -> None:
    source = StooqCsvSource("xauusd", "gold_usd")
    with pytest.raises(ValueError, match="positive"):
        source.fetch(
            start=pd.Timestamp("2026-01-01T00:00:00Z"),
            end=pd.Timestamp("2026-01-02T00:00:00Z"),
            as_of=pd.Timestamp("2026-01-05T00:00:00Z"),
            downloader=lambda url: b"Date,Close\n2026-01-01,0\n",
        )
