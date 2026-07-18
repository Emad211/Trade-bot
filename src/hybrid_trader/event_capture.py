"""Prospective public-feed capture orchestration and compact manifests."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

import yaml

from hybrid_trader.event_capture_models import (
    EventCaptureFailure,
    EventCaptureManifest,
    EventCaptureSpec,
    RawPayloadRecord,
    SourceCaptureAttempt,
)
from hybrid_trader.event_capture_state import (
    CaptureLock,
    canonical_sha256,
    duplicate_content_count,
    ensure_empty_decision_ledger,
    finalize_capture_files,
)
from hybrid_trader.event_documents import DocumentEnvelope, FeedSourceSpec
from hybrid_trader.event_ledger import append_documents, verify_document_ledger
from hybrid_trader.event_relevance import (
    RelevanceDecision,
    evaluate_relevance,
    relevance_decisions_sha256,
)
from hybrid_trader.event_selection import select_semantic_envelopes
from hybrid_trader.feed_source import FeedFetchResult, PublicFeedSource
from hybrid_trader.semantic_extraction import (
    KeywordSemanticExtractor,
    SemanticEventRecord,
    append_semantic_records,
    verify_semantic_ledger,
)

__all__ = [
    "EventCaptureFailure",
    "EventCaptureManifest",
    "EventCaptureSpec",
    "SourceCaptureAttempt",
    "capture_events",
    "load_event_capture_spec",
]


class FeedClient(Protocol):
    def fetch(self, *, retrieved_at: datetime | None = None) -> FeedFetchResult: ...


class SemanticExtractor(Protocol):
    model_id: str
    model_revision: str

    @property
    def prompt_sha256(self) -> str: ...

    def extraction_key(self, envelope: DocumentEnvelope) -> str: ...

    def extract(
        self,
        envelope: DocumentEnvelope,
        *,
        inference_started_at: datetime | None = None,
        inference_completed_at: datetime | None = None,
    ) -> SemanticEventRecord: ...


FeedFactory = Callable[[FeedSourceSpec, int], FeedClient]
ExtractorFactory = Callable[[], SemanticExtractor]


def load_event_capture_spec(path: str | Path) -> EventCaptureSpec:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Event capture config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        payload: Any = yaml.safe_load(handle) or {}
    return EventCaptureSpec.model_validate(payload)


def _default_feed_factory(spec: FeedSourceSpec, timeout_seconds: int) -> FeedClient:
    return PublicFeedSource(spec, timeout_seconds=timeout_seconds)


def _default_extractor_factory() -> SemanticExtractor:
    return KeywordSemanticExtractor()


def capture_events(
    spec: EventCaptureSpec,
    output_dir: str | Path,
    *,
    captured_at: datetime | None = None,
    feed_factory: FeedFactory = _default_feed_factory,
    extractor_factory: ExtractorFactory = _default_extractor_factory,
    maximum_new_semantic_records: int | None = None,
) -> EventCaptureManifest:
    """Capture public feeds, append compact state, and never emit decisions."""

    if captured_at is not None and captured_at.tzinfo is None:
        raise ValueError("captured_at must be timezone-aware")
    if maximum_new_semantic_records is not None and maximum_new_semantic_records < 1:
        raise ValueError("maximum_new_semantic_records must be positive")
    root = Path(output_dir)
    state_root = root / "state"
    raw_root = root / "raw"
    state_root.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)

    with CaptureLock(state_root / ".capture.lock"):
        ensure_empty_decision_ledger(state_root / "prospective_decisions.jsonl")
        fixed_time = captured_at.astimezone(UTC) if captured_at is not None else None
        capture_started_at = fixed_time or datetime.now(UTC)
        raw_staging = raw_root / f".staging-{uuid.uuid4().hex}"
        raw_staging.mkdir(parents=True)

        attempts: list[SourceCaptureAttempt] = []
        envelopes: list[DocumentEnvelope] = []
        relevance_decisions: list[RelevanceDecision] = []
        raw_records_staging: list[tuple[str, Path, str, int]] = []
        for source_spec in spec.sources:
            try:
                result = feed_factory(source_spec, spec.timeout_seconds).fetch(
                    retrieved_at=fixed_time
                )
                raw_path = raw_staging / f"{source_spec.source_id}.xml"
                raw_path.write_bytes(result.payload)
                raw_records_staging.append(
                    (
                        source_spec.source_id,
                        raw_path,
                        result.payload_sha256,
                        len(result.payload),
                    )
                )
                source_relevance = tuple(
                    evaluate_relevance(envelope, source_spec.relevance)
                    for envelope in result.parse_result.documents
                )
                accepted_documents = [
                    envelope
                    for envelope, decision in zip(
                        result.parse_result.documents,
                        source_relevance,
                        strict=True,
                    )
                    if decision.accepted
                ]
                relevance_decisions.extend(source_relevance)
                attempts.append(
                    SourceCaptureAttempt(
                        source_id=source_spec.source_id,
                        feed_url=source_spec.feed_url,
                        required=source_spec.required,
                        status="success",
                        retrieved_at=result.retrieved_at,
                        payload_sha256=result.payload_sha256,
                        payload_bytes=len(result.payload),
                        parsed_documents=len(result.parse_result.documents),
                        duplicate_documents=result.parse_result.duplicate_count,
                        skipped_documents=result.parse_result.skipped_count,
                        truncated_documents=result.parse_result.truncated_count,
                        relevance_accepted_documents=len(accepted_documents),
                        relevance_rejected_documents=(
                            len(result.parse_result.documents) - len(accepted_documents)
                        ),
                        warnings=result.parse_result.warnings,
                    )
                )
                envelopes.extend(accepted_documents)
            except Exception as exc:
                attempts.append(
                    SourceCaptureAttempt(
                        source_id=source_spec.source_id,
                        feed_url=source_spec.feed_url,
                        required=source_spec.required,
                        status="failed",
                        retrieved_at=fixed_time or datetime.now(UTC),
                        error_type=type(exc).__name__,
                        error_message=str(exc)[:1000],
                    )
                )

        ordered_relevance_decisions = tuple(
            sorted(
                relevance_decisions,
                key=lambda item: (item.source_id, item.document_id, item.decision_id),
            )
        )
        relevance_sha = relevance_decisions_sha256(ordered_relevance_decisions)
        relevance_accepted_count = sum(
            decision.accepted for decision in ordered_relevance_decisions
        )
        relevance_rejected_count = len(ordered_relevance_decisions) - relevance_accepted_count
        extractor = extractor_factory()
        config_sha = canonical_sha256(spec.model_dump(mode="json"))
        successful = tuple(
            sorted(attempt.source_id for attempt in attempts if attempt.status == "success")
        )
        failed = tuple(
            sorted(attempt.source_id for attempt in attempts if attempt.status == "failed")
        )
        required_failures = sorted(
            attempt.source_id
            for attempt in attempts
            if attempt.required and attempt.status == "failed"
        )

        document_ledger = state_root / "documents.jsonl"
        semantic_ledger = state_root / "semantic_events.jsonl"
        new_document_count = 0
        new_semantic_count = 0
        recovered_semantic_count = 0
        failure: Exception | None = None

        try:
            if required_failures:
                raise RuntimeError(f"Required event sources failed: {required_failures}")
            if len(successful) < spec.minimum_successful_sources:
                raise RuntimeError("Too few event sources succeeded")

            unique_envelopes: dict[str, DocumentEnvelope] = {}
            for envelope in envelopes:
                existing = unique_envelopes.get(envelope.document.document_id)
                if existing is not None and existing.text != envelope.text:
                    raise ValueError("A document ID mapped to conflicting transient text")
                unique_envelopes[envelope.document.document_id] = envelope
            ordered_envelopes = sorted(
                unique_envelopes.values(),
                key=lambda item: (
                    item.document.retrieved_at,
                    item.document.source_id,
                    item.document.document_id,
                ),
            )

            _, _, _, existing_document_ids = verify_document_ledger(document_ledger)
            semantic_state = verify_semantic_ledger(semantic_ledger)
            selected_envelopes = select_semantic_envelopes(
                ordered_envelopes,
                extraction_key=extractor.extraction_key,
                existing_extraction_keys=semantic_state.extraction_keys,
                strategy=spec.semantic_selection_strategy,
                source_order=tuple(source.source_id for source in spec.sources),
                maximum_records=maximum_new_semantic_records,
            )
            records_to_append: list[SemanticEventRecord] = []
            for envelope in selected_envelopes:
                if envelope.document.document_id in existing_document_ids:
                    recovered_semantic_count += 1
                records_to_append.append(
                    extractor.extract(
                        envelope,
                        inference_started_at=fixed_time,
                        inference_completed_at=fixed_time,
                    )
                )

            new_document_count, _ = append_documents(
                document_ledger,
                [envelope.document for envelope in ordered_envelopes],
            )
            new_semantic_count, _ = append_semantic_records(
                semantic_ledger,
                records_to_append,
            )
            semantic_state = verify_semantic_ledger(semantic_ledger)
            _, _, _, current_document_ids = verify_document_ledger(document_ledger)
            if not semantic_state.document_ids.issubset(current_document_ids):
                raise RuntimeError("Semantic ledger references a missing document")
        except Exception as exc:
            failure = exc

        document_head, _, document_count, _ = verify_document_ledger(document_ledger)
        semantic_state = verify_semantic_ledger(semantic_ledger)
        capture_completed_at = fixed_time or datetime.now(UTC)
        status: Literal["success", "failed"] = "failed" if failure is not None else "success"
        identity = {
            "schema_version": "1.2",
            "status": status,
            "config_sha256": config_sha,
            "capture_started_at": capture_started_at.isoformat(),
            "capture_completed_at": capture_completed_at.isoformat(),
            "source_attempts": [attempt.model_dump(mode="json") for attempt in attempts],
            "document_ledger_head_sha256": document_head,
            "semantic_ledger_head_sha256": semantic_state.head_sha256,
            "relevance_decision_count": len(ordered_relevance_decisions),
            "relevance_accepted_document_count": relevance_accepted_count,
            "relevance_rejected_document_count": relevance_rejected_count,
            "relevance_decisions_sha256": relevance_sha,
            "failure_type": type(failure).__name__ if failure is not None else None,
            "failure_message": str(failure)[:1000] if failure is not None else None,
        }
        capture_id = canonical_sha256(identity)
        raw_records = tuple(
            RawPayloadRecord(
                source_id=source_id,
                relative_path=f"raw/{capture_id}/{path.name}",
                sha256=sha256,
                size_bytes=size_bytes,
            )
            for source_id, path, sha256, size_bytes in sorted(raw_records_staging)
        )
        manifest = EventCaptureManifest(
            capture_id=capture_id,
            status=status,
            config_sha256=config_sha,
            capture_started_at=capture_started_at,
            capture_completed_at=capture_completed_at,
            source_attempts=tuple(attempts),
            successful_sources=successful,
            failed_sources=failed,
            raw_payloads=raw_records,
            document_count=document_count,
            new_document_count=new_document_count,
            document_ledger_head_sha256=document_head,
            semantic_record_count=semantic_state.count,
            new_semantic_record_count=new_semantic_count,
            recovered_semantic_record_count=recovered_semantic_count,
            semantic_ledger_head_sha256=semantic_state.head_sha256,
            cross_source_duplicate_content_count=duplicate_content_count(envelopes),
            relevance_decision_count=len(ordered_relevance_decisions),
            relevance_accepted_document_count=relevance_accepted_count,
            relevance_rejected_document_count=relevance_rejected_count,
            relevance_decisions_sha256=relevance_sha,
            extractor_model_id=extractor.model_id,
            extractor_model_revision=extractor.model_revision,
            extractor_prompt_sha256=extractor.prompt_sha256,
            failure_type=type(failure).__name__ if failure is not None else None,
            failure_message=str(failure)[:1000] if failure is not None else None,
        )
        manifest_path = finalize_capture_files(
            state_root=state_root,
            raw_root=raw_root,
            raw_staging=raw_staging,
            manifest=manifest,
            relevance_decisions=ordered_relevance_decisions,
        )
        if failure is not None:
            raise EventCaptureFailure(str(failure), manifest_path=manifest_path) from failure
        return manifest
