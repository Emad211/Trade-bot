"""Typed contracts for prospective public-feed capture runs."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_documents import FeedSourceSpec


class EventCaptureSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.3"
    sources: tuple[FeedSourceSpec, ...]
    extractor: Literal["keyword_baseline", "avalai_structured"] = "keyword_baseline"
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    minimum_successful_sources: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_sources(self) -> EventCaptureSpec:
        source_ids = [source.source_id for source in self.sources]
        if not source_ids:
            raise ValueError("At least one feed source is required")
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("Feed source IDs cannot contain duplicates")
        if self.minimum_successful_sources > len(self.sources):
            raise ValueError("minimum_successful_sources exceeds the source count")
        return self


class SourceCaptureAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    feed_url: str
    required: bool
    status: Literal["success", "failed"]
    retrieved_at: datetime
    payload_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    payload_bytes: int = Field(default=0, ge=0)
    parsed_documents: int = Field(default=0, ge=0)
    duplicate_documents: int = Field(default=0, ge=0)
    skipped_documents: int = Field(default=0, ge=0)
    truncated_documents: int = Field(default=0, ge=0)
    relevance_accepted_documents: int = Field(default=0, ge=0)
    relevance_rejected_documents: int = Field(default=0, ge=0)
    warnings: tuple[str, ...] = ()
    error_type: str | None = None
    error_message: str | None = None

    @field_validator("retrieved_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Source attempt timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_relevance_counts(self) -> SourceCaptureAttempt:
        decided = self.relevance_accepted_documents + self.relevance_rejected_documents
        if self.status == "success" and decided not in (0, self.parsed_documents):
            raise ValueError(
                "Source relevance counts must be legacy-zero or equal parsed_documents"
            )
        if self.status == "failed" and decided:
            raise ValueError("Failed source cannot contain relevance decisions")
        return self


class RawPayloadRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    relative_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class EventCaptureManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.2"
    capture_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["success", "failed"]
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    capture_started_at: datetime
    capture_completed_at: datetime
    source_attempts: tuple[SourceCaptureAttempt, ...]
    successful_sources: tuple[str, ...]
    failed_sources: tuple[str, ...]
    raw_payloads: tuple[RawPayloadRecord, ...]
    document_count: int = Field(ge=0)
    new_document_count: int = Field(ge=0)
    document_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    semantic_record_count: int = Field(ge=0)
    new_semantic_record_count: int = Field(ge=0)
    recovered_semantic_record_count: int = Field(ge=0)
    semantic_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    cross_source_duplicate_content_count: int = Field(ge=0)
    relevance_decision_count: int = Field(default=0, ge=0)
    relevance_accepted_document_count: int = Field(default=0, ge=0)
    relevance_rejected_document_count: int = Field(default=0, ge=0)
    relevance_decisions_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    extractor_model_id: str
    extractor_model_revision: str
    extractor_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_payloads_committed_to_git: bool = False
    prospective_decisions_created: bool = False
    failure_type: str | None = None
    failure_message: str | None = None

    @field_validator("capture_started_at", "capture_completed_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Capture timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_capture_contract(self) -> EventCaptureManifest:
        if self.capture_completed_at < self.capture_started_at:
            raise ValueError("capture_completed_at cannot precede capture_started_at")
        if self.raw_payloads_committed_to_git:
            raise ValueError("Raw event payloads cannot be marked as committed to Git")
        if self.prospective_decisions_created:
            raise ValueError("Event capture cannot create prospective trading decisions")
        if self.status == "success" and (self.failure_type or self.failure_message):
            raise ValueError("Successful captures cannot contain failure metadata")
        if self.status == "failed" and not self.failure_type:
            raise ValueError("Failed captures must record a failure_type")
        if (
            self.relevance_accepted_document_count
            + self.relevance_rejected_document_count
            != self.relevance_decision_count
        ):
            raise ValueError("Capture relevance counts do not reconcile")
        if self.relevance_decision_count and self.relevance_decisions_sha256 is None:
            raise ValueError("Capture relevance decisions require a checksum")
        return self


class EventCaptureFailure(RuntimeError):
    def __init__(self, message: str, *, manifest_path: Path) -> None:
        super().__init__(message)
        self.manifest_path = manifest_path
