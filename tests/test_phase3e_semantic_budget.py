from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.event_capture import EventCaptureSpec, capture_events
from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.feed_source import FeedFetchResult, parse_feed
from hybrid_trader.semantic_extraction import verify_semantic_ledger

RSS_TWO = b"""<rss><channel>
<item><title>Release 1.0</title><link>https://example.com/r/1</link>
<description>Protocol release</description></item>
<item><title>Security incident</title><link>https://example.com/r/2</link>
<description>Exploit fixed</description></item>
</channel></rss>"""


def _source() -> FeedSourceSpec:
    return FeedSourceSpec(
        source_id="source-one",
        feed_url="https://example.com/feed.xml",
        allowed_domains=("example.com",),
        source_quality=0.9,
        asset_tags=("BTC",),
        required=True,
    )


class FakeClient:
    def __init__(self, spec: FeedSourceSpec) -> None:
        self.spec = spec

    def fetch(self, *, retrieved_at: datetime | None = None) -> FeedFetchResult:
        if retrieved_at is None:
            raise AssertionError("Tests require an explicit retrieval timestamp")
        parsed = parse_feed(RSS_TWO, self.spec, retrieved_at=retrieved_at)
        return FeedFetchResult(
            source_id=self.spec.source_id,
            feed_url=self.spec.feed_url,
            retrieved_at=retrieved_at,
            payload=RSS_TWO,
            payload_sha256=hashlib.sha256(RSS_TWO).hexdigest(),
            parse_result=parsed,
        )


def _factory(spec: FeedSourceSpec, timeout_seconds: int) -> FakeClient:
    assert timeout_seconds == 30
    return FakeClient(spec)


def test_semantic_budget_defers_and_recovers_documents_across_runs(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 17, 8, tzinfo=UTC)
    spec = EventCaptureSpec(sources=(_source(),))

    first = capture_events(
        spec,
        tmp_path,
        captured_at=observed,
        feed_factory=_factory,
        maximum_new_semantic_records=1,
    )
    assert first.new_document_count == 2
    assert first.document_count == 2
    assert first.new_semantic_record_count == 1
    assert first.semantic_record_count == 1
    assert first.recovered_semantic_record_count == 0

    second = capture_events(
        spec,
        tmp_path,
        captured_at=observed + timedelta(hours=1),
        feed_factory=_factory,
        maximum_new_semantic_records=1,
    )
    assert second.new_document_count == 0
    assert second.document_count == 2
    assert second.new_semantic_record_count == 1
    assert second.semantic_record_count == 2
    assert second.recovered_semantic_record_count == 1

    third = capture_events(
        spec,
        tmp_path,
        captured_at=observed + timedelta(hours=2),
        feed_factory=_factory,
        maximum_new_semantic_records=1,
    )
    assert third.new_document_count == 0
    assert third.new_semantic_record_count == 0
    assert third.semantic_record_count == 2
    assert third.recovered_semantic_record_count == 0
    assert verify_semantic_ledger(tmp_path / "state" / "semantic_events.jsonl").count == 2


def test_semantic_budget_must_be_positive_before_state_mutation(tmp_path: Path) -> None:
    spec = EventCaptureSpec(sources=(_source(),))
    with pytest.raises(ValueError, match="maximum_new_semantic_records must be positive"):
        capture_events(
            spec,
            tmp_path,
            captured_at=datetime(2026, 7, 17, 8, tzinfo=UTC),
            feed_factory=_factory,
            maximum_new_semantic_records=0,
        )
    assert not tmp_path.exists()
