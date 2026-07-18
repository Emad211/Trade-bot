"""Immutable artifact hashing and tabular source loading."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_column_name(value: Any) -> str:
    text = str(value).strip().lower()
    chars = [char if char.isalnum() else "_" for char in text]
    normalized = "".join(chars)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _detect_header_row(raw: pd.DataFrame, *, max_rows: int = 40) -> int:
    for index in range(min(max_rows, len(raw))):
        values = [normalize_column_name(value) for value in raw.iloc[index].tolist()]
        if any(value in {"date", "month", "yyyymm", "year_month"} for value in values):
            if sum(bool(value) for value in values) >= 2:
                return index
    raise ValueError("Could not detect a date-bearing header row")


def load_tabular_artifact(path: str | Path, *, sheet_name: str | int | None = None) -> pd.DataFrame:
    """Load CSV or Excel while preserving source semantics.

    Excel workbooks often contain title and terms-of-use rows before the table.
    A date-bearing header is required; silent guessing is prohibited.
    """

    source = Path(path)
    suffix = source.suffix.lower()
    if suffix in {".csv", ".txt"}:
        frame = pd.read_csv(source)
    elif suffix in {".xlsx", ".xlsm", ".xls"}:
        chosen_sheet: str | int = 0 if sheet_name is None else sheet_name
        raw = pd.read_excel(source, sheet_name=chosen_sheet, header=None)
        header_row = _detect_header_row(raw)
        headers = [normalize_column_name(value) for value in raw.iloc[header_row].tolist()]
        frame = raw.iloc[header_row + 1 :].copy()
        frame.columns = headers
    else:
        raise ValueError(f"Unsupported artifact format: {suffix}")

    frame.columns = [normalize_column_name(column) for column in frame.columns]
    frame = frame.dropna(how="all").reset_index(drop=True)
    return frame


def parse_month_column(values: pd.Series) -> pd.Series:
    """Parse common monthly date encodings to month-end UTC timestamps."""

    text = values.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns, UTC]")
    yyyymm = text.str.fullmatch(r"\d{6}")
    if yyyymm.any():
        parsed.loc[yyyymm] = pd.to_datetime(
            text.loc[yyyymm], format="%Y%m", errors="coerce", utc=True
        )
    if (~yyyymm).any():
        parsed.loc[~yyyymm] = pd.to_datetime(
            text.loc[~yyyymm], format="mixed", errors="coerce", utc=True
        )
    if parsed.isna().any():
        examples = text.loc[parsed.isna()].head(5).tolist()
        raise ValueError(f"Unparseable date values: {examples}")
    return parsed.dt.tz_convert(None).dt.to_period("M").dt.to_timestamp("M").dt.tz_localize("UTC")
