"""Canonical identities for prospective event documents."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime


def document_identity_payload(
    *,
    source_id: str,
    canonical_url: str,
    title: str,
    published_at: datetime | None,
    content_sha256: str,
) -> dict[str, str | None]:
    return {
        "source_id": source_id,
        "canonical_url": canonical_url,
        "title": title,
        "published_at": published_at.astimezone(UTC).isoformat() if published_at else None,
        "content_sha256": content_sha256,
    }


def make_document_id(payload: dict[str, str | None]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
