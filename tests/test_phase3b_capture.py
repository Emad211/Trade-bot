from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.event_capture import (
    EventCaptureFailure,
    EventCaptureSpec,
    capture_events,
)
from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.feed_source import FeedFetchResult, parse_feed
from hybrid_trader.semantic_extraction import verify_semantic_ledger

RSS_ONE = b"""<rss><channel>
<item><title>Release 1.0</title><link>https://example.com/r/1</link>
<description>Protocol release</description></item>
</channel></rss>"""
RSS_TWO = b"""<rss><channel>
<item><title>Release 1.0</title><link>https://example.com/r/1</link>
<description>Protocol release</description></item>
<item><title>Security incident</title><link>https://example.com/r/2</link>
<description>Exploit fixed</description></item>
</channel></rss>"""


def _source(source_id: str = "source-one", *, required: bool = True) -> FeedSourceSpec:
    return FeedSourceSpec(
        source_id=source_id,
        feed_url="https://example.com/feed.xml",
        allowed_domains=("example.com",),
        source_quality=0.9,
        asset_tags=("BTC",),
        required=required,
    )


class FakeClient:
    def __init__(self, spec: FeedSourceSpec, payload: bytes | Exception) -> None:
        self.spec = spec
        self.payload = payload

    def fetch(self, *, retrieved_at: datetime | None = None) -> FeedFetchResult:
        if isinstance(self.payload, Exception):
            raise self.payload
        if retrieved_at is None:
            raise AssertionError("Tests require an explicit retrieval timestamp")
        parsed = parse_feed(self.payload, self.spec, retrieved_at=retrieved_at)
        return FeedFetchResult(
            source_id=self.spec.source_id,
            feed_url=self.spec.feed_url,
            retrieved_at=retrieved_at,
            payload=self.payload,
            payload_sha256=hashlib.sha256(self.payload).hexdigest(),
            parse_result=parsed,
        )


def _factory(payloads: dict[str, bytes | Exception]):
    def factory(spec: FeedSourceSpec, timeout_seconds: int) -> FakeClient:
        assert timeout_seconds == 30
        return FakeClient(spec, payloads[spec.source_id])

    return factory


def test_repeated_capture_appends_only_new_state(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    spec = EventCaptureSpec(sources=(_source(),))
    first = capture_events(
        spec,
        tmp_path,
        captured_at=observed,
        feed_factory=_factory({"source-one": RSS_ONE}),
    )
    assert first.status == "success"
    assert first.new_document_count == 1
    assert first.new_semantic_record_count == 1
    assert not first.prospective_decisions_created

    second = capture_events(
        spec,
        tmp_path,
        captured_at=observed + timedelta(hours=1),
        feed_factory=_factory({"source-one": RSS_ONE}),
    )
    assert second.new_document_count == 0
    assert second.new_semantic_record_count == 0
    assert second.document_count == 1
    assert second.semantic_record_count == 1

    third = capture_events(
        spec,
        tmp_path,
        captured_at=observed + timedelta(hours=2),
        feed_factory=_factory({"source-one": RSS_TWO}),
    )
    assert third.new_document_count == 1
    assert third.new_semantic_record_count == 1
    assert third.document_count == 2
    assert third.semantic_record_count == 2
    assert len(list((tmp_path / "state" / "captures").iterdir())) == 3
    assert not (tmp_path / "state" / "prospective_decisions.jsonl").read_text().strip()
    for capture_id in (first.capture_id, second.capture_id, third.capture_id):
        capture_dir = tmp_path / "state" / "captures" / capture_id
        assert (capture_dir / "capture_manifest.json").exists()
        assert (capture_dir / "SHA256SUMS").exists()
        assert (tmp_path / "raw" / capture_id / "source-one.xml").exists()


def test_capture_recovers_missing_semantic_for_existing_document(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    spec = EventCaptureSpec(sources=(_source(),))
    capture_events(
        spec,
        tmp_path,
        captured_at=observed,
        feed_factory=_factory({"source-one": RSS_ONE}),
    )
    semantic_ledger = tmp_path / "state" / "semantic_events.jsonl"
    semantic_ledger.write_text("", encoding="utf-8")
    recovered = capture_events(
        spec,
        tmp_path,
        captured_at=observed + timedelta(hours=1),
        feed_factory=_factory({"source-one": RSS_ONE}),
    )
    assert recovered.new_document_count == 0
    assert recovered.new_semantic_record_count == 1
    assert recovered.recovered_semantic_record_count == 1
    assert verify_semantic_ledger(semantic_ledger).count == 1


def test_required_failure_is_recorded_without_state_mutation(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    spec = EventCaptureSpec(sources=(_source(),))
    with pytest.raises(EventCaptureFailure) as caught:
        capture_events(
            spec,
            tmp_path,
            captured_at=observed,
            feed_factory=_factory({"source-one": RuntimeError("offline")}),
        )
    manifest = json.loads(caught.value.manifest_path.read_text())
    assert manifest["status"] == "failed"
    assert manifest["failure_type"] == "RuntimeError"
    assert manifest["new_document_count"] == 0
    assert not (tmp_path / "state" / "documents.jsonl").exists()
    assert not (tmp_path / "state" / "semantic_events.jsonl").exists()
    assert not (tmp_path / "state" / "prospective_decisions.jsonl").read_text().strip()


def test_nonempty_decision_ledger_and_concurrent_lock_fail_closed(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    spec = EventCaptureSpec(sources=(_source(),))
    state = tmp_path / "state"
    state.mkdir(parents=True)
    decision_ledger = state / "prospective_decisions.jsonl"
    decision_ledger.write_text("forbidden\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not empty"):
        capture_events(
            spec,
            tmp_path,
            captured_at=observed,
            feed_factory=_factory({"source-one": RSS_ONE}),
        )
    decision_ledger.write_text("", encoding="utf-8")
    (state / ".capture.lock").write_text("locked", encoding="utf-8")
    with pytest.raises(RuntimeError, match="holds the lock"):
        capture_events(
            spec,
            tmp_path,
            captured_at=observed,
            feed_factory=_factory({"source-one": RSS_ONE}),
        )


def test_cross_source_duplicate_content_is_reported(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    one = _source("source-one")
    two = _source("source-two", required=False)
    spec = EventCaptureSpec(sources=(one, two), minimum_successful_sources=2)
    manifest = capture_events(
        spec,
        tmp_path,
        captured_at=observed,
        feed_factory=_factory({"source-one": RSS_ONE, "source-two": RSS_ONE}),
    )
    assert manifest.cross_source_duplicate_content_count == 1
    assert manifest.new_document_count == 2
    assert manifest.new_semantic_record_count == 2
