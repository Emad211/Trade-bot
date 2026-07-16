"""Filesystem safety helpers for prospective event capture state."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any

from hybrid_trader.event_capture_models import EventCaptureManifest
from hybrid_trader.event_documents import DocumentEnvelope


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


class CaptureLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._descriptor: int | None = None

    def __enter__(self) -> CaptureLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise RuntimeError(f"Another event capture holds the lock: {self.path}") from exc
        payload = json.dumps(
            {"pid": os.getpid(), "created_at": datetime.now(UTC).isoformat()},
            sort_keys=True,
        ).encode("utf-8")
        os.write(descriptor, payload)
        os.fsync(descriptor)
        self._descriptor = descriptor
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback
        if self._descriptor is not None:
            os.close(self._descriptor)
            self._descriptor = None
        self.path.unlink(missing_ok=True)


def ensure_empty_decision_ledger(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8").strip():
            raise RuntimeError("Prospective decision ledger is not empty")
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def duplicate_content_count(envelopes: list[DocumentEnvelope]) -> int:
    sources_by_hash: dict[str, set[str]] = {}
    counts = Counter(envelope.document.content_sha256 for envelope in envelopes)
    for envelope in envelopes:
        sources_by_hash.setdefault(envelope.document.content_sha256, set()).add(
            envelope.document.source_id
        )
    return sum(
        counts[content_hash] - 1
        for content_hash, sources in sources_by_hash.items()
        if len(sources) > 1
    )


def finalize_capture_files(
    *,
    state_root: Path,
    raw_root: Path,
    raw_staging: Path,
    manifest: EventCaptureManifest,
) -> Path:
    capture_dir = state_root / "captures" / manifest.capture_id
    raw_capture_dir = raw_root / manifest.capture_id
    if capture_dir.exists() or raw_capture_dir.exists():
        raise FileExistsError(f"Capture identity already exists: {manifest.capture_id}")
    capture_dir.mkdir(parents=True)
    raw_capture_dir.parent.mkdir(parents=True, exist_ok=True)
    raw_staging.rename(raw_capture_dir)

    write_json(
        capture_dir / "source_attempts.json",
        [attempt.model_dump(mode="json") for attempt in manifest.source_attempts],
    )
    write_json(
        capture_dir / "raw_payloads.json",
        [record.model_dump(mode="json") for record in manifest.raw_payloads],
    )
    write_json(capture_dir / "capture_manifest.json", manifest.model_dump(mode="json"))
    checksum_paths = [
        capture_dir / "capture_manifest.json",
        capture_dir / "raw_payloads.json",
        capture_dir / "source_attempts.json",
    ]
    checksum_lines = [f"{sha256_file(path)}  {path.name}" for path in sorted(checksum_paths)]
    (capture_dir / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return capture_dir / "capture_manifest.json"
