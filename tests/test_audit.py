from pathlib import Path

import pandas as pd

from hybrid_trader.audit import audit_snapshots, audit_tables
from hybrid_trader.data.snapshot import write_snapshot


def test_snapshot_and_cross_venue_audit(tmp_path: Path, pit_ohlcv: pd.DataFrame) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    created = pit_ohlcv["available_at"].iloc[-1].to_pydatetime()
    write_snapshot(
        pit_ohlcv,
        left,
        source="venue-a",
        symbol="BTC/USD",
        timeframe="4h",
        created_at=created,
    )
    shifted = pit_ohlcv.copy()
    for column in ("open", "high", "low", "close"):
        shifted[column] *= 1.001
    write_snapshot(
        shifted,
        right,
        source="venue-b",
        symbol="BTC/USD",
        timeframe="4h",
        created_at=created,
    )

    report = audit_snapshots([left, right])
    assert len(report.snapshots) == 2
    assert report.snapshots[0].missing_bar_count == 0
    assert report.snapshots[0].coverage_ratio == 1.0
    assert len(report.cross_venue) == 1
    pair = report.cross_venue[0]
    assert pair.overlap_rows == len(pit_ohlcv)
    assert pair.close_return_correlation is not None
    assert pair.close_return_correlation > 0.999
    assert pair.direction_agreement == 1.0
    snapshots, pairs = audit_tables(report)
    assert len(snapshots) == 2
    assert len(pairs) == 1
