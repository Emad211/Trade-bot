from __future__ import annotations

import csv
import hashlib
import io
from datetime import date, timedelta
from pathlib import Path

import pytest

from hybrid_trader.replication.cftc_release_ledger import (
    CFTCReleaseLedgerError,
    build_release_ledger,
    processing_business_days,
    write_release_ledger,
)


def _all_2022_tuesdays() -> list[date]:
    values: list[date] = []
    cursor = date(2022, 1, 1)
    while cursor.year == 2022:
        if cursor.weekday() == 1:
            values.append(cursor)
        cursor += timedelta(days=1)
    return values


def test_veterans_day_delays_third_business_day() -> None:
    days = processing_business_days(date(2022, 11, 8))
    assert days == (date(2022, 11, 9), date(2022, 11, 10), date(2022, 11, 14))


def test_thanksgiving_delays_third_business_day() -> None:
    days = processing_business_days(date(2022, 11, 22))
    assert days == (date(2022, 11, 23), date(2022, 11, 25), date(2022, 11, 28))


def test_pilot_schedule_preserves_dst_and_unverified_actual_time() -> None:
    rows = build_release_ledger(_all_2022_tuesdays())
    pilot = next(row for row in rows if row.report_as_of_date == "2022-09-13")
    assert pilot.scheduled_release_time_eastern == "2022-09-16T15:30:00-04:00"
    assert pilot.scheduled_release_time_utc == "2022-09-16T19:30:00Z"
    assert pilot.provisional_available_at_utc == "2022-09-16T19:35:00Z"
    assert pilot.conservative_available_at_utc == "2022-09-19T19:30:00Z"
    assert pilot.actual_release_time_utc == ""
    assert pilot.actual_release_verified is False


def test_winter_schedule_uses_standard_time() -> None:
    rows = build_release_ledger(_all_2022_tuesdays())
    first = rows[0]
    assert first.scheduled_release_time_eastern == "2022-01-07T15:30:00-05:00"
    assert first.scheduled_release_time_utc == "2022-01-07T20:30:00Z"


def test_full_ledger_has_only_two_holiday_delays() -> None:
    rows = build_release_ledger(_all_2022_tuesdays())
    delayed = [row for row in rows if row.federal_holiday_delay]
    assert len(rows) == 52
    assert [row.report_as_of_date for row in delayed] == ["2022-11-08", "2022-11-22"]
    assert [row.scheduled_release_date for row in delayed] == ["2022-11-14", "2022-11-28"]
    assert all(row.actual_release_time_utc == "" for row in rows)


def test_rejects_incomplete_report_calendar() -> None:
    with pytest.raises(CFTCReleaseLedgerError, match="Expected 52"):
        build_release_ledger([date(2022, 9, 13)])


def test_write_is_deterministic_and_non_promotional(tmp_path: Path) -> None:
    dates = _all_2022_tuesdays()
    first = write_release_ledger(
        tmp_path / "first",
        report_dates=dates,
        source_archive_sha256="a" * 64,
        source_member_sha256="b" * 64,
        source_schema_sha256="c" * 64,
    )
    second = write_release_ledger(
        tmp_path / "second",
        report_dates=reversed(dates),
        source_archive_sha256="a" * 64,
        source_member_sha256="b" * 64,
        source_schema_sha256="c" * 64,
    )
    first_bytes = (tmp_path / "first" / first["profile"]["ledger_filename"]).read_bytes()
    second_bytes = (tmp_path / "second" / second["profile"]["ledger_filename"]).read_bytes()
    assert first_bytes == second_bytes
    assert hashlib.sha256(first_bytes).hexdigest() == first["profile"]["ledger_sha256"]
    parsed = list(csv.DictReader(io.StringIO(first_bytes.decode("utf-8"))))
    assert len(parsed) == 52
    assert first["actual_release_times_verified"] is False
    assert first["artifact_audit_pass"] is False
    assert first["paper_replication_pass"] is False
    assert first["economic_edge_verdict"] == "INCONCLUSIVE"
