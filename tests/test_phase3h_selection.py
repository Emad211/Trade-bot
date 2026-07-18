from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from hybrid_trader.event_capture import EventCaptureSpec, capture_events
from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.feed_source import FeedFetchResult, parse_feed

RSS_TWO = b"""<rss><channel>
<item><title>Release alpha</title><link>https://example.com/alpha</link>
<description>Protocol release alpha</description></item>
<item><title>Release beta</title><link>https://example.com/beta</link>
<description>Protocol release beta</description></item>
</channel></rss>"""


def _source(source_id: str) -> FeedSourceSpec:
    return FeedSourceSpec(
        source_id=source_id,
        feed_url=f"https://example.com/{source_id}.xml",
        allowed_domains=("example.com",),
        source_quality=0.9,
        asset_tags=("BTC",),
        required=True,
        max_items=2,
    )


class FakeClient:
    def __init__(self, spec: FeedSourceSpec) -> None:
        self.spec = spec

    def fetch(self, *, retrieved_at: datetime | None = None) -> FeedFetchResult:
        if retrieved_at is None:
            raise AssertionError("Selection tests require a fixed retrieval time")
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


def _semantic_sources(root: Path) -> Counter[str]:
    path = root / "state" / "semantic_events.jsonl"
    return Counter(
        json.loads(line)["source_id"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def test_global_order_preserves_legacy_budget_behavior(tmp_path: Path) -> None:
    sources = (_source("source-a"), _source("source-b"))
    manifest = capture_events(
        EventCaptureSpec(sources=sources),
        tmp_path,
        captured_at=datetime(2026, 7, 18, 12, tzinfo=UTC),
        feed_factory=_factory,
        maximum_new_semantic_records=2,
    )
    assert manifest.new_document_count == 4
    assert manifest.new_semantic_record_count == 2
    assert _semantic_sources(tmp_path) == Counter({"source-a": 2})


def test_round_robin_spreads_budget_and_recovers_pending_work(tmp_path: Path) -> None:
    sources = (_source("source-a"), _source("source-b"))
    spec = EventCaptureSpec(
        sources=sources,
        semantic_selection_strategy="source_round_robin",
    )
    first = capture_events(
        spec,
        tmp_path,
        captured_at=datetime(2026, 7, 18, 12, tzinfo=UTC),
        feed_factory=_factory,
        maximum_new_semantic_records=2,
    )
    assert first.new_document_count == 4
    assert first.new_semantic_record_count == 2
    assert first.recovered_semantic_record_count == 0
    assert _semantic_sources(tmp_path) == Counter({"source-a": 1, "source-b": 1})

    second = capture_events(
        spec,
        tmp_path,
        captured_at=datetime(2026, 7, 18, 13, tzinfo=UTC),
        feed_factory=_factory,
        maximum_new_semantic_records=2,
    )
    assert second.new_document_count == 0
    assert second.new_semantic_record_count == 2
    assert second.recovered_semantic_record_count == 2
    assert _semantic_sources(tmp_path) == Counter({"source-a": 2, "source-b": 2})
