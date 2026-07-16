"""Validated metadata and transient text for prospective event documents."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_identity import document_identity_payload, make_document_id
from hybrid_trader.event_url import canonicalize_url


class ProspectiveDocument(BaseModel):
    """Metadata stored in Git; full feed text remains an external artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.1"
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
    content_length: int = Field(ge=1)
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

    @field_validator("asset_tags")
    @classmethod
    def normalize_asset_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(tag.upper().strip() for tag in value)
        if any(not tag for tag in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("asset_tags must be unique non-empty values")
        return normalized

    @model_validator(mode="after")
    def validate_prospective_contract(self) -> ProspectiveDocument:
        if self.available_at != self.retrieved_at:
            raise ValueError("Raw feed documents become available at retrieval time")
        if canonicalize_url(self.canonical_url) != self.canonical_url:
            raise ValueError("canonical_url is not canonical")
        expected_id = make_document_id(
            document_identity_payload(
                source_id=self.source_id,
                canonical_url=self.canonical_url,
                title=self.title,
                published_at=self.published_at,
                content_sha256=self.content_sha256,
            )
        )
        if self.document_id != expected_id:
            raise ValueError("document_id does not match the canonical document identity")
        return self


class DocumentEnvelope(BaseModel):
    """In-memory text plus the compact prospective metadata record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document: ProspectiveDocument
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_text_identity(self) -> DocumentEnvelope:
        encoded = self.text.encode("utf-8")
        if len(encoded) != self.document.content_length:
            raise ValueError("Document text length does not match metadata")
        if hashlib.sha256(encoded).hexdigest() != self.document.content_sha256:
            raise ValueError("Document text hash does not match metadata")
        return self
