from datetime import UTC, datetime, timedelta

import pandas as pd

from hybrid_trader.data.fred_source import FredCsvSource


def test_fred_source_applies_release_lag_and_cutoff() -> None:
    payload = b"DATE,NASDAQCOM\n2026-01-01,100\n2026-01-02,101\n2026-01-03,102\n"
    source = FredCsvSource(
        "NASDAQCOM",
        "nasdaq",
        release_lag=timedelta(days=1),
        source_latency=timedelta(minutes=5),
    )
    result = source.fetch(
        start=pd.Timestamp("2026-01-01T00:00:00Z"),
        end=pd.Timestamp("2026-01-03T00:00:00Z"),
        as_of=pd.Timestamp("2026-01-03T00:04:00Z"),
        downloader=lambda _: payload,
        retrieved_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    assert result.frame["nasdaq"].tolist() == [100.0]
    assert result.frame["available_at"].iloc[0] == pd.Timestamp("2026-01-02T00:05:00Z")
    assert len(result.payload_sha256) == 64
