"""Parser and dated pilot extraction for the acquired 2022 CFTC TFF archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, cast

SOURCE_ID = "CFTC_TFF_FUTURES_ONLY_HISTORICAL_TEXT_2022"
SOURCE_ARCHIVE_FILENAME = "fut_fin_txt_2022.zip"
SOURCE_ARCHIVE_SHA256 = "94c9c1fdee9dfbe377a09923ddfe26b88d3460605dd076081f221ad367d88601"
SOURCE_MEMBER_NAME = "FinFutYY.txt"
SOURCE_MEMBER_SHA256 = "7c309cb76da8bf432e1a347e5bfde169bcac31cec4e9e33742cf3a078328bb3b"
EXPECTED_SCHEMA_FIELD_COUNT = 87
EXPECTED_SCHEMA_SHA256 = "fe0123051e8e5f5bb8f0cf4a870b451951bd4fa131777096eb5d028115545d42"
EXPECTED_ROW_COUNT = 2719
EXPECTED_REPORT_DATE_COUNT = 52
EXPECTED_MIN_REPORT_DATE = date(2022, 1, 4)
EXPECTED_MAX_REPORT_DATE = date(2022, 12, 27)
DEFAULT_PILOT_DATE = date(2022, 9, 13)
EXPECTED_DEFAULT_PILOT_ROWS = 54

REQUIRED_FIELDS = frozenset(
    {
        "Market_and_Exchange_Names",
        "As_of_Date_In_Form_YYMMDD",
        "Report_Date_as_YYYY-MM-DD",
        "CFTC_Contract_Market_Code",
        "CFTC_Market_Code",
        "CFTC_Region_Code",
        "CFTC_Commodity_Code",
        "Open_Interest_All",
        "Tot_Rept_Positions_Long_All",
        "Tot_Rept_Positions_Short_All",
        "NonRept_Positions_Long_All",
        "NonRept_Positions_Short_All",
        "FutOnly_or_Combined",
    }
)


class CFTCHistoricalParseError(RuntimeError):
    """Raised when the acquired annual text archive violates the frozen contract."""


@dataclass(frozen=True)
class AnnualDatasetProfile:
    source_id: str
    archive_sha256: str
    member_name: str
    member_sha256: str
    schema_field_count: int
    schema_sha256: str
    row_count: int
    report_date_count: int
    min_report_date: str
    max_report_date: str
    unique_report_contract_keys: int
    futures_only_rows: int
    long_exact_reconciliation_differences: int
    short_exact_reconciliation_differences: int
    consolidated_unit_difference_rows: int
    material_accounting_failures: int


@dataclass(frozen=True)
class PilotProfile:
    report_date: str
    row_count: int
    unique_contract_market_codes: int
    long_exact_reconciliation_differences: int
    short_exact_reconciliation_differences: int
    consolidated_unit_difference_rows: int
    material_accounting_failures: int
    min_contract_market_code: str
    max_contract_market_code: str
    canonical_csv_filename: str
    canonical_csv_byte_count: int
    canonical_csv_sha256: str


@dataclass(frozen=True)
class ParsedAnnualDataset:
    fieldnames: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    profile: AnnualDatasetProfile


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def schema_fingerprint(fieldnames: Sequence[str]) -> str:
    """Fingerprint exact field names and order with an unambiguous delimiter."""

    return _sha256("\x00".join(fieldnames).encode("utf-8"))


def _parse_iso_date(value: str, *, field: str, row_number: int) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise CFTCHistoricalParseError(
            f"Row {row_number}: invalid {field} value {value!r}"
        ) from exc


def _as_nonnegative_int(row: Mapping[str, str], field: str, *, row_number: int) -> int:
    value = row.get(field, "").strip()
    if not value:
        raise CFTCHistoricalParseError(f"Row {row_number}: missing integer field {field}")
    try:
        result = int(value)
    except ValueError as exc:
        raise CFTCHistoricalParseError(
            f"Row {row_number}: invalid integer in {field}: {value!r}"
        ) from exc
    if result < 0:
        raise CFTCHistoricalParseError(f"Row {row_number}: negative integer in {field}: {result}")
    return result


def _accounting_differences(row: Mapping[str, str], *, row_number: int) -> tuple[int, int, bool]:
    open_interest = _as_nonnegative_int(row, "Open_Interest_All", row_number=row_number)
    reported_long = _as_nonnegative_int(row, "Tot_Rept_Positions_Long_All", row_number=row_number)
    nonreported_long = _as_nonnegative_int(row, "NonRept_Positions_Long_All", row_number=row_number)
    reported_short = _as_nonnegative_int(row, "Tot_Rept_Positions_Short_All", row_number=row_number)
    nonreported_short = _as_nonnegative_int(
        row, "NonRept_Positions_Short_All", row_number=row_number
    )
    long_difference = reported_long + nonreported_long - open_interest
    short_difference = reported_short + nonreported_short - open_interest
    code = row.get("CFTC_Contract_Market_Code", "").strip()
    market_name = row.get("Market_and_Exchange_Names", "")
    consolidated = code.endswith("+") and "Consolidated" in market_name
    material_failure = (
        abs(long_difference) > 1
        or abs(short_difference) > 1
        or ((long_difference != 0 or short_difference != 0) and not consolidated)
    )
    return long_difference, short_difference, material_failure


def extract_and_verify_member(archive_path: str | Path) -> bytes:
    """Verify the exact acquired archive identity and return its text member bytes."""

    path = Path(archive_path)
    raw_zip = path.read_bytes()
    actual_archive_hash = _sha256(raw_zip)
    if actual_archive_hash != SOURCE_ARCHIVE_SHA256:
        raise CFTCHistoricalParseError(
            f"Archive SHA-256 does not match the frozen acquired source: {actual_archive_hash}"
        )
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw_zip))
    except zipfile.BadZipFile as exc:
        raise CFTCHistoricalParseError("Acquired archive is not a valid ZIP") from exc
    with archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise CFTCHistoricalParseError(f"ZIP CRC failed for {bad_member!r}")
        names = [info.filename for info in archive.infolist() if not info.is_dir()]
        if names != [SOURCE_MEMBER_NAME]:
            raise CFTCHistoricalParseError(f"Unexpected archive members: {names!r}")
        member_bytes = archive.read(SOURCE_MEMBER_NAME)
    actual_member_hash = _sha256(member_bytes)
    if actual_member_hash != SOURCE_MEMBER_SHA256:
        raise CFTCHistoricalParseError(
            f"Text member SHA-256 does not match the frozen acquired source: {actual_member_hash}"
        )
    return member_bytes


def parse_member_bytes(member_bytes: bytes) -> ParsedAnnualDataset:
    """Parse and fully validate the frozen annual TFF text member."""

    if _sha256(member_bytes) != SOURCE_MEMBER_SHA256:
        raise CFTCHistoricalParseError("Member bytes do not match the frozen source hash")
    try:
        text = member_bytes.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise CFTCHistoricalParseError("Text member is not valid UTF-8") from exc

    reader = csv.DictReader(io.StringIO(text, newline=""), skipinitialspace=True)
    if reader.fieldnames is None:
        raise CFTCHistoricalParseError("Text member has no CSV header")
    fieldnames = tuple(reader.fieldnames)
    fingerprint = schema_fingerprint(fieldnames)
    if len(fieldnames) != EXPECTED_SCHEMA_FIELD_COUNT:
        raise CFTCHistoricalParseError(
            f"Expected {EXPECTED_SCHEMA_FIELD_COUNT} fields, found {len(fieldnames)}"
        )
    if fingerprint != EXPECTED_SCHEMA_SHA256:
        raise CFTCHistoricalParseError(f"Schema fingerprint changed: {fingerprint}")
    missing_required = REQUIRED_FIELDS - set(fieldnames)
    if missing_required:
        raise CFTCHistoricalParseError(f"Schema lacks required fields: {sorted(missing_required)}")

    rows: list[dict[str, str]] = []
    report_dates: set[date] = set()
    keys: set[tuple[date, str]] = set()
    futures_only_rows = 0
    long_differences = 0
    short_differences = 0
    consolidated_unit_difference_rows = 0
    material_failures = 0

    for row_number, raw_row in enumerate(reader, start=2):
        if None in raw_row:
            raise CFTCHistoricalParseError(f"Row {row_number}: unexpected extra CSV fields")
        if any(value is None for value in raw_row.values()):
            raise CFTCHistoricalParseError(f"Row {row_number}: missing trailing CSV fields")
        row = {str(key): cast(str, value) for key, value in raw_row.items()}
        report_date = _parse_iso_date(
            row["Report_Date_as_YYYY-MM-DD"],
            field="Report_Date_as_YYYY-MM-DD",
            row_number=row_number,
        )
        expected_yymmdd = report_date.strftime("%y%m%d")
        if row["As_of_Date_In_Form_YYMMDD"].strip() != expected_yymmdd:
            raise CFTCHistoricalParseError(f"Row {row_number}: date encodings disagree")
        contract_code = row["CFTC_Contract_Market_Code"].strip()
        if not contract_code:
            raise CFTCHistoricalParseError(f"Row {row_number}: empty CFTC contract market code")
        key = (report_date, contract_code)
        if key in keys:
            raise CFTCHistoricalParseError(
                f"Row {row_number}: duplicate report-date/contract key {key!r}"
            )
        keys.add(key)
        report_dates.add(report_date)

        if row["FutOnly_or_Combined"].strip() != "FutOnly":
            raise CFTCHistoricalParseError(f"Row {row_number}: row is not Futures Only")
        futures_only_rows += 1
        long_difference, short_difference, material_failure = _accounting_differences(
            row, row_number=row_number
        )
        long_differences += int(long_difference != 0)
        short_differences += int(short_difference != 0)
        consolidated_unit_difference_rows += int(
            (long_difference != 0 or short_difference != 0) and not material_failure
        )
        material_failures += int(material_failure)
        rows.append(row)

    if len(rows) != EXPECTED_ROW_COUNT:
        raise CFTCHistoricalParseError(f"Expected {EXPECTED_ROW_COUNT} rows, found {len(rows)}")
    if len(report_dates) != EXPECTED_REPORT_DATE_COUNT:
        raise CFTCHistoricalParseError(
            f"Expected {EXPECTED_REPORT_DATE_COUNT} report dates, found {len(report_dates)}"
        )
    if min(report_dates) != EXPECTED_MIN_REPORT_DATE:
        raise CFTCHistoricalParseError(f"Unexpected first report date: {min(report_dates)}")
    if max(report_dates) != EXPECTED_MAX_REPORT_DATE:
        raise CFTCHistoricalParseError(f"Unexpected last report date: {max(report_dates)}")
    if material_failures:
        raise CFTCHistoricalParseError(
            f"Material open-interest accounting failures: {material_failures}"
        )

    profile = AnnualDatasetProfile(
        source_id=SOURCE_ID,
        archive_sha256=SOURCE_ARCHIVE_SHA256,
        member_name=SOURCE_MEMBER_NAME,
        member_sha256=SOURCE_MEMBER_SHA256,
        schema_field_count=len(fieldnames),
        schema_sha256=fingerprint,
        row_count=len(rows),
        report_date_count=len(report_dates),
        min_report_date=min(report_dates).isoformat(),
        max_report_date=max(report_dates).isoformat(),
        unique_report_contract_keys=len(keys),
        futures_only_rows=futures_only_rows,
        long_exact_reconciliation_differences=long_differences,
        short_exact_reconciliation_differences=short_differences,
        consolidated_unit_difference_rows=consolidated_unit_difference_rows,
        material_accounting_failures=material_failures,
    )
    return ParsedAnnualDataset(fieldnames, tuple(rows), profile)


def canonical_pilot_csv(
    dataset: ParsedAnnualDataset, *, report_date: date = DEFAULT_PILOT_DATE
) -> tuple[bytes, int, int, int]:
    """Create a deterministic CSV for one report date preserving all source fields."""

    selected = [
        row
        for row in dataset.rows
        if row["Report_Date_as_YYYY-MM-DD"].strip() == report_date.isoformat()
    ]
    selected.sort(key=lambda row: row["CFTC_Contract_Market_Code"].strip())
    codes = [row["CFTC_Contract_Market_Code"].strip() for row in selected]
    if not selected:
        raise CFTCHistoricalParseError(f"No rows found for {report_date}")
    if len(codes) != len(set(codes)):
        raise CFTCHistoricalParseError(
            f"Duplicate contract market codes for pilot date {report_date}"
        )
    if report_date == DEFAULT_PILOT_DATE and len(selected) != EXPECTED_DEFAULT_PILOT_ROWS:
        raise CFTCHistoricalParseError(
            f"Expected {EXPECTED_DEFAULT_PILOT_ROWS} pilot rows, found {len(selected)}"
        )

    long_differences = 0
    short_differences = 0
    material_failures = 0
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=list(dataset.fieldnames),
        lineterminator="\n",
        extrasaction="raise",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for index, row in enumerate(selected, start=2):
        long_difference, short_difference, material_failure = _accounting_differences(
            row, row_number=index
        )
        long_differences += int(long_difference != 0)
        short_differences += int(short_difference != 0)
        material_failures += int(material_failure)
        writer.writerow(row)
    if long_differences or short_differences or material_failures:
        raise CFTCHistoricalParseError(
            "Pilot date has open-interest reconciliation differences: "
            f"long={long_differences}, short={short_differences}, "
            f"material={material_failures}"
        )
    return (
        output.getvalue().encode("utf-8"),
        len(selected),
        long_differences,
        short_differences,
    )


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


def write_pilot_derivation(
    output_dir: Path,
    *,
    dataset: ParsedAnnualDataset,
    report_date: date = DEFAULT_PILOT_DATE,
) -> dict[str, Any]:
    """Write annual profile, canonical pilot CSV, and lineage manifest."""

    output_dir.mkdir(parents=True, exist_ok=True)
    pilot_filename = f"tff_futures_only_{report_date.isoformat()}.canonical.csv"
    pilot_bytes, row_count, long_failures, short_failures = canonical_pilot_csv(
        dataset, report_date=report_date
    )
    pilot_rows = list(csv.DictReader(io.StringIO(pilot_bytes.decode("utf-8"), newline="")))
    codes = [row["CFTC_Contract_Market_Code"].strip() for row in pilot_rows]
    pilot_profile = PilotProfile(
        report_date=report_date.isoformat(),
        row_count=row_count,
        unique_contract_market_codes=len(set(codes)),
        long_exact_reconciliation_differences=long_failures,
        short_exact_reconciliation_differences=short_failures,
        consolidated_unit_difference_rows=0,
        material_accounting_failures=0,
        min_contract_market_code=min(codes),
        max_contract_market_code=max(codes),
        canonical_csv_filename=pilot_filename,
        canonical_csv_byte_count=len(pilot_bytes),
        canonical_csv_sha256=_sha256(pilot_bytes),
    )
    _atomic_write(output_dir / pilot_filename, pilot_bytes)
    _atomic_write(
        output_dir / "annual-profile.json",
        (json.dumps(asdict(dataset.profile), indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    _atomic_write(
        output_dir / "pilot-profile.json",
        (json.dumps(asdict(pilot_profile), indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "derivation_id": "CFTC_TFF_2022_09_13_PILOT_V1",
        "source_id": SOURCE_ID,
        "source_archive_filename": SOURCE_ARCHIVE_FILENAME,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_member_name": SOURCE_MEMBER_NAME,
        "source_member_sha256": SOURCE_MEMBER_SHA256,
        "schema_field_count": EXPECTED_SCHEMA_FIELD_COUNT,
        "schema_sha256": EXPECTED_SCHEMA_SHA256,
        "annual_profile": asdict(dataset.profile),
        "pilot_profile": asdict(pilot_profile),
        "lineage_complete": True,
        "source_access_state": "DERIVED_FROM_ACTIONS_STAGED_OFFICIAL_RAW_ARTIFACT",
        "artifact_audit_pass": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    _atomic_write(
        output_dir / "derivation-manifest.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return manifest


def derive_pilot(
    archive_path: str | Path,
    output_dir: str | Path,
    *,
    report_date: date = DEFAULT_PILOT_DATE,
) -> dict[str, Any]:
    """Verify the acquired archive, parse it, and derive the frozen dated pilot."""

    member_bytes = extract_and_verify_member(archive_path)
    dataset = parse_member_bytes(member_bytes)
    return write_pilot_derivation(Path(output_dir), dataset=dataset, report_date=report_date)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-date", type=date.fromisoformat, default=DEFAULT_PILOT_DATE)
    args = parser.parse_args(argv)
    manifest = derive_pilot(args.archive, args.output_dir, report_date=args.report_date)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
