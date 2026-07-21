"""Safe metadata profiling for bounded OKX historical funding archives."""

from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import PurePosixPath
from typing import Any

MAX_ARCHIVE_BYTES = 10_000_000
MAX_MEMBER_BYTES = 25_000_000
TIMESTAMP_FIELD_CANDIDATES = (
    "fundingTime",
    "funding_time",
    "timestamp",
    "ts",
    "time",
    "date",
)


class OKXHistoricalExportError(RuntimeError):
    """Raised when an OKX historical export violates the bounded audit contract."""


@dataclass(frozen=True)
class FundingArchiveMemberProfile:
    filename: str
    compressed_size: int
    uncompressed_size: int
    crc32_hex: str
    member_sha256: str
    field_count: int
    fieldnames: tuple[str, ...]
    schema_sha256: str
    row_count: int
    timestamp_field: str
    first_timestamp_utc: str
    last_timestamp_utc: str
    minimum_timestamp_utc: str
    maximum_timestamp_utc: str
    timestamp_order: str
    unique_timestamp_count: int
    duplicate_timestamp_count: int


@dataclass(frozen=True)
class FundingArchiveProfile:
    archive_byte_count: int
    archive_sha256: str
    member_count: int
    member: FundingArchiveMemberProfile
    raw_rows_retained: bool
    ordered_timestamp_series_retained: bool
    funding_rate_values_retained: bool

    def to_safe_dict(self) -> dict[str, Any]:
        """Return a JSON-safe profile that contains no funding-rate observations."""

        return asdict(self)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def schema_fingerprint(fieldnames: tuple[str, ...]) -> str:
    """Fingerprint exact CSV field names and order with an unambiguous delimiter."""

    if not fieldnames:
        raise OKXHistoricalExportError("Funding archive schema cannot be empty")
    return sha256_bytes("\x00".join(fieldnames).encode("utf-8"))


def _safe_member_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or not path.name:
        raise OKXHistoricalExportError(f"Unsafe ZIP member path: {name!r}")
    return normalized


def _timestamp_field(fieldnames: tuple[str, ...]) -> str:
    exact = set(fieldnames)
    for candidate in TIMESTAMP_FIELD_CANDIDATES:
        if candidate in exact:
            return candidate
    lower_map = {field.lower(): field for field in fieldnames}
    for candidate in TIMESTAMP_FIELD_CANDIDATES:
        resolved = lower_map.get(candidate.lower())
        if resolved is not None:
            return resolved
    raise OKXHistoricalExportError(
        "Funding archive lacks a recognized timestamp field: "
        f"{list(fieldnames)!r}"
    )


