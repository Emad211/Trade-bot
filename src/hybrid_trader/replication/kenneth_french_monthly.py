"""Fail-closed parsing for frozen Kenneth French monthly factor snapshots."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd

SNAPSHOT_ID = "KENNETH_FRENCH_CURRENT_MONTHLY_2026_05_V1"
DATA_STATE = "CURRENT_REVISED_PUBLIC_RECONSTRUCTION_SOURCE"
RETURN_UNIT = "PERCENT"
DATA_LIBRARY_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
DATA_LIBRARY_BYTE_COUNT = 245_739
DATA_LIBRARY_SHA256 = "436a8b99c1d1039b28f494756bbe5b79857a314251cc0b0e4d495fa229cd384e"
REQUIRED_LIBRARY_PHRASES = (
    "Legacy Format (FIZ)",
    "Flat File Format 2.0 (CIZ)",
    "reconstruct the full history of returns each month",
    "Historical returns can change",
)
MONTH_PATTERN = re.compile(r"^\d{6}$")
YEAR_PATTERN = re.compile(r"^\d{4}$")
MISSING_SENTINELS = frozenset({"-99.99", "-999"})


@dataclass(frozen=True)
class MonthlySourceContract:
    source_key: str
    zip_filename: str
    source_url: str
    zip_byte_count: int
    zip_sha256: str
    member_filename: str
    member_byte_count: int
    member_sha256: str
    member_crc32: str
    expected_columns: tuple[str, ...]
    selected_columns: tuple[str, ...]
    expected_monthly_row_count: int
    expected_first_month: str
    expected_last_month: str
    expected_annual_row_count: int
    expected_first_annual_year: int
    expected_last_annual_year: int
    expected_header_index: int
    expected_trailing_delimiter_lines: int
    expected_sentinel_counts: Mapping[str, int]
    expected_preamble_sha256: str
    expected_non_data_line_count: int
    expected_non_data_lines_sha256: str


SOURCE_CONTRACTS: Mapping[str, MonthlySourceContract] = {
    "ff3_monthly": MonthlySourceContract(
        source_key="ff3_monthly",
        zip_filename="F-F_Research_Data_Factors_CSV.zip",
        source_url=(
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
            "F-F_Research_Data_Factors_CSV.zip"
        ),
        zip_byte_count=13_045,
        zip_sha256="80b88699a18ac408e2456d25b1004e340f3f7f8d41d5b476a0285bc53c6f0436",
        member_filename="F-F_Research_Data_Factors.csv",
        member_byte_count=52_373,
        member_sha256="a26fcdeb09199d29bf79d40bb34ce0ffe41798d08feff1190a2c532b4742e88e",
        member_crc32="817e7280",
        expected_columns=("Mkt-RF", "SMB", "HML", "RF"),
        selected_columns=("Mkt-RF", "SMB", "HML", "RF"),
        expected_monthly_row_count=1_199,
        expected_first_month="1926-07",
        expected_last_month="2026-05",
        expected_annual_row_count=99,
        expected_first_annual_year=1927,
        expected_last_annual_year=2025,
        expected_header_index=4,
        expected_trailing_delimiter_lines=0,
        expected_sentinel_counts={"-99.99": 0, "-999": 0},
        expected_preamble_sha256="69147fff2d7579938648ba56045a664758b8d750231a294c1771a86811fcc463",
        expected_non_data_line_count=3,
        expected_non_data_lines_sha256=(
            "7a57b4f8a1af73f95521f48bc5b2e929b95127b6f96998d9e8aef39b1d2b0650"
        ),
    ),
    "ff5_monthly": MonthlySourceContract(
        source_key="ff5_monthly",
        zip_filename="F-F_Research_Data_5_Factors_2x3_CSV.zip",
        source_url=(
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
            "F-F_Research_Data_5_Factors_2x3_CSV.zip"
        ),
        zip_byte_count=11_888,
        zip_sha256="ddc0280b2bb8ca6c4c6ea5b68923a5549c37259bde468202108c11e812bd4241",
        member_filename="F-F_Research_Data_5_Factors_2x3.csv",
        member_byte_count=51_123,
        member_sha256="e101e7bb3ba30d0abe5919ec28fb78723b08bd668041cf0274c65ed7ca5bf249",
        member_crc32="2d6aed5f",
        expected_columns=("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"),
        selected_columns=("RMW", "CMA"),
        expected_monthly_row_count=755,
        expected_first_month="1963-07",
        expected_last_month="2026-05",
        expected_annual_row_count=62,
        expected_first_annual_year=1964,
        expected_last_annual_year=2025,
        expected_header_index=4,
        expected_trailing_delimiter_lines=0,
        expected_sentinel_counts={"-99.99": 0, "-999": 0},
        expected_preamble_sha256="69147fff2d7579938648ba56045a664758b8d750231a294c1771a86811fcc463",
        expected_non_data_line_count=3,
        expected_non_data_lines_sha256=(
            "fcb5c3bb77759979f4b08ff9e0b616ca595cbfd0e82a71e9fe52ae06c3813800"
        ),
    ),
    "momentum_monthly": MonthlySourceContract(
        source_key="momentum_monthly",
        zip_filename="F-F_Momentum_Factor_CSV.zip",
        source_url=(
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
            "F-F_Momentum_Factor_CSV.zip"
        ),
        zip_byte_count=5_605,
        zip_sha256="37baf72ae4eace9715e8746413d0122334c63aa4083fd1c3cf2060fa04e4bd28",
        member_filename="F-F_Momentum_Factor.csv",
        member_byte_count=21_592,
        member_sha256="b82ea7000591bc34b2e7770094b4e378445561fcef7ffb205e92ab2ad8c838b5",
        member_crc32="a4f4869e",
        expected_columns=("Mom",),
        selected_columns=("Mom",),
        expected_monthly_row_count=1_193,
        expected_first_month="1927-01",
        expected_last_month="2026-05",
        expected_annual_row_count=99,
        expected_first_annual_year=1927,
        expected_last_annual_year=2025,
        expected_header_index=13,
        expected_trailing_delimiter_lines=0,
        expected_sentinel_counts={"-99.99": 0, "-999": 0},
        expected_preamble_sha256="e3eecd6e02b3fad7f5d7a3b61db1e7326f7ad6559424bbe23f3825c9ce95e584",
        expected_non_data_line_count=4,
        expected_non_data_lines_sha256=(
            "7409a8e61377e4e4b883838dc7a81f99daa6398d9be58e5a5335f4680d576cb5"
        ),
    ),
}

SELECTED_FACTOR_SOURCE: Mapping[str, tuple[str, str]] = {
    "Mkt-RF": ("ff3_monthly", "Mkt-RF"),
    "SMB": ("ff3_monthly", "SMB"),
    "HML": ("ff3_monthly", "HML"),
    "RMW": ("ff5_monthly", "RMW"),
    "CMA": ("ff5_monthly", "CMA"),
    "Mom": ("momentum_monthly", "Mom"),
    "RF": ("ff3_monthly", "RF"),
}


@dataclass(frozen=True)
class ParsedMonthlySource:
    contract: MonthlySourceContract
    monthly_frame: pd.DataFrame
    annual_frame: pd.DataFrame
    zip_byte_count: int
    zip_sha256: str
    member_byte_count: int
    member_sha256: str
    member_crc32: str
    encoding: str
    header_index: int
    trailing_delimiter_lines: int
    sentinel_counts: dict[str, int]
    preamble_sha256: str
    non_data_line_count: int
    non_data_lines_sha256: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def trim_one_trailing_empty(cells: Sequence[str]) -> list[str]:
    normalized = [cell.strip() for cell in cells]
    if normalized and normalized[-1] == "":
        normalized.pop()
    return normalized


def validate_data_library_page(
    page: bytes, *, require_exact_snapshot: bool = True
) -> dict[str, Any]:
    if not page:
        raise ValueError("Kenneth French Data Library page is empty")
    if require_exact_snapshot:
        if len(page) != DATA_LIBRARY_BYTE_COUNT:
            raise ValueError(f"Data Library byte count changed: {len(page)}")
        digest = sha256_bytes(page)
        if digest != DATA_LIBRARY_SHA256:
            raise ValueError(f"Data Library SHA-256 changed: {digest}")
    text = page.decode("utf-8", errors="replace")
    phrase_presence = {phrase: phrase in text for phrase in REQUIRED_LIBRARY_PHRASES}
    if not all(phrase_presence.values()):
        raise ValueError(f"Data Library revision warning changed: {phrase_presence}")
    return {
        "url": DATA_LIBRARY_URL,
        "byte_count": len(page),
        "sha256": sha256_bytes(page),
        "revision_warning_phrase_presence": phrase_presence,
    }


def _read_single_safe_member(
    zip_bytes: bytes, contract: MonthlySourceContract
) -> tuple[bytes, str]:
    if not zip_bytes:
        raise ValueError(f"Empty ZIP for {contract.source_key}")
    if len(zip_bytes) > 100_000_000:
        raise ValueError(f"ZIP exceeds size cap for {contract.source_key}")
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise ValueError(f"Invalid ZIP for {contract.source_key}")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if len(members) != 1:
            raise ValueError(f"Expected one regular member for {contract.source_key}")
        member = members[0]
        posix = PurePosixPath(member.filename)
        if posix.is_absolute() or ".." in posix.parts or len(posix.parts) != 1:
            raise ValueError(f"Unsafe ZIP member path: {member.filename}")
        if member.flag_bits & 1:
            raise ValueError(f"Encrypted ZIP member: {member.filename}")
        if member.filename != contract.member_filename:
            raise ValueError(
                f"Unexpected member name for {contract.source_key}: {member.filename}"
            )
        if member.file_size <= 0 or member.file_size > 100_000_000:
            raise ValueError(f"Unsafe member size for {contract.source_key}")
        payload = archive.read(member)
        if len(payload) != member.file_size:
            raise ValueError(f"Member-size mismatch for {contract.source_key}")
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"ZIP CRC failure for {contract.source_key}: {bad_member}")
        member_crc32 = f"{member.CRC:08x}"
    return payload, member_crc32


def _parse_numeric_block(
    rows: Sequence[Sequence[str]], columns: Sequence[str], *, label: str
) -> tuple[dict[str, list[float]], dict[str, int]]:
    sentinel_counts = {sentinel: 0 for sentinel in sorted(MISSING_SENTINELS)}
    data = {column: [] for column in columns}
    for row in rows:
        for index, column in enumerate(columns, start=1):
            cell = row[index]
            if cell in sentinel_counts:
                sentinel_counts[cell] += 1
                data[column].append(float("nan"))
                continue
            try:
                value = float(cell)
            except ValueError as exc:
                raise ValueError(f"Non-numeric {label}.{column} on {row[0]}") from exc
            if not math.isfinite(value):
                raise ValueError(f"Non-finite {label}.{column} on {row[0]}")
            data[column].append(value)
    return data, sentinel_counts


def parse_monthly_zip(
    zip_bytes: bytes,
    contract: MonthlySourceContract,
    *,
    require_exact_snapshot: bool = True,
) -> ParsedMonthlySource:
    """Parse exact monthly and annual blocks without mixing their observations."""

    if require_exact_snapshot:
        if len(zip_bytes) != contract.zip_byte_count:
            raise ValueError(
                f"{contract.source_key} ZIP byte count changed: {len(zip_bytes)}"
            )
        zip_digest = sha256_bytes(zip_bytes)
        if zip_digest != contract.zip_sha256:
            raise ValueError(f"{contract.source_key} ZIP SHA-256 changed: {zip_digest}")
    payload, member_crc32 = _read_single_safe_member(zip_bytes, contract)
    if require_exact_snapshot:
        if len(payload) != contract.member_byte_count:
            raise ValueError(
                f"{contract.source_key} member byte count changed: {len(payload)}"
            )
        member_digest = sha256_bytes(payload)
        if member_digest != contract.member_sha256:
            raise ValueError(
                f"{contract.source_key} member SHA-256 changed: {member_digest}"
            )
        if member_crc32 != contract.member_crc32:
            raise ValueError(
                f"{contract.source_key} member CRC changed: {member_crc32}"
            )

    try:
        text = payload.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        text = payload.decode("latin-1")
        encoding = "latin-1"
    lines = text.splitlines()
    expected_header = ["", *contract.expected_columns]
    header_index: int | None = None
    header: list[str] | None = None
    for index, line in enumerate(lines):
        candidate = trim_one_trailing_empty(next(csv.reader([line])))
        if candidate == expected_header:
            header_index = index
            header = candidate
            break
    if header_index is None or header is None:
        raise ValueError(f"Expected monthly header not found for {contract.source_key}")
    if require_exact_snapshot and header_index != contract.expected_header_index:
        raise ValueError(
            f"{contract.source_key} header position changed: {header_index}"
        )

    monthly_rows: list[list[str]] = []
    annual_rows: list[list[str]] = []
    non_data_lines: list[str] = []
    annual_started = False
    trailing_delimiter_lines = 0
    for line in lines[header_index + 1 :]:
        raw_cells = next(csv.reader([line]))
        if raw_cells and raw_cells[-1].strip() == "":
            trailing_delimiter_lines += 1
        row = trim_one_trailing_empty(raw_cells)
        if not row or all(cell == "" for cell in row):
            continue
        if MONTH_PATTERN.fullmatch(row[0]):
            if annual_started:
                raise ValueError(
                    f"Monthly row after annual block for {contract.source_key}"
                )
            if len(row) != len(header):
                raise ValueError(
                    f"Monthly width mismatch for {contract.source_key} on {row[0]}"
                )
            if any(cell == "" for cell in row):
                raise ValueError(
                    f"Internal blank monthly field for {contract.source_key} on {row[0]}"
                )
            monthly_rows.append(row)
            continue
        if YEAR_PATTERN.fullmatch(row[0]):
            annual_started = True
            if len(row) != len(header):
                raise ValueError(
                    f"Annual width mismatch for {contract.source_key} on {row[0]}"
                )
            if any(cell == "" for cell in row):
                raise ValueError(
                    f"Internal blank annual field for {contract.source_key} on {row[0]}"
                )
            annual_rows.append(row)
            continue
        if monthly_rows:
            non_data_lines.append(line)
    if not monthly_rows:
        raise ValueError(f"No monthly rows for {contract.source_key}")
    if not annual_rows:
        raise ValueError(f"No annual rows for {contract.source_key}")

    months = [datetime.strptime(row[0], "%Y%m") for row in monthly_rows]
    if months != sorted(months):
        raise ValueError(f"Months are not sorted for {contract.source_key}")
    if len(months) != len(set(months)):
        raise ValueError(f"Duplicate months for {contract.source_key}")
    expected_months = list(
        pd.date_range(months[0], months[-1], freq="MS").to_pydatetime()
    )
    if months != expected_months:
        raise ValueError(f"Monthly calendar gap for {contract.source_key}")

    years = [int(row[0]) for row in annual_rows]
    if years != sorted(years):
        raise ValueError(f"Annual years are not sorted for {contract.source_key}")
    if len(years) != len(set(years)):
        raise ValueError(f"Duplicate annual years for {contract.source_key}")

    monthly_data, monthly_sentinels = _parse_numeric_block(
        monthly_rows, contract.expected_columns, label=contract.source_key
    )
    annual_data, annual_sentinels = _parse_numeric_block(
        annual_rows, contract.expected_columns, label=f"{contract.source_key}.annual"
    )
    combined_sentinels = {
        sentinel: monthly_sentinels[sentinel] + annual_sentinels[sentinel]
        for sentinel in monthly_sentinels
    }
    monthly_frame = pd.DataFrame(
        {"Date": pd.DatetimeIndex(months), **monthly_data}
    )
    annual_frame = pd.DataFrame({"Year": years, **annual_data})

    preamble = "\n".join(lines[:header_index]) + "\n"
    non_data = "\n".join(non_data_lines) + ("\n" if non_data_lines else "")
    preamble_sha256 = sha256_bytes(preamble.encode("utf-8"))
    non_data_sha256 = sha256_bytes(non_data.encode("utf-8"))

    if require_exact_snapshot:
        if len(monthly_frame) != contract.expected_monthly_row_count:
            raise ValueError(
                f"{contract.source_key} monthly row count changed: "
                f"{len(monthly_frame)}"
            )
        if monthly_frame["Date"].iloc[0].strftime("%Y-%m") != contract.expected_first_month:
            raise ValueError(f"{contract.source_key} first month changed")
        if monthly_frame["Date"].iloc[-1].strftime("%Y-%m") != contract.expected_last_month:
            raise ValueError(f"{contract.source_key} last month changed")
        if len(annual_frame) != contract.expected_annual_row_count:
            raise ValueError(
                f"{contract.source_key} annual row count changed: {len(annual_frame)}"
            )
        if years[0] != contract.expected_first_annual_year:
            raise ValueError(f"{contract.source_key} first annual year changed")
        if years[-1] != contract.expected_last_annual_year:
            raise ValueError(f"{contract.source_key} last annual year changed")
        if trailing_delimiter_lines != contract.expected_trailing_delimiter_lines:
            raise ValueError(
                f"{contract.source_key} trailing-delimiter count changed: "
                f"{trailing_delimiter_lines}"
            )
        if combined_sentinels != dict(contract.expected_sentinel_counts):
            raise ValueError(
                f"{contract.source_key} sentinel counts changed: {combined_sentinels}"
            )
        if preamble_sha256 != contract.expected_preamble_sha256:
            raise ValueError(f"{contract.source_key} preamble changed")
        if len(non_data_lines) != contract.expected_non_data_line_count:
            raise ValueError(
                f"{contract.source_key} non-data line count changed: "
                f"{len(non_data_lines)}"
            )
        if non_data_sha256 != contract.expected_non_data_lines_sha256:
            raise ValueError(f"{contract.source_key} non-data lines changed")

    monthly_frame.attrs.update(
        {
            "snapshot_id": SNAPSHOT_ID,
            "source_key": contract.source_key,
            "data_state": DATA_STATE,
            "return_unit": RETURN_UNIT,
            "selected_columns": contract.selected_columns,
            "zip_sha256": sha256_bytes(zip_bytes),
            "member_sha256": sha256_bytes(payload),
            "daily_compounding_used_as_monthly_substitute": False,
        }
    )
    return ParsedMonthlySource(
        contract=contract,
        monthly_frame=monthly_frame,
        annual_frame=annual_frame,
        zip_byte_count=len(zip_bytes),
        zip_sha256=sha256_bytes(zip_bytes),
        member_byte_count=len(payload),
        member_sha256=sha256_bytes(payload),
        member_crc32=member_crc32,
        encoding=encoding,
        header_index=header_index,
        trailing_delimiter_lines=trailing_delimiter_lines,
        sentinel_counts=combined_sentinels,
        preamble_sha256=preamble_sha256,
        non_data_line_count=len(non_data_lines),
        non_data_lines_sha256=non_data_sha256,
    )


def build_selected_monthly_panel(
    parsed: Mapping[str, ParsedMonthlySource],
) -> pd.DataFrame:
    """Combine only the frozen monthly factor definitions."""

    if set(parsed) != set(SOURCE_CONTRACTS):
        raise ValueError(
            f"Expected sources {sorted(SOURCE_CONTRACTS)}, found {sorted(parsed)}"
        )
    parts: list[pd.DataFrame] = []
    for factor, (source_key, column) in SELECTED_FACTOR_SOURCE.items():
        source = parsed[source_key]
        if column not in source.contract.selected_columns:
            raise ValueError(
                f"Unapproved monthly factor mapping: {factor} <- {source_key}.{column}"
            )
        part = (
            source.monthly_frame[["Date", column]]
            .rename(columns={column: factor})
            .set_index("Date")
        )
        parts.append(part)
    panel = pd.concat(parts, axis=1, join="outer").sort_index()
    panel.index.name = "Date"
    panel.attrs.update(
        {
            "snapshot_id": SNAPSHOT_ID,
            "data_state": DATA_STATE,
            "return_unit": RETURN_UNIT,
            "factor_source_mapping": dict(SELECTED_FACTOR_SOURCE),
            "daily_compounding_used_as_monthly_substitute": False,
            "performance_calculation_authorized": False,
        }
    )
    return panel


def safe_contract_evidence(
    *, page: bytes, source_zips: Mapping[str, bytes]
) -> dict[str, Any]:
    page_identity = validate_data_library_page(page)
    if set(source_zips) != set(SOURCE_CONTRACTS):
        raise ValueError("Monthly source ZIP set is incomplete or contains extras")
    parsed = {
        key: parse_monthly_zip(source_zips[key], contract)
        for key, contract in SOURCE_CONTRACTS.items()
    }
    panel = build_selected_monthly_panel(parsed)
    profiles = []
    for key in SOURCE_CONTRACTS:
        source = parsed[key]
        profiles.append(
            {
                "source_key": key,
                "source_url": source.contract.source_url,
                "zip_filename": source.contract.zip_filename,
                "zip_byte_count": source.zip_byte_count,
                "zip_sha256": source.zip_sha256,
                "member_filename": source.contract.member_filename,
                "member_byte_count": source.member_byte_count,
                "member_sha256": source.member_sha256,
                "member_crc32": source.member_crc32,
                "encoding": source.encoding,
                "header": ["", *source.contract.expected_columns],
                "header_index_zero_based": source.header_index,
                "selected_columns": list(source.contract.selected_columns),
                "monthly_row_count": len(source.monthly_frame),
                "first_month": source.monthly_frame["Date"].iloc[0].strftime("%Y-%m"),
                "last_month": source.monthly_frame["Date"].iloc[-1].strftime("%Y-%m"),
                "annual_row_count": len(source.annual_frame),
                "first_annual_year": int(source.annual_frame["Year"].iloc[0]),
                "last_annual_year": int(source.annual_frame["Year"].iloc[-1]),
                "trailing_delimiter_line_count": source.trailing_delimiter_lines,
                "sentinel_counts": source.sentinel_counts,
                "preamble_sha256": source.preamble_sha256,
                "non_data_line_count": source.non_data_line_count,
                "non_data_lines_sha256": source.non_data_lines_sha256,
            }
        )
    return {
        "schema_version": "1.0",
        "evidence_id": "KENNETH_FRENCH_CURRENT_MONTHLY_FACTOR_CONTRACT_AUDIT_V1",
        "snapshot_id": SNAPSHOT_ID,
        "data_state": DATA_STATE,
        "declared_return_unit": RETURN_UNIT,
        "data_library": page_identity,
        "source_profiles": profiles,
        "selected_factor_source": {
            factor: {"source_key": value[0], "column": value[1]}
            for factor, value in SELECTED_FACTOR_SOURCE.items()
        },
        "selected_panel_first_month": panel.index.min().strftime("%Y-%m"),
        "selected_panel_last_month": panel.index.max().strftime("%Y-%m"),
        "daily_compounding_used_as_monthly_substitute": False,
        "daily_historical_vintage_archive_verified": False,
        "monthly_historical_archives_exist": True,
        "exact_paper_vintage_verified": False,
        "raw_uploaded": False,
        "row_level_data_uploaded": False,
        "source_reconciliation_calculated": False,
        "performance_calculated": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def write_safe_contract_evidence(
    *,
    page_path: str | Path,
    zip_paths: Mapping[str, str | Path],
    output_dir: str | Path,
) -> dict[str, Any]:
    page = Path(page_path).read_bytes()
    source_zips = {key: Path(value).read_bytes() for key, value in zip_paths.items()}
    evidence = safe_contract_evidence(page=page, source_zips=source_zips)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_bytes = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode()
    (output_root / "safe-monthly-factor-contract-evidence.json").write_bytes(
        evidence_bytes
    )
    summary = {
        "snapshot_id": SNAPSHOT_ID,
        "data_state": DATA_STATE,
        "source_count": len(evidence["source_profiles"]),
        "source_identities": [
            {
                "source_key": profile["source_key"],
                "zip_sha256": profile["zip_sha256"],
                "member_sha256": profile["member_sha256"],
                "monthly_row_count": profile["monthly_row_count"],
                "first_month": profile["first_month"],
                "last_month": profile["last_month"],
                "annual_row_count": profile["annual_row_count"],
            }
            for profile in evidence["source_profiles"]
        ],
        "selected_factor_source": evidence["selected_factor_source"],
        "safe_evidence_sha256": sha256_bytes(evidence_bytes),
        "source_reconciliation_calculated": False,
        "performance_calculated": False,
        "paper_replication_pass": False,
    }
    (output_root / "safe-monthly-factor-contract-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return evidence
