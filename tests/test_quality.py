from datetime import UTC, datetime

import pandas as pd

from hybrid_trader.data.point_in_time import add_bar_availability
from hybrid_trader.data.quality import bar_quality, cross_venue_quality


def _frame(prices: list[float]) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=len(prices), freq="4h", tz="UTC")
    raw = pd.DataFrame(
        {
            "timestamp": index,
            "open": prices,
            "high": [value * 1.01 for value in prices],
            "low": [value * 0.99 for value in prices],
            "close": prices,
            "volume": [10.0] * len(prices),
        }
    )
    return add_bar_availability(raw, timeframe="4h")


def test_quality_reports_gap_and_cross_venue_spread() -> None:
    primary = _frame([100, 101, 102, 103])
    secondary = _frame([100, 100.5, 101.5, 102.5])
    report = bar_quality(
        primary.drop(primary.index[1]),
        source_id="a",
        timeframe="4h",
        as_of=pd.Timestamp(datetime(2026, 1, 2, tzinfo=UTC)),
    )
    assert report.missing_bar_count == 1
    cross = cross_venue_quality(
        primary,
        secondary,
        primary_source_id="a",
        secondary_source_id="b",
    )
    assert cross.overlap_rows == 4
    assert cross.median_absolute_spread_bps is not None
