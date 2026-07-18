"""Immutable pilot ingestion for the official CFTC TFF futures-only dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET_ID = "gpe5-46if"
RESOURCE_URL = f"https://publicreporting.cftc.gov/resource/{DATASET_ID}.json"
DEFAULT_REPORT_DATE = date(2022, 9, 13)
DEFAULT_LIMIT = 5000
DEFAULT_USER_AGENT = (
    "Emad211-Trade-bot-replication/1.0 (+https://github.com/Emad211/Trade-bot)"
)
RAW_FILENAME = "tff_futures_only_2022-09-13.raw.json"
CANONICAL_FILENAME = "tff_futures_only_2022-09-13.canonical.json"

SELECT_FIELDS = (
    "id",
    "market_and_exchange_names",
    "report_date_as_yyyy_mm_dd",
    "cftc_contract_market_code",
    "commodity_name",
    "open_interest_all",
    "tot_rept_positions_long_all",
    "tot_rept_positions_short",
    "nonrept_positions_long_all",
    "nonrept_positions_short_all",
    "futonly_or_combined",
)
REQUIRED_FIELDS = frozenset(SELECT_FIELDS)


class CFTCPilotError(RuntimeError):
    """Raised when official pilot acquisition or validation fails."""


@dataclass(frozen=True)
class HTTPArtifact:
    raw_bytes: bytes
    status_code: int
    content_type: str
    etag: str | None
    last_modified: str | None


@dataclass(frozen=True)
class PilotValidation:
    dataset_id: str
    report_date: str
    row_count: int
    unique_id_count: int
    column_count: int
    min_id: str
    max_id: str
    accounting_identity_rows_checked: int
    raw_order_inversion_count: int
    canonical_sort_key: str


def build_query_url(*, report_date: date = DEFAULT_REPORT_DATE, limit: int = DEFAULT_LIMIT) -> str:
    """Build a narrow official Socrata query for one frozen report date."""

    if limit <= 0 or limit > 50_000:
        raise ValueError("limit must be between 1 and 50000")
    timestamp = f"{report_date.isoformat()}T00:00:00.000"
    params = {
        "$select": ",".join(SELECT_FIELDS),
        "report_date_as_yyyy_mm_dd": timestamp,
        "$limit": str(limit),
    }
    return f"{RESOURCE_URL}?{urlencode(params)}"


def fetch_official_bytes(
    url: str,
    *,
    timeout_seconds: float = 60.0,
    user_agent: str = DEFAULT_USER_AGENT,
    app_token: str | None = None,
) -> HTTPArtifact:
    """Fetch unmodified response bytes from the official CFTC endpoint."""

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    headers = {"Accept": "application/json", "User-Agent": user_agent}
    if app_token:
        headers["X-App-Token"] = app_token
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read()
        status = int(response.status)
        content_type = response.headers.get("Content-Type", "")
        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")
    if status != 200:
        raise CFTCPilotError(f"Official endpoint returned HTTP {status}")
    if not raw:
        raise CFTCPilotError("Official endpoint returned an empty body")
    if "json" not in content_type.lower():
        raise CFTCPilotError(f"Unexpected content type: {content_type!r}")
    return HTTPArtifact(raw, status, content_type, etag, last_modified)


def _decode_rows(raw_bytes: bytes) -> list[Mapping[str, Any]]:
    try:
        decoded = json.loads(raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CFTCPilotError("Response is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, list) or not decoded:
        raise CFTCPilotError("Expected a non-empty JSON array")

    rows: list[Mapping[str, Any]] = []
    for index, value in enumerate(decoded):
        if not isinstance(value, dict):
            raise CFTCPilotError(f"Row {index} is not a JSON object")
        rows.append(cast(Mapping[str, Any], value))
    return rows


def _as_int(row: Mapping[str, Any], field: str) -> int:
    value = row.get(field)
    if value is None or value == "":
        raise CFTCPilotError(f"Missing numeric field {field!r}")
    try:
        result = int(str(value))
    except ValueError as exc:
        raise CFTCPilotError(f"Invalid integer in {field!r}: {value!r}") from exc
    if result < 0:
        raise CFTCPilotError(f"Negative value in {field!r}: {result}")
    return result


def canonicalize_rows(raw_bytes: bytes) -> bytes:
    """Create a stable, derived JSON representation sorted by the business row ID."""

    rows = _decode_rows(raw_bytes)
    canonical_rows = sorted(rows, key=lambda row: str(row.get("id", "")))
    return (
        json.dumps(canonical_rows, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def parse_and_validate(raw_bytes: bytes, *, report_date: date = DEFAULT_REPORT_DATE) -> PilotValidation:
    """Parse and fail closed on identity, date, schema, and accounting defects."""

    rows = _decode_rows(raw_bytes)
    expected_timestamp = f"{report_date.isoformat()}T00:00:00.000"
    ids: list[str] = []
    all_columns: set[str] = set()
    accounting_checked = 0

    for index, row in enumerate(rows):
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise CFTCPilotError(f"Row {index} lacks required fields: {sorted(missing)}")
        identifier = str(row["id"])
        if not identifier:
            raise CFTCPilotError(f"Row {index} has an empty id")
        ids.append(identifier)
        all_columns.update(str(key) for key in row)

        if row["report_date_as_yyyy_mm_dd"] != expected_timestamp:
            raise CFTCPilotError(
                f"Row {identifier} has unexpected report date "
                f"{row['report_date_as_yyyy_mm_dd']!r}"
            )
        if row["futonly_or_combined"] != "FutOnly":
            raise CFTCPilotError(f"Row {identifier} is not Futures Only")

        open_interest = _as_int(row, "open_interest_all")
        reported_long = _as_int(row, "tot_rept_positions_long_all")
        nonreported_long = _as_int(row, "nonrept_positions_long_all")
        reported_short = _as_int(row, "tot_rept_positions_short")
        nonreported_short = _as_int(row, "nonrept_positions_short_all")
        if reported_long + nonreported_long != open_interest:
            raise CFTCPilotError(f"Long-side accounting identity failed for {identifier}")
        if reported_short + nonreported_short != open_interest:
            raise CFTCPilotError(f"Short-side accounting identity failed for {identifier}")
        accounting_checked += 1

    if len(ids) != len(set(ids)):
        raise CFTCPilotError("Duplicate CFTC row ids detected")
    inversion_count = sum(1 for left, right in pairwise(ids) if left > right)

    return PilotValidation(
        dataset_id=DATASET_ID,
        report_date=report_date.isoformat(),
        row_count=len(rows),
        unique_id_count=len(set(ids)),
        column_count=len(all_columns),
        min_id=min(ids),
        max_id=max(ids),
        accounting_identity_rows_checked=accounting_checked,
        raw_order_inversion_count=inversion_count,
        canonical_sort_key="id",
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


def _artifact_evidence(
    *, artifact: HTTPArtifact, source_url: str, retrieved_at: datetime
) -> dict[str, Any]:
    return {
        "source_id": "CFTC_TFF_FUTURES_ONLY",
        "dataset_id": DATASET_ID,
        "official_source_url": source_url,
        "retrieved_at": retrieved_at.astimezone(UTC).isoformat(),
        "http_status": artifact.status_code,
        "content_type": artifact.content_type,
        "etag": artifact.etag,
        "last_modified": artifact.last_modified,
        "raw_filename": RAW_FILENAME,
        "raw_byte_count": len(artifact.raw_bytes),
        "raw_sha256": hashlib.sha256(artifact.raw_bytes).hexdigest(),
    }


def write_validation_failure_bundle(
    output_dir: Path,
    *,
    artifact: HTTPArtifact,
    source_url: str,
    retrieved_at: datetime,
    error: CFTCPilotError,
) -> dict[str, Any]:
    """Quarantine downloaded official bytes when validation rejects them."""

    if retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(output_dir / RAW_FILENAME, artifact.raw_bytes)
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        **_artifact_evidence(
            artifact=artifact,
            source_url=source_url,
            retrieved_at=retrieved_at,
        ),
        "validation_status": "FAILED_QUARANTINED",
        "validation_error_type": type(error).__name__,
        "validation_error": str(error),
        "source_access_state": "RAW_ARTIFACT_ACQUIRED_VALIDATION_FAILED_QUARANTINED",
        "artifact_audit_pass": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    _atomic_write(
        output_dir / "validation-failure-manifest.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return manifest


def write_pilot_bundle(
    output_dir: Path,
    *,
    artifact: HTTPArtifact,
    validation: PilotValidation,
    source_url: str,
    retrieved_at: datetime,
) -> dict[str, Any]:
    """Persist raw and canonical bytes plus a non-promotional validation manifest."""

    if retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / RAW_FILENAME
    canonical_path = output_dir / CANONICAL_FILENAME
    validation_path = output_dir / "validation.json"
    manifest_path = output_dir / "acquisition-manifest.json"
    canonical_bytes = canonicalize_rows(artifact.raw_bytes)
    _atomic_write(raw_path, artifact.raw_bytes)
    _atomic_write(canonical_path, canonical_bytes)

    validation_payload = asdict(validation)
    _atomic_write(
        validation_path,
        (json.dumps(validation_payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    manifest: dict[str, Any] = {
        "schema_version": "1.1",
        **_artifact_evidence(
            artifact=artifact,
            source_url=source_url,
            retrieved_at=retrieved_at,
        ),
        "canonical_filename": CANONICAL_FILENAME,
        "canonical_byte_count": len(canonical_bytes),
        "canonical_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "validation": validation_payload,
        "validation_status": "PASS",
        "source_access_state": "RAW_ARTIFACT_ACQUIRED_NOT_YET_ACTIONS_STAGED",
        "artifact_audit_pass": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    _atomic_write(
        manifest_path,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return manifest


def ingest_pilot(
    output_dir: Path,
    *,
    report_date: date = DEFAULT_REPORT_DATE,
    app_token: str | None = None,
) -> dict[str, Any]:
    """Download, validate, and persist the frozen official pilot response."""

    source_url = build_query_url(report_date=report_date)
    retrieved_at = datetime.now(UTC)
    artifact = fetch_official_bytes(source_url, app_token=app_token)
    try:
        validation = parse_and_validate(artifact.raw_bytes, report_date=report_date)
    except CFTCPilotError as exc:
        write_validation_failure_bundle(
            output_dir,
            artifact=artifact,
            source_url=source_url,
            retrieved_at=retrieved_at,
            error=exc,
        )
        raise
    return write_pilot_bundle(
        output_dir,
        artifact=artifact,
        validation=validation,
        source_url=source_url,
        retrieved_at=retrieved_at,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report-date", type=date.fromisoformat, default=DEFAULT_REPORT_DATE)
    args = parser.parse_args(argv)
    app_token = os.getenv("CFTC_APP_TOKEN")
    manifest = ingest_pilot(args.output_dir, report_date=args.report_date, app_token=app_token)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
