"""Fail-closed CFTC TFF release-schedule reconstruction for the 2022 archive."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")

CFTC_RELEASE_RULE_SOURCE = (
    "https://www.cftc.gov/MarketReports/CommitmentsofTraders/"
    "AbouttheCOTReports/index.htm"
)
CFTC_HISTORICAL_SPECIAL_ANNOUNCEMENTS_SOURCE = (
    "https://www.cftc.gov/MarketReports/CommitmentsofTraders/"
    "HistoricalSpecialAnnouncements/index.htm"
)
CFTC_HISTORICAL_VIEWABLE_SOURCE = (
    "https://www.cftc.gov/MarketReports/CommitmentsofTraders/"
    "HistoricalViewable/index.htm"
)
OPM_2022_HOLIDAY_SOURCE = (
    "https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/"
)

FEDERAL_HOLIDAYS_2022: dict[date, str] = {
    date(2021, 12, 31): "New Year's Day (observed)",
    date(2022, 1, 17): "Birthday of Martin Luther King, Jr.",
    date(2022, 2, 21): "Washington's Birthday",
    date(2022, 5, 30): "Memorial Day",
    date(2022, 6, 20): "Juneteenth National Independence Day (observed)",
    date(2022, 7, 4): "Independence Day",
    date(2022, 9, 5): "Labor Day",
    date(2022, 10, 10): "Columbus Day",
    date(2022, 11, 11): "Veterans Day",
    date(2022, 11, 24): "Thanksgiving Day",
    date(2022, 12, 26): "Christmas Day (observed)",
}

DEFAULT_PARSER_DELAY = timedelta(minutes=5)
EXPECTED_2022_REPORT_COUNT = 52
EXPECTED_2022_DELAYED_REPORTS = frozenset({date(2022, 11, 8), date(2022, 11, 22)})


class CFTCReleaseLedgerError(RuntimeError):
    """Raised when release-ledger inputs or derived schedules violate the contract."""


@dataclass(frozen=True)
class ReleaseLedgerRow:
    report_as_of_date: str
    report_weekday: str
    scheduled_release_date: str
    scheduled_release_time_eastern: str
    scheduled_release_time_utc: str
    processing_business_days: str
    federal_holidays_in_processing_window: str
    federal_holiday_delay: bool
    schedule_delay_calendar_days: int
    actual_release_time_utc: str
    actual_release_verified: bool
    release_evidence_class: str
    provisional_available_at_utc: str
    conservative_available_at_utc: str
    historical_viewable_url: str


@dataclass(frozen=True)
class ReleaseLedgerProfile:
    report_count: int
    first_report_date: str
    last_report_date: str
    delayed_report_count: int
    delayed_report_dates: tuple[str, ...]
    actual_release_verified_count: int
    eastern_standard_time_rows: int
    eastern_daylight_time_rows: int
    ledger_filename: str
    ledger_byte_count: int
    ledger_sha256: str


def is_federal_business_day(value: date) -> bool:
    """Return whether a date is a Monday-Friday US federal workday."""

    return value.weekday() < 5 and value not in FEDERAL_HOLIDAYS_2022


def processing_business_days(report_date: date, *, count: int = 3) -> tuple[date, ...]:
    """Return the first ``count`` federal business days strictly after report date."""

    if count <= 0:
        raise ValueError("count must be positive")
    result: list[date] = []
    cursor = report_date
    while len(result) < count:
        cursor += timedelta(days=1)
        if is_federal_business_day(cursor):
            result.append(cursor)
    return tuple(result)


def next_federal_business_day(value: date) -> date:
    """Return the first federal business day strictly after ``value``."""

    return processing_business_days(value, count=1)[0]


def _historical_viewable_url(report_date: date) -> str:
    suffix = report_date.strftime("%m%d%y")
    return (
        "https://www.cftc.gov/MarketReports/CommitmentsofTraders/"
        f"HistoricalViewable/cot{suffix}"
    )


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _iso_eastern(value: datetime) -> str:
    return value.astimezone(EASTERN).isoformat()


def build_release_ledger(
    report_dates: Iterable[date],
    *,
    parser_delay: timedelta = DEFAULT_PARSER_DELAY,
) -> tuple[ReleaseLedgerRow, ...]:
    """Build the deterministic 2022 schedule ledger without claiming actual release times."""

    if parser_delay < timedelta(0):
        raise ValueError("parser_delay cannot be negative")
    ordered = sorted(set(report_dates))
    if len(ordered) != EXPECTED_2022_REPORT_COUNT:
        raise CFTCReleaseLedgerError(
            f"Expected {EXPECTED_2022_REPORT_COUNT} unique report dates, found {len(ordered)}"
        )
    if ordered[0] != date(2022, 1, 4) or ordered[-1] != date(2022, 12, 27):
        raise CFTCReleaseLedgerError("Unexpected 2022 report-date range")
    if any(value.year != 2022 or value.weekday() != 1 for value in ordered):
        raise CFTCReleaseLedgerError("Every 2022 CFTC report date must be a Tuesday")

    rows: list[ReleaseLedgerRow] = []
    for report_date in ordered:
        processing_days = processing_business_days(report_date)
        scheduled_date = processing_days[-1]
        normal_friday = report_date + timedelta(days=3)
        window_holidays = sorted(
            holiday
            for holiday in FEDERAL_HOLIDAYS_2022
            if report_date < holiday <= scheduled_date
        )
        release_eastern = datetime.combine(
            scheduled_date,
            time(15, 30),
            tzinfo=EASTERN,
        )
        provisional = release_eastern + parser_delay
        conservative_date = next_federal_business_day(scheduled_date)
        conservative = datetime.combine(
            conservative_date,
            time(15, 30),
            tzinfo=EASTERN,
        )
        rows.append(
            ReleaseLedgerRow(
                report_as_of_date=report_date.isoformat(),
                report_weekday=report_date.strftime("%A"),
                scheduled_release_date=scheduled_date.isoformat(),
                scheduled_release_time_eastern=_iso_eastern(release_eastern),
                scheduled_release_time_utc=_iso_utc(release_eastern),
                processing_business_days="|".join(value.isoformat() for value in processing_days),
                federal_holidays_in_processing_window="|".join(
                    f"{value.isoformat()}:{FEDERAL_HOLIDAYS_2022[value]}"
                    for value in window_holidays
                ),
                federal_holiday_delay=scheduled_date != normal_friday,
                schedule_delay_calendar_days=(scheduled_date - normal_friday).days,
                actual_release_time_utc="",
                actual_release_verified=False,
                release_evidence_class=(
                    "OFFICIAL_RULE_AND_HOLIDAY_RECONSTRUCTION_ACTUAL_TIME_UNVERIFIED"
                ),
                provisional_available_at_utc=_iso_utc(provisional),
                conservative_available_at_utc=_iso_utc(conservative),
                historical_viewable_url=_historical_viewable_url(report_date),
            )
        )

    delayed = {
        date.fromisoformat(row.report_as_of_date)
        for row in rows
        if row.federal_holiday_delay
    }
    if delayed != EXPECTED_2022_DELAYED_REPORTS:
        raise CFTCReleaseLedgerError(
            f"Unexpected delayed-report set: {sorted(value.isoformat() for value in delayed)}"
        )
    return tuple(rows)


def report_dates_from_rows(rows: Iterable[dict[str, str]]) -> tuple[date, ...]:
    """Extract unique report dates from validated annual CFTC rows."""

    values: set[date] = set()
    for row in rows:
        raw = row.get("Report_Date_as_YYYY-MM-DD", "").strip()
        if not raw:
            raise CFTCReleaseLedgerError("Annual row lacks Report_Date_as_YYYY-MM-DD")
        try:
            values.add(date.fromisoformat(raw))
        except ValueError as exc:
            raise CFTCReleaseLedgerError(f"Invalid annual report date: {raw!r}") from exc
    return tuple(sorted(values))


def release_ledger_csv(rows: Sequence[ReleaseLedgerRow]) -> bytes:
    """Serialize release rows to a deterministic UTF-8 CSV."""

    if not rows:
        raise CFTCReleaseLedgerError("Release ledger cannot be empty")
    output = io.StringIO(newline="")
    fieldnames = list(asdict(rows[0]))
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(asdict(row))
    return output.getvalue().encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_release_ledger(
    output_dir: str | Path,
    *,
    report_dates: Iterable[date],
    source_archive_sha256: str,
    source_member_sha256: str,
    source_schema_sha256: str,
    parser_delay: timedelta = DEFAULT_PARSER_DELAY,
) -> dict[str, Any]:
    """Write deterministic release ledger, profile, and fail-closed lineage manifest."""

    rows = build_release_ledger(report_dates, parser_delay=parser_delay)
    ledger_bytes = release_ledger_csv(rows)
    ledger_filename = "cftc_tff_futures_only_2022_release_ledger.csv"
    ledger_sha256 = hashlib.sha256(ledger_bytes).hexdigest()
    delayed_dates = tuple(
        row.report_as_of_date for row in rows if row.federal_holiday_delay
    )
    standard_rows = sum("-05:00" in row.scheduled_release_time_eastern for row in rows)
    daylight_rows = sum("-04:00" in row.scheduled_release_time_eastern for row in rows)
    profile = ReleaseLedgerProfile(
        report_count=len(rows),
        first_report_date=rows[0].report_as_of_date,
        last_report_date=rows[-1].report_as_of_date,
        delayed_report_count=len(delayed_dates),
        delayed_report_dates=delayed_dates,
        actual_release_verified_count=sum(row.actual_release_verified for row in rows),
        eastern_standard_time_rows=standard_rows,
        eastern_daylight_time_rows=daylight_rows,
        ledger_filename=ledger_filename,
        ledger_byte_count=len(ledger_bytes),
        ledger_sha256=ledger_sha256,
    )
    pilot = next(row for row in rows if row.report_as_of_date == "2022-09-13")
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "ledger_id": "CFTC_TFF_FUTURES_ONLY_2022_RELEASE_LEDGER_V1",
        "source_archive_sha256": source_archive_sha256,
        "source_member_sha256": source_member_sha256,
        "source_schema_sha256": source_schema_sha256,
        "cftc_release_rule_source": CFTC_RELEASE_RULE_SOURCE,
        "cftc_historical_viewable_source": CFTC_HISTORICAL_VIEWABLE_SOURCE,
        "cftc_special_announcements_source": CFTC_HISTORICAL_SPECIAL_ANNOUNCEMENTS_SOURCE,
        "opm_2022_holiday_source": OPM_2022_HOLIDAY_SOURCE,
        "release_rule": "third federal business day after report date at 15:30 America/New_York",
        "parser_delay_seconds": int(parser_delay.total_seconds()),
        "actual_release_time_policy": "null unless independently verified by historical publication evidence",
        "provisional_availability_policy": "scheduled release plus parser delay; not actual-release evidence",
        "conservative_availability_policy": "next federal business day at 15:30 America/New_York",
        "profile": asdict(profile),
        "pilot_2022_09_13": asdict(pilot),
        "special_announcement_review": {
            "year": 2022,
            "release_delay_announcement_found": False,
            "other_announcement_found": True,
            "other_announcement_summary": "2022-02-11 contract-market name shortening; codes and other data unaffected",
        },
        "actual_release_times_verified": False,
        "historical_schedule_reconstructed": True,
        "lineage_complete_to_actions_staged_source": True,
        "artifact_audit_pass": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    root = Path(output_dir)
    _atomic_write(root / ledger_filename, ledger_bytes)
    _atomic_write(
        root / "release-ledger-profile.json",
        (json.dumps(asdict(profile), indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    _atomic_write(
        root / "release-ledger-manifest.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return manifest


def derive_release_ledger(
    archive_path: str | Path,
    output_dir: str | Path,
    *,
    parser_delay: timedelta = DEFAULT_PARSER_DELAY,
) -> dict[str, Any]:
    """Verify the frozen annual archive and derive its 2022 release ledger."""

    from hybrid_trader.replication.cftc_historical_parser import (
        EXPECTED_SCHEMA_SHA256,
        SOURCE_ARCHIVE_SHA256,
        SOURCE_MEMBER_SHA256,
        extract_and_verify_member,
        parse_member_bytes,
    )

    member_bytes = extract_and_verify_member(archive_path)
    dataset = parse_member_bytes(member_bytes)
    return write_release_ledger(
        output_dir,
        report_dates=report_dates_from_rows(dataset.rows),
        source_archive_sha256=SOURCE_ARCHIVE_SHA256,
        source_member_sha256=SOURCE_MEMBER_SHA256,
        source_schema_sha256=EXPECTED_SCHEMA_SHA256,
        parser_delay=parser_delay,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for deterministic release-ledger derivation."""

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--parser-delay-seconds", type=int, default=300)
    args = parser.parse_args(argv)
    if args.parser_delay_seconds < 0:
        parser.error("--parser-delay-seconds cannot be negative")
    manifest = derive_release_ledger(
        args.archive,
        args.output_dir,
        parser_delay=timedelta(seconds=args.parser_delay_seconds),
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
