from datetime import UTC, datetime

import pandas as pd
import pytest

from hybrid_trader.data.artifact import (
    read_tabular_artifact,
    write_tabular_artifact,
)


def test_tabular_artifact_round_trip_and_tamper(tmp_path) -> None:
    frame = pd.DataFrame(
        {
            "event_time": pd.date_range("2026-01-01", periods=3, freq="D", tz="UTC"),
            "available_at": pd.date_range("2026-01-02", periods=3, freq="D", tz="UTC"),
            "value": [1.0, 2.0, 3.0],
        }
    )
    manifest = write_tabular_artifact(
        frame,
        tmp_path,
        source_id="fred:test",
        source_type="market_context",
        instrument="TEST",
        availability_policy="event_plus_1d",
        revision_policy="market_price_latest_vintage",
        created_at=datetime(2026, 1, 5, tzinfo=UTC),
    )
    loaded, read_manifest = read_tabular_artifact(tmp_path)
    assert manifest == read_manifest
    assert loaded["value"].tolist() == [1.0, 2.0, 3.0]
    payload = (tmp_path / "data.csv.gz").read_bytes()
    (tmp_path / "data.csv.gz").write_bytes(payload[:-1] + bytes([payload[-1] ^ 1]))
    with pytest.raises((OSError, ValueError)):
        read_tabular_artifact(tmp_path)


def test_tabular_artifact_checks_global_maximum_availability(tmp_path) -> None:
    frame = pd.DataFrame(
        {
            "event_time": pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"]),
            # The last event is observable, but an earlier event is not.
            "available_at": pd.to_datetime(["2026-01-10T00:00:00Z", "2026-01-03T00:00:00Z"]),
            "value": [1.0, 2.0],
        }
    )
    with pytest.raises(ValueError, match="unavailable at created_at"):
        write_tabular_artifact(
            frame,
            tmp_path,
            source_id="test:nonmonotonic",
            source_type="market_context",
            instrument="TEST",
            availability_policy="nonmonotonic_fixture",
            revision_policy="fixture",
            created_at=datetime(2026, 1, 5, tzinfo=UTC),
        )


def test_tabular_manifest_records_minimum_and_maximum_availability(tmp_path) -> None:
    frame = pd.DataFrame(
        {
            "event_time": pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"]),
            "available_at": pd.to_datetime(["2026-01-05T00:00:00Z", "2026-01-03T00:00:00Z"]),
            "value": [1.0, 2.0],
        }
    )
    manifest = write_tabular_artifact(
        frame,
        tmp_path,
        source_id="test:bounds",
        source_type="market_context",
        instrument="TEST",
        availability_policy="nonmonotonic_fixture",
        revision_policy="fixture",
        created_at=datetime(2026, 1, 6, tzinfo=UTC),
    )
    assert manifest.availability_start == datetime(2026, 1, 3, tzinfo=UTC)
    assert manifest.availability_end == datetime(2026, 1, 5, tzinfo=UTC)
    _, loaded_manifest = read_tabular_artifact(tmp_path)
    assert loaded_manifest == manifest
