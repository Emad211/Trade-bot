from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from hybrid_trader.data.snapshot import frame_sha256, read_snapshot, write_snapshot


def test_snapshot_round_trip_is_content_addressed(tmp_path: Path, pit_ohlcv: pd.DataFrame) -> None:
    root = tmp_path / "snapshot"
    created = pit_ohlcv["available_at"].iloc[-1].to_pydatetime()
    manifest = write_snapshot(
        pit_ohlcv,
        root,
        source="unit-test",
        symbol="BTC/USD",
        timeframe="4h",
        source_latency_seconds=30,
        created_at=created,
    )
    loaded, loaded_manifest = read_snapshot(root)
    assert manifest == loaded_manifest
    assert loaded_manifest.content_sha256 == frame_sha256(loaded)
    assert loaded_manifest.dataset_id.endswith(loaded_manifest.content_sha256[:12])


def test_snapshot_identical_rewrite_is_idempotent(tmp_path: Path, pit_ohlcv: pd.DataFrame) -> None:
    root = tmp_path / "snapshot"
    created = pit_ohlcv["available_at"].iloc[-1].to_pydatetime()
    first = write_snapshot(
        pit_ohlcv,
        root,
        source="unit-test",
        symbol="BTC/USD",
        timeframe="4h",
        created_at=created,
    )
    second = write_snapshot(
        pit_ohlcv,
        root,
        source="different-metadata-is-not-rewritten",
        symbol="BTC/USD",
        timeframe="4h",
        created_at=created,
    )
    assert first == second


def test_snapshot_rejects_future_observations(tmp_path: Path, pit_ohlcv: pd.DataFrame) -> None:
    created = pit_ohlcv["available_at"].iloc[-2].to_pydatetime()
    with pytest.raises(ValueError, match="unavailable"):
        write_snapshot(
            pit_ohlcv,
            tmp_path / "snapshot",
            source="unit-test",
            symbol="BTC/USD",
            timeframe="4h",
            created_at=created,
        )


def test_snapshot_detects_payload_tampering(tmp_path: Path, pit_ohlcv: pd.DataFrame) -> None:
    root = tmp_path / "snapshot"
    write_snapshot(
        pit_ohlcv,
        root,
        source="unit-test",
        symbol="BTC/USD",
        timeframe="4h",
        created_at=pit_ohlcv["available_at"].iloc[-1].to_pydatetime(),
    )
    payload = bytearray((root / "data.csv.gz").read_bytes())
    payload[-10] ^= 1
    (root / "data.csv.gz").write_bytes(payload)
    with pytest.raises((OSError, EOFError, ValueError)):
        read_snapshot(root)


def test_snapshot_created_at_requires_awareness(tmp_path: Path, pit_ohlcv: pd.DataFrame) -> None:
    # The writer safely normalizes an explicitly naive timestamp to UTC.
    manifest = write_snapshot(
        pit_ohlcv,
        tmp_path / "snapshot",
        source="unit-test",
        symbol="BTC/USD",
        timeframe="4h",
        created_at=datetime(2025, 1, 1),
    )
    assert manifest.created_at.tzinfo == UTC
