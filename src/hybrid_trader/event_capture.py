"""Prospective public-feed capture orchestration and compact manifests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_documents import DocumentEnvelope, FeedSourceSpec
from hybrid_trader.event_ledger import append_documents, verify_document_ledger
from hybrid_trader.feed_source import PublicFeedSource
from hybrid_trader.semantic_extraction import (
    KeywordSemanticExtractor,
    append_semantic_records,
    verify_semantic_ledger,
)

FeedFactory = Callable[[FeedSourceSpec, int], PublicFeedSource]


class EventCaptureSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    sources: tuple[FeedSourceSpec, ...]
    extractor: Literal["keyword_baseline"] = "keyword_baseline"
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
    parsed_documents: int = Field(default=0, ge=0)
    duplicate_documents: int = Field(default=0, ge=0)
    skipped_documents: int = Field(default=0, ge=0)
    warnings: tuple[str, ...] = ()
    error_type: str | None = None
    error_message: str | None = None

    @field_validator("retrieved_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Source attempt timestamps must be timezone-aware")
        return value.astimezone(UTC)


class EventCaptureManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    capture_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    captured_at: datetime
    source_attempts: tuple[SourceCaptureAttempt, ...]
    successful_sources: tuple[str, ...]
    failed_sources: tuple[str, ...]
    document_count: int = Field(ge=0)
    new_document_count: int = Field(ge=0)
    document_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    semantic_record_count: int = Field(ge=0)
    new_semantic_record_count: int = Field(ge=0)
    semantic_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    raw_payloads_committed_to_git: bool = False
    prospective_decisions_created: bool = False

    @field_validator("captured_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("captured_at must be timezone-aware")
        return value.astimezone(UTC)


def _canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_event_capture_spec(path: str | Path) -> EventCaptureSpec:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Event capture config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        payload: Any = yaml.safe_load(handle) or {}
    return EventCaptureSpec.model_validate(payload)


def _default_feed_factory(spec: FeedSourceSpec, timeout_seconds: int) -> PublicFeedSource:
    return PublicFeedSource(spec, timeout_seconds=timeout_seconds)


def capture_events(
    spec: EventCaptureSpec,
    output_dir: str | Path,
    *,
    captured_at: datetime | None = None,
    feed_factory: FeedFactory = _default_feed_factory,
) -> EventCaptureManifest:
    """Capture public feeds, append metadata/features, and never emit decisions."""

    root = Path(output_dir)
    manifest_path = root / "capture_manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"Capture output is immutable: {root}")
    root.mkdir(parents=True, exist_ok=True)
    raw_root = root / "raw"
    raw_root.mkdir(exist_ok=True)
    observed_at = (captured_at or datetime.now(UTC)).astimezone(UTC)

    attempts: list[SourceCaptureAttempt] = []
    envelopes: list[DocumentEnvelope] = []
    required_failures: list[str] = []
    for source_spec in spec.sources:
        try:
            result = feed_factory(source_spec, spec.timeout_seconds).fetch(
                retrieved_at=observed_at
            )
            (raw_root / f"{source_spec.source_id}.xml").write_bytes(result.payload)
            attempts.append(
                SourceCaptureAttempt(
                    source_id=source_spec.source_id,
                    feed_url=source_spec.feed_url,
                    required=source_spec.required,
                    status="success",
                    retrieved_at=result.retrieved_at,
                    payload_sha256=result.payload_sha256,
                    parsed_documents=len(result.parse_result.documents),
                    duplicate_documents=result.parse_result.duplicate_count,
                    skipped_documents=result.parse_result.skipped_count,
                    warnings=result.parse_result.warnings,
                )
            )
            envelopes.extend(result.parse_result.documents)
        except Exception as exc:
            attempts.append(
                SourceCaptureAttempt(
                    source_id=source_spec.source_id,
                    feed_url=source_spec.feed_url,
                    required=source_spec.required,
                    status="failed",
                    retrieved_at=observed_at,
                    error_type=type(exc).__name__,
                    error_message=str(exc)[:1000],
                )
            )
            if source_spec.required:
                required_failures.append(source_spec.source_id)

    attempts_path = root / "source_attempts.json"
    attempts_path.write_text(
        json.dumps(
            [attempt.model_dump(mode="json") for attempt in attempts],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    successful = tuple(sorted(attempt.source_id for attempt in attempts if attempt.status == "success"))
    failed = tuple(sorted(attempt.source_id for attempt in attempts if attempt.status == "failed"))
    if required_failures:
        raise RuntimeError(f"Required event sources failed: {sorted(required_failures)}")
    if len(successful) < spec.minimum_successful_sources:
        raise RuntimeError("Too few event sources succeeded")

    document_ledger = root / "documents.jsonl"
    _, _, _, existing_document_ids = verify_document_ledger(document_ledger)
    unseen_envelopes = [
        envelope
        for envelope in envelopes
        if envelope.document.document_id not in existing_document_ids
    ]
    new_document_count, document_head = append_documents(
        document_ledger,
        [envelope.document for envelope in unseen_envelopes],
    )
    _, _, document_count, _ = verify_document_ledger(document_ledger)

    extractor = KeywordSemanticExtractor()
    semantic_records = [extractor.extract(envelope) for envelope in unseen_envelopes]
    semantic_ledger = root / "semantic_events.jsonl"
    new_semantic_count, semantic_head = append_semantic_records(
        semantic_ledger,
        semantic_records,
    )
    _, _, semantic_count, _ = verify_semantic_ledger(semantic_ledger)
    (root / "prospective_decisions.jsonl").write_text("", encoding="utf-8")

    config_payload = spec.model_dump(mode="json")
    config_sha = _canonical_sha256(config_payload)
    identity = {
        "config_sha256": config_sha,
        "captured_at": observed_at.isoformat(),
        "source_attempts": [attempt.model_dump(mode="json") for attempt in attempts],
        "document_ledger_head_sha256": document_head,
        "semantic_ledger_head_sha256": semantic_head,
    }
    manifest = EventCaptureManifest(
        capture_id=_canonical_sha256(identity),
        config_sha256=config_sha,
        captured_at=observed_at,
        source_attempts=tuple(attempts),
        successful_sources=successful,
        failed_sources=failed,
        document_count=document_count,
        new_document_count=new_document_count,
        document_ledger_head_sha256=document_head,
        semantic_record_count=semantic_count,
        new_semantic_record_count=new_semantic_count,
        semantic_ledger_head_sha256=semantic_head,
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
