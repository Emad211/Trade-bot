"""Fail-closed ingestion of the official 2022 CFTC TFF futures-only ZIP."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import tempfile
import zipfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.request import Request, urlopen

SOURCE_ID = "CFTC_TFF_FUTURES_ONLY_HISTORICAL_TEXT_2022"
REPORT_FAMILY = "TFF_FUTURES_ONLY"
YEAR = 2022
OFFICIAL_URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_2022.zip"
RAW_FILENAME = "fut_fin_txt_2022.zip"
DEFAULT_USER_AGENT = (
    "Emad211-Trade-bot-replication/1.0 (+https://github.com/Emad211/Trade-bot)"
)
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


class CFTCHistoricalError(RuntimeError):
    """Raised when the official annual archive cannot be trusted."""


@dataclass(frozen=True)
class HTTPZipArtifact:
    raw_bytes: bytes
    status_code: int
    content_type: str
    etag: str | None
    last_modified: str | None


@dataclass(frozen=True)
class ZipMemberEvidence:
    name: str
    compressed_size: int
    uncompressed_size: int
    crc32: str
    sha256: str


@dataclass(frozen=True)
class ZipValidation:
    source_id: str
    report_family: str
    year: int
    member_count: int
    text_member_count: int
    total_compressed_size: int
    total_uncompressed_size: int
    members: tuple[ZipMemberEvidence, ...]


def fetch_official_zip(
    *,
    url: str = OFFICIAL_URL,
    timeout_seconds: float = 90.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> HTTPZipArtifact:
    """Download unmodified bytes from the official CFTC historical-file host."""

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request = Request(url, headers={"Accept": "application/zip", "User-Agent": user_agent})
    with urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read()
        status = int(response.status)
        content_type = response.headers.get("Content-Type", "")
        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")
    if status != 200:
        raise CFTCHistoricalError(f"Official archive returned HTTP {status}")
    if not raw:
        raise CFTCHistoricalError("Official archive returned an empty body")
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise CFTCHistoricalError("Official archive exceeded the acquisition size ceiling")
    if not raw.startswith(b"PK"):
        raise CFTCHistoricalError("Downloaded bytes do not have a ZIP signature")
    return HTTPZipArtifact(raw, status, content_type, etag, last_modified)


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts and bool(path.name)


def validate_zip(raw_bytes: bytes) -> ZipValidation:
    """Validate ZIP integrity, safe names, size ceilings, and member hashes."""

    if not raw_bytes.startswith(b"PK"):
        raise CFTCHistoricalError("Archive lacks a ZIP signature")
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw_bytes))
    except zipfile.BadZipFile as exc:
        raise CFTCHistoricalError("Archive is not a valid ZIP file") from exc

    with archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise CFTCHistoricalError(f"ZIP CRC validation failed for {bad_member!r}")
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if not infos:
            raise CFTCHistoricalError("Archive contains no files")
        if any(not _safe_member_name(info.filename) for info in infos):
            raise CFTCHistoricalError("Archive contains an unsafe member path")
        if any(info.flag_bits & 0x1 for info in infos):
            raise CFTCHistoricalError("Archive contains an encrypted member")

        total_compressed = sum(info.compress_size for info in infos)
        total_uncompressed = sum(info.file_size for info in infos)
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise CFTCHistoricalError("Archive exceeds the uncompressed-size ceiling")

        evidence: list[ZipMemberEvidence] = []
        text_member_count = 0
        for info in infos:
            member_bytes = archive.read(info.filename)
            suffix = Path(info.filename).suffix.lower()
            if suffix in {".txt", ".csv"}:
                text_member_count += 1
            evidence.append(
                ZipMemberEvidence(
                    name=info.filename,
                    compressed_size=info.compress_size,
                    uncompressed_size=info.file_size,
                    crc32=f"{info.CRC:08x}",
                    sha256=hashlib.sha256(member_bytes).hexdigest(),
                )
            )
        if text_member_count == 0:
            raise CFTCHistoricalError("Archive contains no text or CSV member")

    return ZipValidation(
        source_id=SOURCE_ID,
        report_family=REPORT_FAMILY,
        year=YEAR,
        member_count=len(evidence),
        text_member_count=text_member_count,
        total_compressed_size=total_compressed,
        total_uncompressed_size=total_uncompressed,
        members=tuple(evidence),
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


def write_historical_bundle(
    output_dir: Path,
    *,
    artifact: HTTPZipArtifact,
    validation: ZipValidation,
    retrieved_at: datetime,
    source_url: str = OFFICIAL_URL,
) -> dict[str, Any]:
    """Persist the raw official ZIP and a non-promotional evidence manifest."""

    if retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / RAW_FILENAME
    inventory_path = output_dir / "zip-inventory.json"
    manifest_path = output_dir / "acquisition-manifest.json"
    _atomic_write(raw_path, artifact.raw_bytes)

    validation_payload = asdict(validation)
    _atomic_write(
        inventory_path,
        (json.dumps(validation_payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "source_id": SOURCE_ID,
        "report_family": REPORT_FAMILY,
        "year": YEAR,
        "official_source_url": source_url,
        "retrieved_at": retrieved_at.astimezone(UTC).isoformat(),
        "http_status": artifact.status_code,
        "content_type": artifact.content_type,
        "etag": artifact.etag,
        "last_modified": artifact.last_modified,
        "raw_filename": RAW_FILENAME,
        "raw_byte_count": len(artifact.raw_bytes),
        "raw_sha256": hashlib.sha256(artifact.raw_bytes).hexdigest(),
        "zip_validation": validation_payload,
        "source_access_state": "RAW_OFFICIAL_HISTORICAL_ZIP_ACQUIRED_NOT_YET_ACTIONS_STAGED",
        "artifact_audit_pass": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }
    _atomic_write(
        manifest_path,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return manifest


def ingest_historical_zip(output_dir: Path) -> dict[str, Any]:
    """Download, validate, and persist the official annual TFF archive."""

    retrieved_at = datetime.now(UTC)
    artifact = fetch_official_zip()
    validation = validate_zip(artifact.raw_bytes)
    return write_historical_bundle(
        output_dir,
        artifact=artifact,
        validation=validation,
        retrieved_at=retrieved_at,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = ingest_historical_zip(args.output_dir)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
