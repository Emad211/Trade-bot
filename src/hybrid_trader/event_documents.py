"""Prospective-only document contracts for semantic event research."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


class FeedSourceSpec(BaseModel):
    """Predeclared public feed and trust metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$")
    feed_url: str
    allowed_domains: tuple[str, ...]
    source_quality: float = Field(ge=0, le=1)
    asset_tags: tuple[str, ...] = ()
    required: bool = False
    max_items: int = Field(default=100, ge=1, le=1000)
    maximum_payload_bytes: int = Field(default=5_000_000, ge=1_024, le=50_000_000)
    maximum_clock_skew_seconds: int = Field(default=900, ge=0, le=86_400)

    @field_validator("feed_url")
    @classmethod
    def validate_feed_url(cls, value: str) -> str:
        normalized = canonicalize_url(value)
        if not normalized.startswith("https://"):
            raise ValueError("Feed URLs must use HTTPS")
        return normalized

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(domain.lower().strip(".") for domain in value)
        if not normalized or any(not domain or "/" in domain for domain in normalized):
            raise ValueError("allowed_domains must contain valid host names")
        if len(set(normalized)) != len(normalized):
            raise ValueError("allowed_domains cannot contain duplicates")
        return normalized

    @field_validator("asset_tags")
    @classmethod
    def validate_asset_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(tag.upper().strip() for tag in value)
        if any(not tag for tag in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("asset_tags must be unique non-empty values")
        return normalized


class ProspectiveDocument(BaseModel):
    """Metadata stored in Git; full feed text remains an external artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    document_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$")
    canonical_url: str
    title: str = Field(min_length=1, max_length=500)
    published_at: datetime | None = None
    retrieved_at: datetime
    available_at: datetime
    source_quality: float = Field(ge=0, le=1)
    asset_tags: tuple[str, ...] = ()
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_length: int = Field(ge=0)
    feed_payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_record_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("published_at", "retrieved_at", "available_at")
    @classmethod
    def normalize_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Event timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_prospective_contract(self) -> ProspectiveDocument:
        if self.available_at != self.retrieved_at:
            raise ValueError("Raw feed documents become available at retrieval time")
        if len(set(self.asset_tags)) != len(self.asset_tags):
            raise ValueError("asset_tags cannot contain duplicates")
        if canonicalize_url(self.canonical_url) != self.canonical_url:
            raise ValueError("canonical_url is not canonical")
        return self


class DocumentEnvelope(BaseModel):
    """In-memory text plus the compact prospective metadata record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document: ProspectiveDocument
    text: str

    @model_validator(mode="after")
    def validate_text_identity(self) -> DocumentEnvelope:
        encoded = self.text.encode("utf-8")
        if len(encoded) != self.document.content_length:
            raise ValueError("Document text length does not match metadata")
        if hashlib.sha256(encoded).hexdigest() != self.document.content_sha256:
            raise ValueError("Document text hash does not match metadata")
        return self


def canonicalize_url(value: str) -> str:
    """Normalize an HTTP(S) URL and remove common tracking parameters."""

    parts = urlsplit(value.strip())
    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower().strip(".")
    if scheme not in {"http", "https"} or not hostname:
        raise ValueError("URL must be absolute HTTP(S)")
    port = parts.port
    default_port = (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    netloc = hostname if port is None or default_port else f"{hostname}:{port}"
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query_pairs = [
        (key, item)
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_QUERY_KEYS
    ]
    query = urlencode(sorted(query_pairs))
    return urlunsplit((scheme, netloc, path, query, ""))


def url_is_allowed(url: str, allowed_domains: tuple[str, ...]) -> bool:
    hostname = (urlsplit(url).hostname or "").lower().strip(".")
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains)


def document_identity_payload(
    *,
    source_id: str,
    canonical_url: str,
    title: str,
    published_at: datetime | None,
    content_sha256: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "canonical_url": canonical_url,
        "title": title,
        "published_at": published_at.astimezone(UTC).isoformat() if published_at else None,
        "content_sha256": content_sha256,
    }


def make_document_id(**payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()