def _parse_timestamp(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        raise OKXHistoricalExportError("Funding timestamp cannot be empty")
    try:
        numeric = int(raw)
    except ValueError:
        normalized = raw.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise OKXHistoricalExportError(
                f"Invalid funding timestamp: {value!r}"
            ) from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    magnitude = abs(numeric)
    if magnitude >= 10**17:
        seconds = numeric / 1_000_000_000
    elif magnitude >= 10**14:
        seconds = numeric / 1_000_000
    elif magnitude >= 10**11:
        seconds = numeric / 1_000
    else:
        seconds = float(numeric)
    try:
        return datetime.fromtimestamp(seconds, tz=UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise OKXHistoricalExportError(
            f"Funding timestamp is outside the supported range: {value!r}"
        ) from exc


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _timestamp_order(values: list[datetime]) -> str:
    if len(values) < 2:
        return "single"
    pairs = list(pairwise(values))
    ascending = all(left <= right for left, right in pairs)
    descending = all(left >= right for left, right in pairs)
    if ascending and descending:
        return "constant"
    if ascending:
        return "ascending"
    if descending:
        return "descending"
    return "unsorted"


def inspect_funding_archive_bytes(
    archive_bytes: bytes,
    *,
    max_archive_bytes: int = MAX_ARCHIVE_BYTES,
    max_member_bytes: int = MAX_MEMBER_BYTES,
) -> FundingArchiveProfile:
    """Inspect one funding ZIP and retain only non-rate metadata.

    The function reads funding-rate values only as opaque CSV fields. It never stores,
    returns, aggregates, or serializes those values. Only archive identity, schema,
    row counts, and timestamp bounds are returned.
    """

    if not archive_bytes:
        raise OKXHistoricalExportError("Funding archive cannot be empty")
    if len(archive_bytes) > max_archive_bytes:
        raise OKXHistoricalExportError(
            f"Funding archive exceeds the {max_archive_bytes}-byte guard"
        )
    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except zipfile.BadZipFile as exc:
        raise OKXHistoricalExportError("Funding archive is not a valid ZIP") from exc

    with archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise OKXHistoricalExportError(f"ZIP CRC failed for {bad_member!r}")
        members = [info for info in archive.infolist() if not info.is_dir()]
        if len(members) != 1:
            raise OKXHistoricalExportError(
                f"Expected exactly one funding CSV member, found {len(members)}"
            )
        info = members[0]
        filename = _safe_member_name(info.filename)
        if not filename.lower().endswith(".csv"):
            raise OKXHistoricalExportError(
                f"Funding archive member is not a CSV: {filename!r}"
            )
        if info.file_size <= 0 or info.file_size > max_member_bytes:
            raise OKXHistoricalExportError(
                f"Funding CSV size violates the bounded contract: {info.file_size}"
            )
        member_bytes = archive.read(info)

    try:
        text = member_bytes.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise OKXHistoricalExportError("Funding CSV is not valid UTF-8") from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None:
        raise OKXHistoricalExportError("Funding CSV has no header")
    fieldnames = tuple(str(field) for field in reader.fieldnames)
    if len(fieldnames) != len(set(fieldnames)):
        raise OKXHistoricalExportError("Funding CSV contains duplicate field names")
    timestamp_field = _timestamp_field(fieldnames)

    timestamps: list[datetime] = []
    row_count = 0
    for row_number, raw_row in enumerate(reader, start=2):
        if None in raw_row:
            raise OKXHistoricalExportError(
                f"Row {row_number}: unexpected extra CSV fields"
            )
        if any(value is None for value in raw_row.values()):
            raise OKXHistoricalExportError(
                f"Row {row_number}: missing trailing CSV fields"
            )
        timestamp_value = raw_row.get(timestamp_field)
        if timestamp_value is None:
            raise OKXHistoricalExportError(
                f"Row {row_number}: missing {timestamp_field!r}"
            )
        timestamps.append(_parse_timestamp(timestamp_value))
        row_count += 1

    if row_count == 0:
        raise OKXHistoricalExportError("Funding CSV contains no data rows")
    unique_timestamp_count = len(set(timestamps))
    duplicate_timestamp_count = row_count - unique_timestamp_count
    profile = FundingArchiveMemberProfile(
        filename=filename,
        compressed_size=info.compress_size,
        uncompressed_size=info.file_size,
        crc32_hex=f"{info.CRC:08x}",
        member_sha256=sha256_bytes(member_bytes),
        field_count=len(fieldnames),
        fieldnames=fieldnames,
        schema_sha256=schema_fingerprint(fieldnames),
        row_count=row_count,
        timestamp_field=timestamp_field,
        first_timestamp_utc=_iso_utc(timestamps[0]),
        last_timestamp_utc=_iso_utc(timestamps[-1]),
        minimum_timestamp_utc=_iso_utc(min(timestamps)),
        maximum_timestamp_utc=_iso_utc(max(timestamps)),
        timestamp_order=_timestamp_order(timestamps),
        unique_timestamp_count=unique_timestamp_count,
        duplicate_timestamp_count=duplicate_timestamp_count,
    )
    return FundingArchiveProfile(
        archive_byte_count=len(archive_bytes),
        archive_sha256=sha256_bytes(archive_bytes),
        member_count=1,
        member=profile,
        raw_rows_retained=False,
        ordered_timestamp_series_retained=False,
        funding_rate_values_retained=False,
    )
