from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.event_documents import (
    DocumentEnvelope,
    ProspectiveDocument,
    document_identity_payload,
    make_document_id,
)
from hybrid_trader.event_ledger import append_documents, verify_document_ledger


def _envelope(
    *,
    observed: datetime,
    url: str = "https://example.com/news/1",
    title: str = "Protocol release 1.0",
    source_quality: float = 0.9,
) -> DocumentEnvelope:
    encoded = title.encode("utf-8")
    content_sha = hashlib.sha256(encoded).hexdigest()
    identity = document_identity_payload(
        source_id="source-one",
        canonical_url=url,
        title=title,
        published_at=observed,
        content_sha256=content_sha,
    )
    document = ProspectiveDocument(
        document_id=make_document_id(**identity),
        source_id="source-one",
        canonical_url=url,
        title=title,
        published_at=observed,
        retrieved_at=observed,
        available_at=observed,
        source_quality=source_quality,
        asset_tags=("BTC",),
        content_sha256=content_sha,
        content_length=len(encoded),
        feed_payload_sha256="f" * 64,
    )
    return DocumentEnvelope(document=document, text=title)


def test_document_ledger_is_deduplicated_and_tamper_evident(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    first = _envelope(observed=observed)
    second = _envelope(
        observed=observed + timedelta(minutes=1),
        url="https://example.com/news/2",
        title="Protocol release 2.0",
    )
    ledger = tmp_path / "documents.jsonl"
    count, head = append_documents(ledger, [second.document, first.document])
    assert count == 2
    verified_head, previous, verified_count, ids = verify_document_ledger(ledger)
    assert verified_head == head
    assert previous is not None and previous.document_id == second.document.document_id
    assert verified_count == 2
    assert ids == frozenset({first.document.document_id, second.document.document_id})
    duplicate_count, duplicate_head = append_documents(ledger, [first.document])
    assert duplicate_count == 0
    assert duplicate_head == head

    raw = ledger.read_bytes()
    ledger.write_bytes(raw.replace(b"Protocol release 1.0", b"Protocol release X.0", 1))
    with pytest.raises(ValueError, match="Invalid event ledger|hash chain"):
        verify_document_ledger(ledger)


def test_document_ledger_rejects_conflicting_source_metadata(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    envelope = _envelope(observed=observed)
    ledger = tmp_path / "documents.jsonl"
    append_documents(ledger, [envelope.document])
    conflicting = envelope.document.model_copy(update={"source_quality": 0.1})
    with pytest.raises(ValueError, match="conflicting source metadata"):
        append_documents(ledger, [conflicting])
