"""Fail-closed parsing for frozen Kenneth French daily factor snapshots."""

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

SNAPSHOT_ID = "KENNETH_FRENCH_CURRENT_DAILY_2026_05_V1"
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
DATE_PATTERN = re.compile(r"^\d{8}$")
MISSING_SENTINELS = frozenset({"-99.99", "-999"})


@dataclass(frozen=True)
class DailySourceContract:
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
    expected_row_count: int
    expected_first_date: str
    expected_last_date: str
    expected_header_index: int
    expected_trailing_delimiter_rows: int
    expected_sentinel_counts: Mapping[str, int]


SOURCE_CONTRACTS: Mapping[str, DailySourceContract] = {
    "ff3": DailySourceContract(
        source_key="ff3",
        zip_filename="F-F_Research_Data_Factors_daily_CSV.zip",
        source_url=(
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
            "F-F_Research_Data_Factors_daily_CSV.zip"
        ),
        zip_byte_count=177_699,
        zip_sha256="af8aec07d55c98caa15045a77b87455be68cb8847b2ee5bd03bf5c2c8a3f96e2",
        member_filename="F-F_Research_Data_Factors_daily.csv",
        member_byte_count=1_208_053,
        member_sha256="f051e37d30c129359c6801d9d2a715c929b19aa3be0ffe684b93995ede9ffebb",
        member_crc32="042c4b83",
        expected_columns=("Mkt-RF", "SMB", "HML", "RF"),
        selected_columns=("Mkt-RF", "SMB", "HML", "RF"),
        expected_row_count=26_253,
        expected_first_date="1926-07-01",
        expected_last_date="2026-05-29",
        expected_header_index=4,
        expected_trailing_delimiter_rows=0,
        expected_sentinel_counts={"-99.99": 0, "-999": 0},
    ),
    "ff5": DailySourceContract(
        source_key="ff5",
        zip_filename="F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
        source_url=(
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
            "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
        ),
        zip_byte_count=149_700,
        zip_sha256="bcf32ecc9e2bb20383784ac98891e42146a0091eec6ec77d3b5bf0d4e981e3f6",
        member_filename="F-F_Research_Data_5_Factors_2x3_daily.csv",
        member_byte_count=1_013_735,
        member_sha256="8b6cf2992ccdc6086fc11b594b74ca8095843622deaee0602196b8deab0287b1",
        member_crc32="52b63b11",
        expected_columns=("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"),
        selected_columns=("RMW", "CMA"),
        expected_row_count=15_833,
        expected_first_date="1963-07-01",
        expected_last_date="2026-05-29",
        expected_header_index=4,
        expected_trailing_delimiter_rows=0,
        expected_sentinel_counts={"-99.99": 0, "-999": 0},
    ),
    "mom": DailySourceContract(
        source_key="mom",
        zip_filename="F-F_Momentum_Factor_daily_CSV.zip",
        source_url=(
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
            "F-F_Momentum_Factor_daily_CSV.zip"
        ),
        zip_byte_count=89_788,
        zip_sha256="f4237e2e36dffa13fd7823f55376316a94b5ac663af951dd9eaca8ed2c678bcf",
        member_filename="F-F_Momentum_Factor_daily.csv",
        member_byte_count=427_515,
        member_sha256="3f396e1381861a65f7cd37c86483f163e17fb2516a2ad4d0f66a312d48a860b2",
        member_crc32="2e0f1b00",
        expected_columns=("Mom",),
        selected_columns=("Mom",),
        expected_row_count=26_152,
        expected_first_date="1926-11-03",
        expected_last_date="2026-05-29",
        expected_header_index=13,
        expected_trailing_delimiter_rows=26_154,
        expected_sentinel_counts={"-99.99": 0, "-999": 0},
    ),
}

SELECTED_FACTOR_SOURCE: Mapping[str, tuple[str, str]] = {
    "Mkt-RF": ("ff3", "Mkt-RF"),
    "SMB": ("ff3", "SMB"),
    "HML": ("ff3", "HML"),
    "RMW": ("ff5", "RMW"),
    "CMA": ("ff5", "CMA"),
    "Mom": ("mom", "Mom"),
    "RF": ("ff3", "RF"),
}


@dataclass(frozen=True)
class ParsedDailySource:
    contract: DailySourceContract
    frame: pd.DataFrame
    zip_byte_count: int
    zip_sha256: str
    member_byte_count: int
    member_sha256: str
    member_crc32: str
    encoding: str
    header_index: int
    trailing_delimiter_rows: int
    sentinel_counts: dict[str, int]
    preamble_sha256: str
    footer_line_count: int
    footer_sha256: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def trim_trailing_empty(cells: Sequence[str]) -> list[str]:
    """Remove at most one official trailing delimiter; preserve internal blanks."""

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
    zip_bytes: bytes, contract: DailySourceContract
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
        posix_path = PurePosixPath(member.filename)
        if (
            posix_path.is_absolute()
            or ".." in posix_path.parts
            or len(posix_path.parts) != 1
        ):
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


