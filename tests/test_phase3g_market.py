from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hybrid_trader.data.point_in_time import add_bar_availability
from hybrid_trader.data.snapshot import read_snapshot
from hybrid_trader.phase2c_contracts import SpotVenueSpec
from hybrid_trader.phase3g_market import Phase3GMarketSpec, collect_phase3g_market


def _bars(*, offset: float = 0.0, rows: int = 20) -> pd.DataFrame:
    index = pd.date_range("2026-07-01T00:00:00Z", periods=rows, freq="4h")
    close = 60_000 + np.arange(rows, dtype=float) * 25 + offset
    raw = pd.DataFrame(
        {
            "timestamp": index,
            "open": close - 5,
            "high": close + 20,
            "low": close - 20,
            "close": close,
            "volume": 100 + np.arange(rows, dtype=float),
        }
    )
    return add_bar_availability(
        raw,
        timeframe="4h",
        source_latency=timedelta(seconds=30),
    )


class FakeSpot:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame

    def fetch_point_in_time(self, *args, **kwargs) -> pd.DataFrame:
        del args, kwargs
        return self.frame.copy()


def _spec(*, as_of: datetime, required: bool = True) -> Phase3GMarketSpec:
    return Phase3GMarketSpec(
        as_of=as_of,
        lookback_days=30,
        spot_required_count=2,
        spot_sources=(
            SpotVenueSpec(
                exchange_id="venue-a",
                symbol="BTC/USD",
                required=required,
            ),
            SpotVenueSpec(
                exchange_id="venue-b",
                symbol="BTC/USDT",
                required=required,
            ),
        ),
        page_limit=50,
        max_pages=3,
    )


def test_phase3g_collects_two_sources_and_drops_unavailable_bar(tmp_path: Path) -> None:
    first = _bars()
    second = _bars(offset=3.0)
    as_of = first.index[-1].to_pydatetime() + timedelta(hours=3)
    frames = {"venue-a": first, "venue-b": second}

    manifest = collect_phase3g_market(
        _spec(as_of=as_of),
        tmp_path / "run",
        source_commit_sha="a" * 40,
        retrieved_at=datetime(2026, 7, 18, 9, tzinfo=UTC),
        spot_factory=lambda venue: FakeSpot(frames[venue.exchange_id]),
    )

    assert manifest.successful_spot_sources == ("venue-a", "venue-b")
    assert manifest.primary_source == "venue-a"
    assert manifest.credentials_used is False
    assert manifest.trading_decisions_created is False
    assert len(manifest.cross_venue_quality) == 1
    assert manifest.cross_venue_quality[0].overlap_rows == len(first) - 1
    assert all(attempt.status == "success" for attempt in manifest.source_attempts)

    combined, snapshot = read_snapshot(tmp_path / "run" / "combined_snapshot")
    assert len(combined) == len(first) - 1
    assert snapshot.content_sha256 == manifest.combined_snapshot_sha256
    assert pd.to_datetime(combined["available_at"], utc=True).max() <= pd.Timestamp(as_of)
    assert "spot_venue-b_close" in combined
    assert "spot_venue-b_spread_bps" in combined


def test_phase3g_fails_closed_when_required_source_fails(tmp_path: Path) -> None:
    frame = _bars()
    spec = Phase3GMarketSpec(
        as_of=datetime(2026, 7, 5, tzinfo=UTC),
        lookback_days=30,
        spot_required_count=2,
        spot_sources=(
            SpotVenueSpec(exchange_id="good", required=True),
            SpotVenueSpec(exchange_id="bad", required=True),
        ),
        page_limit=50,
    )

    def factory(venue: SpotVenueSpec) -> FakeSpot:
        if venue.exchange_id == "bad":
            raise RuntimeError("source unavailable")
        return FakeSpot(frame)

    with pytest.raises(RuntimeError, match="Required Phase 3G source failed"):
        collect_phase3g_market(
            spec,
            tmp_path / "run",
            source_commit_sha="b" * 40,
            spot_factory=factory,
        )
    attempts = (tmp_path / "run" / "source_attempts.json").read_text()
    assert '"status": "failure"' in attempts
    assert "source unavailable" in attempts


def test_phase3g_rejects_fewer_than_two_successful_optional_sources(
    tmp_path: Path,
) -> None:
    frame = _bars()
    spec = _spec(as_of=datetime(2026, 7, 5, tzinfo=UTC), required=False)

    def factory(venue: SpotVenueSpec) -> FakeSpot:
        if venue.exchange_id == "venue-b":
            raise RuntimeError("optional source unavailable")
        return FakeSpot(frame)

    with pytest.raises(RuntimeError, match="requires 2 spot sources; got 1"):
        collect_phase3g_market(
            spec,
            tmp_path / "run",
            source_commit_sha="c" * 40,
            spot_factory=factory,
        )


def test_phase3g_rejects_nonempty_output_and_duplicate_venues(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exchange IDs must be unique"):
        Phase3GMarketSpec(
            as_of=datetime(2026, 7, 5, tzinfo=UTC),
            spot_sources=(
                SpotVenueSpec(exchange_id="same"),
                SpotVenueSpec(exchange_id="same"),
            ),
        )

    output = tmp_path / "run"
    output.mkdir()
    (output / "existing.txt").write_text("occupied")
    with pytest.raises(FileExistsError, match="not empty"):
        collect_phase3g_market(
            _spec(as_of=datetime(2026, 7, 5, tzinfo=UTC)),
            output,
            source_commit_sha="d" * 40,
            spot_factory=lambda venue: FakeSpot(_bars()),
        )
