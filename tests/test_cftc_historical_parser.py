from __future__ import annotations

import csv
import io
import zipfile
from datetime import date
from pathlib import Path

import pytest

from hybrid_trader.replication.cftc_historical_parser import (
    AnnualDatasetProfile,
    CFTCHistoricalParseError,
    ParsedAnnualDataset,
    canonical_pilot_csv,
    extract_and_verify_member,
    schema_fingerprint,
)


def _synthetic_row(code: str) -> dict[str, str]:
    return {
        "Market_and_Exchange_Names": "SYNTHETIC MARKET",
        "As_of_Date_In_Form_YYMMDD": "220104",
        "Report_Date_as_YYYY-MM-DD": "2022-01-04",
        "CFTC_Contract_Market_Code": code,
        "Open_Interest_All": "100",
        "Tot_Rept_Positions_Long_All": "80",
        "Tot_Rept_Positions_Short_All": "70",
        "NonRept_Positions_Long_All": "20",
        "NonRept_Positions_Short_All": "30",
    }


def _profile(fieldnames: tuple[str, ...], *, material_failures: int = 0) -> AnnualDatasetProfile:
    return AnnualDatasetProfile(
        source_id="fixture",
        archive_sha256="a" * 64,
        member_name="fixture.txt",
        member_sha256="b" * 64,
        schema_field_count=len(fieldnames),
        schema_sha256=schema_fingerprint(fieldnames),
        row_count=2,
        report_date_count=1,
        min_report_date="2022-01-04",
        max_report_date="2022-01-04",
        unique_report_contract_keys=2,
        futures_only_rows=2,
        long_exact_reconciliation_differences=material_failures,
        short_exact_reconciliation_differences=0,
        consolidated_unit_difference_rows=0,
        material_accounting_failures=material_failures,
    )


def test_schema_fingerprint_depends_on_order() -> None:
    assert schema_fingerprint(["a", "b"]) != schema_fingerprint(["b", "a"])


def test_canonical_pilot_sorts_codes_and_preserves_values() -> None:
    fieldnames = tuple(_synthetic_row("2").keys())
    dataset = ParsedAnnualDataset(
        fieldnames=fieldnames,
        rows=(_synthetic_row("2"), _synthetic_row("1")),
        profile=_profile(fieldnames),
    )
    pilot, row_count, long_differences, short_differences = canonical_pilot_csv(
        dataset, report_date=date(2022, 1, 4)
    )
    rows = list(csv.DictReader(io.StringIO(pilot.decode("utf-8"))))
    assert [row["CFTC_Contract_Market_Code"] for row in rows] == ["1", "2"]
    assert row_count == 2
    assert long_differences == 0
    assert short_differences == 0


def test_canonical_pilot_rejects_material_accounting_difference() -> None:
    row = _synthetic_row("1")
    row["NonRept_Positions_Long_All"] = "19"
    fieldnames = tuple(row)
    dataset = ParsedAnnualDataset(fieldnames, (row,), _profile(fieldnames, material_failures=1))
    with pytest.raises(CFTCHistoricalParseError, match="reconciliation differences"):
        canonical_pilot_csv(dataset, report_date=date(2022, 1, 4))


def test_modified_archive_is_rejected(tmp_path: Path) -> None:
    modified = tmp_path / "modified.zip"
    with zipfile.ZipFile(modified, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("FinFutYY.txt", b"not the acquired source")
    with pytest.raises(CFTCHistoricalParseError, match="Archive SHA-256"):
        extract_and_verify_member(modified)
