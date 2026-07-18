from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hybrid_trader.replication.cftc_historical_ingestion import (
    CFTCHistoricalError,
    HTTPZipArtifact,
    validate_zip,
    write_historical_bundle,
)


def _zip_bytes(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_validate_zip_records_member_hashes() -> None:
    raw = _zip_bytes({"F_TFF_2022.txt": b"header\nrow\n"})
    result = validate_zip(raw)
    assert result.member_count == 1
    assert result.text_member_count == 1
    assert result.members[0].name == "F_TFF_2022.txt"
    assert result.members[0].sha256 == hashlib.sha256(b"header\nrow\n").hexdigest()


def test_validate_zip_rejects_path_traversal() -> None:
    raw = _zip_bytes({"../escape.txt": b"bad"})
    with pytest.raises(CFTCHistoricalError, match="unsafe member path"):
        validate_zip(raw)


def test_validate_zip_rejects_non_zip_and_no_text_member() -> None:
    with pytest.raises(CFTCHistoricalError, match="ZIP signature"):
        validate_zip(b"not-a-zip")

    raw = _zip_bytes({"payload.bin": b"binary"})
    with pytest.raises(CFTCHistoricalError, match="no text or CSV"):
        validate_zip(raw)


def test_bundle_preserves_zip_and_records_non_promotional_state(tmp_path: Path) -> None:
    raw = _zip_bytes({"F_TFF_2022.txt": b"header\nrow\n"})
    validation = validate_zip(raw)
    artifact = HTTPZipArtifact(raw, 200, "application/zip", '"etag"', None)
    manifest = write_historical_bundle(
        tmp_path,
        artifact=artifact,
        validation=validation,
        retrieved_at=datetime(2026, 7, 18, tzinfo=UTC),
    )
    stored = (tmp_path / "fut_fin_txt_2022.zip").read_bytes()
    inventory = json.loads((tmp_path / "zip-inventory.json").read_text(encoding="utf-8"))
    assert stored == raw
    assert manifest["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["raw_byte_count"] == len(raw)
    assert inventory["member_count"] == 1
    assert manifest["artifact_audit_pass"] is False
    assert manifest["paper_replication_pass"] is False
    assert manifest["economic_edge_verdict"] == "INCONCLUSIVE"