def parse_daily_zip(
    zip_bytes: bytes,
    contract: DailySourceContract,
    *,
    require_exact_snapshot: bool = True,
) -> ParsedDailySource:
    """Parse one official daily factor ZIP and preserve the declared percent unit."""

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
    header_index: int | None = None
    header: list[str] | None = None
    expected_header = ["", *contract.expected_columns]
    for index, line in enumerate(lines):
        candidate = trim_trailing_empty(next(csv.reader([line])))
        if candidate == expected_header:
            header_index = index
            header = candidate
            break
    if header_index is None or header is None:
        raise ValueError(f"Expected header not found for {contract.source_key}")
    if require_exact_snapshot and header_index != contract.expected_header_index:
        raise ValueError(
            f"{contract.source_key} header position changed: {header_index}"
        )

    rows: list[list[str]] = []
    footer_lines: list[str] = []
    started = False
    trailing_delimiter_rows = 0
    for line in lines[header_index + 1 :]:
        raw_cells = next(csv.reader([line]))
        if raw_cells and raw_cells[-1].strip() == "":
            trailing_delimiter_rows += 1
        normalized = trim_trailing_empty(raw_cells)
        if normalized and DATE_PATTERN.fullmatch(normalized[0]):
            started = True
            if len(normalized) != len(header):
                raise ValueError(
                    f"Normalized row-width mismatch for {contract.source_key} "
                    f"on {normalized[0]}"
                )
            if any(cell == "" for cell in normalized):
                raise ValueError(
                    f"Internal blank field for {contract.source_key} on {normalized[0]}"
                )
            rows.append(normalized)
        elif started:
            footer_lines.append(line)
    if not rows:
        raise ValueError(f"No daily records for {contract.source_key}")

    dates = [datetime.strptime(row[0], "%Y%m%d") for row in rows]
    if dates != sorted(dates):
        raise ValueError(f"Dates are not sorted for {contract.source_key}")
    if len(dates) != len(set(dates)):
        raise ValueError(f"Duplicate dates for {contract.source_key}")

    sentinel_counts = {sentinel: 0 for sentinel in sorted(MISSING_SENTINELS)}
    data: dict[str, list[float]] = {
        column: [] for column in contract.expected_columns
    }
    for row in rows:
        for index, column in enumerate(contract.expected_columns, start=1):
            cell = row[index]
            if cell in sentinel_counts:
                sentinel_counts[cell] += 1
                data[column].append(float("nan"))
                continue
            try:
                value = float(cell)
            except ValueError as exc:
                raise ValueError(
                    f"Non-numeric {contract.source_key}.{column} on {row[0]}"
                ) from exc
            if not math.isfinite(value):
                raise ValueError(
                    f"Non-finite {contract.source_key}.{column} on {row[0]}"
                )
            data[column].append(value)

    frame = pd.DataFrame({"Date": pd.DatetimeIndex(dates), **data})
    if require_exact_snapshot:
        if len(frame) != contract.expected_row_count:
            raise ValueError(
                f"{contract.source_key} row count changed: {len(frame)}"
            )
        if (
            frame["Date"].iloc[0].strftime("%Y-%m-%d")
            != contract.expected_first_date
        ):
            raise ValueError(f"{contract.source_key} first date changed")
        if (
            frame["Date"].iloc[-1].strftime("%Y-%m-%d")
            != contract.expected_last_date
        ):
            raise ValueError(f"{contract.source_key} last date changed")
        if trailing_delimiter_rows != contract.expected_trailing_delimiter_rows:
            raise ValueError(
                f"{contract.source_key} trailing-delimiter count changed: "
                f"{trailing_delimiter_rows}"
            )
        if sentinel_counts != dict(contract.expected_sentinel_counts):
            raise ValueError(
                f"{contract.source_key} sentinel counts changed: {sentinel_counts}"
            )

    frame.attrs.update(
        {
            "snapshot_id": SNAPSHOT_ID,
            "source_key": contract.source_key,
            "data_state": DATA_STATE,
            "return_unit": RETURN_UNIT,
            "selected_columns": contract.selected_columns,
            "zip_sha256": sha256_bytes(zip_bytes),
            "member_sha256": sha256_bytes(payload),
        }
    )
    preamble = "\n".join(lines[:header_index]) + "\n"
    footer = "\n".join(footer_lines) + ("\n" if footer_lines else "")
    return ParsedDailySource(
        contract=contract,
        frame=frame,
        zip_byte_count=len(zip_bytes),
        zip_sha256=sha256_bytes(zip_bytes),
        member_byte_count=len(payload),
        member_sha256=sha256_bytes(payload),
        member_crc32=member_crc32,
        encoding=encoding,
        header_index=header_index,
        trailing_delimiter_rows=trailing_delimiter_rows,
        sentinel_counts=sentinel_counts,
        preamble_sha256=sha256_bytes(preamble.encode("utf-8")),
        footer_line_count=len(footer_lines),
        footer_sha256=sha256_bytes(footer.encode("utf-8")),
    )


