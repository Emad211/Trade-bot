from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from hybrid_trader.event_documents import (
    DocumentEnvelope,
    ProspectiveDocument,
    document_identity_payload,
    make_document_id,
)
from hybrid_trader.events import EventSignal
from hybrid_trader.semantic_extraction import (
    KeywordSemanticExtractor,
    append_semantic_records,
    make_semantic_record,
    verify_semantic_ledger,
)


def _envelope(observed: datetime) -> DocumentEnvelope:
    title = "Protocol release 1.0"
    encoded = title.encode("utf-8")
    content_sha = hashlib.sha256(encoded).hexdigest()
    identity = document_identity_payload(
        source_id="source-one",
        canonical_url="https://example.com/news/1",
        title=title,
        published_at=observed,
        content_sha256=content_sha,
    )
    document = ProspectiveDocument(
        document_id=make_document_id(**identity),
        source_id="source-one",
        canonical_url="https://example.com/news/1",
        title=title,
        published_at=observed,
        retrieved_at=observed,
        available_at=observed,
        source_quality=0.9,
        asset_tags=("BTC",),
        content_sha256=content_sha,
        content_length=len(encoded),
        feed_payload_sha256="f" * 64,
    )
    return DocumentEnvelope(document=document, text=title)


def test_keyword_semantic_identity_is_stable_across_retries() -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    envelope = _envelope(observed)
    extractor = KeywordSemanticExtractor()
    first = extractor.extract(
        envelope,
        inference_started_at=observed + timedelta(seconds=1),
        inference_completed_at=observed + timedelta(seconds=2),
    )
    second = extractor.extract(
        envelope,
        inference_started_at=observed + timedelta(seconds=10),
        inference_completed_at=observed + timedelta(seconds=11),
    )
    assert first.signal_id == second.signal_id
    assert first.extraction_key == second.extraction_key
    assert first.available_at != second.available_at
    assert first.signal.direction == "neutral"


def test_semantic_schema_forbids_extra_output_and_bad_evidence() -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    envelope = _envelope(observed)
    payload = {
        "asset": "BTC",
        "event_time_utc": observed,
        "event_type": "release",
        "direction": "neutral",
        "horizon": "1w_plus",
        "severity": 0.2,
        "novelty": 1.0,
        "source_quality": 0.9,
        "confidence": 0.2,
        "evidence_ids": [envelope.document.document_id],
        "unexpected_field": 1,
    }
    with pytest.raises(ValidationError, match="unexpected_field"):
        EventSignal.model_validate(payload)

    signal = EventSignal.model_validate(
        {key: value for key, value in payload.items() if key != "unexpected_field"}
    )
    wrong = signal.model_copy(update={"evidence_ids": ("0" * 64,)})
    with pytest.raises(ValidationError, match="exactly its source"):
        make_semantic_record(
            envelope,
            wrong,
            model_id="test-model",
            model_revision="1",
            prompt="prompt",
            inference_started_at=observed,
            inference_completed_at=observed,
        )


def test_semantic_ledger_deduplicates_retries_and_rejects_conflicts(
    tmp_path: Path,
) -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    envelope = _envelope(observed)
    extractor = KeywordSemanticExtractor()
    first = extractor.extract(
        envelope,
        inference_started_at=observed,
        inference_completed_at=observed,
    )
    retry = extractor.extract(
        envelope,
        inference_started_at=observed + timedelta(minutes=1),
        inference_completed_at=observed + timedelta(minutes=1),
    )
    ledger = tmp_path / "semantic.jsonl"
    count, head = append_semantic_records(ledger, [first])
    assert count == 1
    retry_count, retry_head = append_semantic_records(ledger, [retry])
    assert retry_count == 0
    assert retry_head == head

    conflicting_signal = first.signal.model_copy(update={"event_type": "different_update"})
    conflict = make_semantic_record(
        envelope,
        conflicting_signal,
        model_id=first.model_id,
        model_revision=first.model_revision,
        prompt=extractor.prompt,
        inference_started_at=observed + timedelta(minutes=2),
        inference_completed_at=observed + timedelta(minutes=2),
    )
    with pytest.raises(ValueError, match="conflicting semantic output"):
        append_semantic_records(ledger, [conflict])

    state = verify_semantic_ledger(ledger)
    assert state.count == 1
    assert state.head_sha256 == head
    assert state.document_ids == frozenset({envelope.document.document_id})


def test_semantic_record_rejects_inference_before_document() -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    envelope = _envelope(observed)
    with pytest.raises(ValidationError, match="before the document"):
        KeywordSemanticExtractor().extract(
            envelope,
            inference_started_at=observed - timedelta(seconds=1),
            inference_completed_at=observed,
        )
