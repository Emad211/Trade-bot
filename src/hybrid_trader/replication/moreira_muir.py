"""Fail-closed parsing and safe evidence for official Moreira-Muir factor data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SNAPSHOT_ID = "MOREIRA_MUIR_VOL_MANAGED_FACTORS_2026_01_V1"
SOURCE_URL = "https://tylersmuir.com/data/VolManagedFactors.csv"
AUTHOR_PAGE_URL = "https://tylersmuir.com/data.html"
EXPECTED_BYTE_COUNT = 113_060
EXPECTED_SHA256 = "e9d92955e6ef2154aa55d05eed7b9237a313b987aad9afb0fdffd2103a81a6ba"
EXPECTED_ROW_COUNT = 1_189
EXPECTED_FIRST_MONTH = "1927-01"
EXPECTED_LAST_MONTH = "2026-01"
EXPECTED_HEADER = (
    "Date",
    "Mkt-RF_VM",
    "SMB_VM",
    "HML_VM",
    "Mom_VM",
    "RMW_VM",
    "CMA_VM",
    "Mkt-RF",
    "SMB",
    "HML",
    "Mom",
    "RMW",
    "CMA",
    "RF",
)
FACTOR_PAIRS: Mapping[str, tuple[str, str]] = {
    "Mkt-RF": ("Mkt-RF_VM", "Mkt-RF"),
    "SMB": ("SMB_VM", "SMB"),
    "HML": ("HML_VM", "HML"),
    "Mom": ("Mom_VM", "Mom"),
    "RMW": ("RMW_VM", "RMW"),
    "CMA": ("CMA_VM", "CMA"),
}
LATE_START_PAIRS = ("RMW", "CMA")
EXPECTED_LATE_START_MISSING_COUNT = 439
VOLATILITY_MATCH_RELATIVE_TOLERANCE = 0.025
SAFE_METRIC_DECIMAL_PLACES = 12
REQUIRED_AUTHOR_PAGE_PHRASES = (
    "Volatility-Managed Factor Returns",
    "Returns are in percent",
    "inverse of the prior month",
)


@dataclass(frozen=True)
class FactorPairAudit:
    factor: str
    managed_column: str
    unmanaged_column: str
    overlap_count: int
    first_overlap_month: str
    last_overlap_month: str
    managed_standard_deviation_percent: float
    unmanaged_standard_deviation_percent: float
    standard_deviation_ratio: float
    relative_standard_deviation_error: float
    correlation: float
    volatility_match_within_tolerance: bool


@dataclass(frozen=True)
class OfficialFactorProfile:
    snapshot_id: str
    row_count: int
    column_count: int
    first_month: str
    last_month: str
    declared_frequency: str
    declared_return_unit: str
    missing_counts: dict[str, int]
    factor_pair_audits: tuple[FactorPairAudit, ...]
    all_factor_pairs_match_volatility_tolerance: bool
    raw_publication_authorized: bool
    empirical_verdict_issued: bool
    paper_replication_pass: bool
    economic_edge_verdict: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_month(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise ValueError(f"Invalid monthly date {value!r}") from exc
    if parsed.strftime("%Y-%m") != value:
        raise ValueError(f"Non-canonical monthly date {value!r}")
    return parsed


def _parse_number(value: str, *, column: str, row_number: int) -> float:
    if value == "":
        return float("nan")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"Non-numeric value in {column} at CSV row {row_number}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"Non-finite value in {column} at CSV row {row_number}")
    return parsed


def _validate_missingness(frame: pd.DataFrame) -> None:
    paired_columns = {column for pair in FACTOR_PAIRS.values() for column in pair}
    for column in EXPECTED_HEADER[1:]:
        if column not in paired_columns and frame[column].isna().any():
            raise ValueError(f"Unexpected missing values in {column}")

    for factor, (managed, unmanaged) in FACTOR_PAIRS.items():
        managed_missing = frame[managed].isna()
        unmanaged_missing = frame[unmanaged].isna()
        if not managed_missing.equals(unmanaged_missing):
            raise ValueError(f"Managed/unmanaged missingness mismatch for {factor}")
        missing_count = int(managed_missing.sum())
        if factor not in LATE_START_PAIRS and missing_count:
            raise ValueError(f"Unexpected missing history for {factor}")
        if factor in LATE_START_PAIRS:
            valid_positions = np.flatnonzero((~managed_missing).to_numpy())
            if valid_positions.size == 0:
                raise ValueError(f"No observations for {factor}")
            first_valid = int(valid_positions[0])
            if managed_missing.iloc[first_valid:].any():
                raise ValueError(f"Non-leading missing value for {factor}")
            if not managed_missing.iloc[:first_valid].all():
                raise ValueError(f"Late-start missing block is not contiguous for {factor}")


def parse_official_factor_bytes(
    raw: bytes,
    *,
    require_exact_snapshot: bool = True,
) -> pd.DataFrame:
    """Parse the official author CSV while preserving its declared percent unit."""

    if not raw:
        raise ValueError("Official factor file is empty")
    prefix = raw[:2000].lower()
    if b"<html" in prefix or b"<!doctype" in prefix:
        raise ValueError("Official factor endpoint returned HTML")
    if require_exact_snapshot:
        if len(raw) != EXPECTED_BYTE_COUNT:
            raise ValueError(f"Official factor byte count changed: {len(raw)}")
        digest = sha256_bytes(raw)
        if digest != EXPECTED_SHA256:
            raise ValueError(f"Official factor SHA-256 changed: {digest}")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Official factor file is not UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    header = tuple(reader.fieldnames or ())
    if header != EXPECTED_HEADER:
        raise ValueError(f"Unexpected official factor header: {header}")

    records = list(reader)
    if not records:
        raise ValueError("Official factor file has no data rows")
    if require_exact_snapshot and len(records) != EXPECTED_ROW_COUNT:
        raise ValueError(f"Official factor row count changed: {len(records)}")

    months: list[datetime] = []
    numeric: dict[str, list[float]] = {column: [] for column in EXPECTED_HEADER[1:]}
    for row_number, record in enumerate(records, start=2):
        if None in record:
            raise ValueError(f"Extra CSV field at row {row_number}")
        if any(record[column] is None for column in EXPECTED_HEADER):
            raise ValueError(f"Missing CSV field at row {row_number}")
        month_text = str(record["Date"]).strip()
        months.append(_parse_month(month_text))
        for column in EXPECTED_HEADER[1:]:
            cell = str(record[column]).strip()
            numeric[column].append(_parse_number(cell, column=column, row_number=row_number))

    if len(months) != len(set(months)):
        raise ValueError("Official factor file contains duplicate months")
    if months != sorted(months):
        raise ValueError("Official factor months are not sorted ascending")
    expected_months = list(pd.date_range(months[0], months[-1], freq="MS").to_pydatetime())
    if months != expected_months:
        raise ValueError("Official factor file has a monthly date gap")
    if require_exact_snapshot:
        if months[0].strftime("%Y-%m") != EXPECTED_FIRST_MONTH:
            raise ValueError("Official factor first month changed")
        if months[-1].strftime("%Y-%m") != EXPECTED_LAST_MONTH:
            raise ValueError("Official factor last month changed")

    frame = pd.DataFrame({"Date": pd.DatetimeIndex(months), **numeric})
    _validate_missingness(frame)
    if require_exact_snapshot:
        for factor in LATE_START_PAIRS:
            managed = FACTOR_PAIRS[factor][0]
            missing_count = int(frame[managed].isna().sum())
            if missing_count != EXPECTED_LATE_START_MISSING_COUNT:
                raise ValueError(f"Official {factor} missing-count changed: {missing_count}")
    frame.attrs.update(
        {
            "snapshot_id": SNAPSHOT_ID,
            "source_url": SOURCE_URL,
            "return_unit": "PERCENT",
            "frequency": "MONTHLY",
            "raw_sha256": sha256_bytes(raw),
            "raw_byte_count": len(raw),
        }
    )
    return frame


def validate_author_page(page: bytes) -> dict[str, str | int]:
    if not page:
        raise ValueError("Author data page is empty")
    text = page.decode("utf-8", errors="replace")
    missing = [phrase for phrase in REQUIRED_AUTHOR_PAGE_PHRASES if phrase not in text]
    if missing:
        raise ValueError(f"Author data-page description changed: {missing}")
    return {
        "url": AUTHOR_PAGE_URL,
        "byte_count": len(page),
        "sha256": sha256_bytes(page),
    }


def factor_pair_audits(frame: pd.DataFrame) -> tuple[FactorPairAudit, ...]:
    results: list[FactorPairAudit] = []
    for factor, (managed, unmanaged) in FACTOR_PAIRS.items():
        selected = frame[["Date", managed, unmanaged]].dropna()
        if len(selected) < 2:
            raise ValueError(f"Insufficient overlapping observations for {factor}")
        managed_std = float(selected[managed].std(ddof=1))
        unmanaged_std = float(selected[unmanaged].std(ddof=1))
        if not math.isfinite(managed_std) or managed_std <= 0:
            raise ValueError(f"Invalid managed volatility for {factor}")
        if not math.isfinite(unmanaged_std) or unmanaged_std <= 0:
            raise ValueError(f"Invalid unmanaged volatility for {factor}")
        ratio = managed_std / unmanaged_std
        relative_error = abs(ratio - 1.0)
        correlation = float(selected[managed].corr(selected[unmanaged]))
        if not math.isfinite(correlation):
            raise ValueError(f"Invalid managed/unmanaged correlation for {factor}")
        first_month = pd.Timestamp(selected["Date"].iloc[0]).strftime("%Y-%m")
        last_month = pd.Timestamp(selected["Date"].iloc[-1]).strftime("%Y-%m")
        results.append(
            FactorPairAudit(
                factor=factor,
                managed_column=managed,
                unmanaged_column=unmanaged,
                overlap_count=len(selected),
                first_overlap_month=first_month,
                last_overlap_month=last_month,
                managed_standard_deviation_percent=round(
                    managed_std, SAFE_METRIC_DECIMAL_PLACES
                ),
                unmanaged_standard_deviation_percent=round(
                    unmanaged_std, SAFE_METRIC_DECIMAL_PLACES
                ),
                standard_deviation_ratio=round(ratio, SAFE_METRIC_DECIMAL_PLACES),
                relative_standard_deviation_error=round(
                    relative_error, SAFE_METRIC_DECIMAL_PLACES
                ),
                correlation=round(correlation, SAFE_METRIC_DECIMAL_PLACES),
                volatility_match_within_tolerance=(
                    relative_error <= VOLATILITY_MATCH_RELATIVE_TOLERANCE
                ),
            )
        )
    return tuple(results)


def official_factor_profile(frame: pd.DataFrame) -> OfficialFactorProfile:
    audits = factor_pair_audits(frame)
    return OfficialFactorProfile(
        snapshot_id=str(frame.attrs.get("snapshot_id", SNAPSHOT_ID)),
        row_count=len(frame),
        column_count=len(frame.columns),
        first_month=pd.Timestamp(frame["Date"].iloc[0]).strftime("%Y-%m"),
        last_month=pd.Timestamp(frame["Date"].iloc[-1]).strftime("%Y-%m"),
        declared_frequency=str(frame.attrs.get("frequency", "MONTHLY")),
        declared_return_unit=str(frame.attrs.get("return_unit", "PERCENT")),
        missing_counts={
            column: int(frame[column].isna().sum()) for column in EXPECTED_HEADER[1:]
        },
        factor_pair_audits=audits,
        all_factor_pairs_match_volatility_tolerance=all(
            audit.volatility_match_within_tolerance for audit in audits
        ),
        raw_publication_authorized=False,
        empirical_verdict_issued=False,
        paper_replication_pass=False,
        economic_edge_verdict="INCONCLUSIVE",
    )


def write_safe_evidence(
    *,
    csv_path: str | Path,
    author_page_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    raw = Path(csv_path).read_bytes()
    page = Path(author_page_path).read_bytes()
    frame = parse_official_factor_bytes(raw)
    profile = official_factor_profile(frame)
    author_page = validate_author_page(page)
    evidence: dict[str, Any] = {
        "schema_version": "1.0",
        "evidence_id": "MOREIRA_MUIR_OFFICIAL_FACTOR_CONTRACT_AUDIT_V1",
        "snapshot_id": SNAPSHOT_ID,
        "source_url": SOURCE_URL,
        "source_byte_count": len(raw),
        "source_sha256": sha256_bytes(raw),
        "author_page": author_page,
        "expected_header": list(EXPECTED_HEADER),
        "factor_pairs": {key: list(value) for key, value in FACTOR_PAIRS.items()},
        "volatility_match_relative_tolerance": VOLATILITY_MATCH_RELATIVE_TOLERANCE,
        "profile": asdict(profile),
        "raw_uploaded": False,
        "row_level_data_uploaded": False,
        "annualized_performance_calculated": False,
        "sharpe_calculated": False,
        "alpha_calculated": False,
        "empirical_verdict_issued": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_bytes = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (output_root / "safe-factor-contract-evidence.json").write_bytes(evidence_bytes)
    summary = {
        "snapshot_id": SNAPSHOT_ID,
        "source_sha256": evidence["source_sha256"],
        "source_byte_count": evidence["source_byte_count"],
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "first_month": profile.first_month,
        "last_month": profile.last_month,
        "factor_pair_count": len(profile.factor_pair_audits),
        "all_factor_pairs_match_volatility_tolerance": (
            profile.all_factor_pairs_match_volatility_tolerance
        ),
        "safe_evidence_sha256": sha256_bytes(evidence_bytes),
        "raw_uploaded": False,
        "empirical_verdict_issued": False,
    }
    (output_root / "safe-factor-contract-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the frozen official Moreira-Muir factor-data snapshot."
    )
    parser.add_argument("--csv", required=True)
    parser.add_argument("--author-page", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evidence = write_safe_evidence(
        csv_path=args.csv,
        author_page_path=args.author_page,
        output_dir=args.output_dir,
    )
    summary = {
        "snapshot_id": evidence["snapshot_id"],
        "source_sha256": evidence["source_sha256"],
        "profile": evidence["profile"],
        "empirical_verdict_issued": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