def build_selected_daily_panel(
    parsed: Mapping[str, ParsedDailySource],
) -> pd.DataFrame:
    """Combine only predeclared definitions; never silently mix FF3 and FF5."""

    if set(parsed) != set(SOURCE_CONTRACTS):
        raise ValueError(
            f"Expected sources {sorted(SOURCE_CONTRACTS)}, found {sorted(parsed)}"
        )
    parts: list[pd.DataFrame] = []
    for factor, (source_key, column) in SELECTED_FACTOR_SOURCE.items():
        source = parsed[source_key]
        if column not in source.contract.selected_columns:
            raise ValueError(
                f"Unapproved factor source mapping: {factor} <- {source_key}.{column}"
            )
        part = (
            source.frame[["Date", column]]
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
            "performance_calculation_authorized": False,
        }
    )
    return panel


def safe_contract_evidence(
    *, page: bytes, source_zips: Mapping[str, bytes]
) -> dict[str, Any]:
    page_identity = validate_data_library_page(page)
    if set(source_zips) != set(SOURCE_CONTRACTS):
        raise ValueError("Daily source ZIP set is incomplete or contains extras")
    parsed = {
        source_key: parse_daily_zip(source_zips[source_key], contract)
        for source_key, contract in SOURCE_CONTRACTS.items()
    }
    panel = build_selected_daily_panel(parsed)
    source_profiles = []
    for source_key in SOURCE_CONTRACTS:
        source = parsed[source_key]
        source_profiles.append(
            {
                "source_key": source_key,
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
                "row_count": len(source.frame),
                "first_date": source.frame["Date"].iloc[0].strftime("%Y-%m-%d"),
                "last_date": source.frame["Date"].iloc[-1].strftime("%Y-%m-%d"),
                "trailing_delimiter_row_count": source.trailing_delimiter_rows,
                "sentinel_counts": source.sentinel_counts,
                "preamble_sha256": source.preamble_sha256,
                "footer_line_count": source.footer_line_count,
                "footer_sha256": source.footer_sha256,
            }
        )
    return {
        "schema_version": "1.0",
        "evidence_id": "KENNETH_FRENCH_CURRENT_DAILY_FACTOR_CONTRACT_AUDIT_V1",
        "snapshot_id": SNAPSHOT_ID,
        "data_state": DATA_STATE,
        "declared_return_unit": RETURN_UNIT,
        "data_library": page_identity,
        "source_profiles": source_profiles,
        "selected_factor_source": {
            factor: {"source_key": value[0], "column": value[1]}
            for factor, value in SELECTED_FACTOR_SOURCE.items()
        },
        "selected_panel_first_date": panel.index.min().strftime("%Y-%m-%d"),
        "selected_panel_last_date": panel.index.max().strftime("%Y-%m-%d"),
        "daily_historical_vintage_archive_verified": False,
        "historical_revisions_possible": True,
        "legacy_to_flat_file_change": (
            "FIZ_TO_CIZ_BEGINNING_JANUARY_2025_RELEASE"
        ),
        "raw_uploaded": False,
        "row_level_data_uploaded": False,
        "monthly_aggregation_calculated": False,
        "performance_calculated": False,
        "recursive_strategy_constructed": False,
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
    source_zips = {key: Path(path).read_bytes() for key, path in zip_paths.items()}
    evidence = safe_contract_evidence(page=page, source_zips=source_zips)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_bytes = (
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    (output_root / "safe-daily-factor-contract-evidence.json").write_bytes(
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
                "row_count": profile["row_count"],
                "first_date": profile["first_date"],
                "last_date": profile["last_date"],
            }
            for profile in evidence["source_profiles"]
        ],
        "selected_factor_source": evidence["selected_factor_source"],
        "safe_evidence_sha256": sha256_bytes(evidence_bytes),
        "monthly_aggregation_calculated": False,
        "performance_calculated": False,
        "paper_replication_pass": False,
    }
    (output_root / "safe-daily-factor-contract-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return evidence
