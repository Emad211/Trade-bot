from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from hybrid_trader.replication.cftc import normalize_cot_rows, standard_release_time


def test_standard_cftc_release_is_friday_1530_eastern() -> None:
    release = standard_release_time(date(2026, 7, 14))
    eastern = release.astimezone(ZoneInfo("America/New_York"))
    assert eastern.weekday() == 4
    assert (eastern.hour, eastern.minute) == (15, 30)


def test_cftc_available_at_uses_override_and_parser_delay() -> None:
    report_date = date(2025, 9, 30)
    actual = datetime(2025, 11, 19, 15, 30, tzinfo=ZoneInfo("America/New_York"))
    result = normalize_cot_rows(
        [{"report_date_as_yyyy_mm_dd": "2025-09-30T00:00:00", "id": "x"}],
        report_family="LEGACY_FUTURES_ONLY",
        parser_delay=timedelta(minutes=2),
        release_overrides={report_date: actual},
    )
    assert result.iloc[0]["available_at"] > result.iloc[0]["report_as_of_time"]
    assert result.iloc[0]["available_at"] == result.iloc[0]["actual_release_time"] + timedelta(
        minutes=2
    )


def test_negative_parser_delay_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_cot_rows(
            [{"report_date_as_yyyy_mm_dd": "2026-07-14T00:00:00"}],
            report_family="DISAGGREGATED_FUTURES_ONLY",
            parser_delay=timedelta(seconds=-1),
        )
