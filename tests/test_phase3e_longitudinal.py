from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hybrid_trader.avalai import (
    AvalAIHTTPResponse,
    AvalAISettings,
    AvalAIStructuredExtractor,
)
from hybrid_trader.avalai_capture import Phase3CAvalAIConfig, capture_avalai_events
from hybrid_trader.event_capture_models import EventCaptureSpec
from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.feed_source import FeedFetchResult, parse_feed
from hybrid_trader.phase3e import Phase3EPolicy, assess_phase3e_run

RSS_ONE = b"""<rss><channel>
<item><title>Release 1.0</title><link>https://example.com/r/1</link>
<description>Routine protocol release</description></item>
</channel></rss>"""
RSS_TWO = b"""<rss><channel>
<item><title>Release 1.0</title><link>https://example.com/r/1</link>
<description>Routine protocol release</description></item>
<item><title>Security release</title><link>https://example.com/r/2</link>
<description>Security fix released</description></item>
</channel></rss>"""


class SequenceClock:
    def __init__(self, start: datetime) -> None:
        self.start = start
        self.calls = 0

    def __call__(self) -> datetime:
        value = self.start + timedelta(milliseconds=self.calls)
        self.calls += 1
        return value


class FakeFeedClient:
    def __init__(self, spec: FeedSourceSpec, payload: bytes, observed: datetime) -> None:
        self.spec = spec
        self.payload = payload
        self.observed = observed

    def fetch(self, *, retrieved_at: datetime | None = None) -> FeedFetchResult:
        del retrieved_at
        parsed = parse_feed(self.payload, self.spec, retrieved_at=self.observed)
        return FeedFetchResult(
            source_id=self.spec.source_id,
            feed_url=self.spec.feed_url,
            retrieved_at=self.observed,
            payload=self.payload,
            payload_sha256=hashlib.sha256(self.payload).hexdigest(),
            parse_result=parsed,
        )


class FakeTransport:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, url: str, headers, body: bytes, timeout_seconds: float):
        del url, headers, body, timeout_seconds
        self.calls += 1
        semantic = {
            "asset": "BTC",
            "event_time_utc": "2026-07-17T08:00:00Z",
            "event_type": "software_release",
            "direction": "neutral",
            "horizon": "1d_3d",
            "severity": 0.2,
            "novelty": 0.3,
            "confidence": 0.6,
        }
        payload = {
            "id": f"resp-{self.calls}",
            "status": "completed",
            "model": "gpt-5-mini-2025-08-07",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": json.dumps(semantic)}],
                }
            ],
            "usage": {"input_tokens": 100, "output_tokens": 30, "total_tokens": 130},
        }
        return AvalAIHTTPResponse(
            status_code=200,
            headers={"x-request-id": f"provider-{self.calls}"},
            body=json.dumps(payload).encode(),
        )


def _config() -> Phase3CAvalAIConfig:
    source = FeedSourceSpec(
        source_id="official-feed",
        feed_url="https://example.com/feed.xml",
        allowed_domains=("example.com",),
        source_quality=0.95,
        asset_tags=("BTC",),
        required=True,
        max_items=10,
    )
    return Phase3CAvalAIConfig(
        capture=EventCaptureSpec(
            extractor="avalai_structured",
            sources=(source,),
            minimum_successful_sources=1,
        ),
        avalai=AvalAISettings(max_retries=0, reasoning_effort=None),
    )


def _capture(
    root: Path,
    *,
    payload: bytes,
    observed: datetime,
    maximum_new_semantic_records: int,
) -> None:
    config = _config()
    transport = FakeTransport()

    def feed_factory(spec: FeedSourceSpec, timeout_seconds: int) -> FakeFeedClient:
        assert timeout_seconds == 30
        return FakeFeedClient(spec, payload, observed)

    def extractor_factory() -> AvalAIStructuredExtractor:
        return AvalAIStructuredExtractor(
            config.avalai,
            api_key="unit-test-secret-value",
            transport=transport,
            clock=SequenceClock(observed + timedelta(seconds=1)),
        )

    capture_avalai_events(
        config,
        root,
        feed_factory=feed_factory,
        extractor_factory=extractor_factory,
        maximum_new_semantic_records=maximum_new_semantic_records,
    )
    assert transport.calls == 1


def _write_context(root: Path, *, restored: bool) -> None:
    payload = {
        "schema_version": "1.0",
        "workflow_run_id": "current-run",
        "source_commit_sha": "a" * 40,
        "previous_workflow_run_id": "previous-run",
        "previous_artifact_id": 123,
        "previous_artifact_digest": f"sha256:{'b' * 64}",
        "state_restored": restored,
    }
    (root / "phase3e_run_context.json").write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def test_phase3e_assesses_only_latest_restored_delta(tmp_path: Path) -> None:
    first_time = datetime(2026, 7, 17, 8, tzinfo=UTC)
    _capture(
        tmp_path,
        payload=RSS_ONE,
        observed=first_time,
        maximum_new_semantic_records=1,
    )
    _capture(
        tmp_path,
        payload=RSS_TWO,
        observed=first_time + timedelta(hours=1),
        maximum_new_semantic_records=1,
    )
    _write_context(tmp_path, restored=True)

    assessment = assess_phase3e_run(
        tmp_path,
        policy=Phase3EPolicy(
            max_new_calls_per_run=1,
            max_total_tokens_per_run=500,
        ),
    )
    assert assessment.status == "pass"
    assert assessment.previous_call_count == 1
    assert assessment.total_call_count == 2
    assert assessment.new_call_count == 1
    assert assessment.latest_total_tokens == 130
    assert assessment.duplicate_extraction_key_count == 0
    assert assessment.pending_semantic_document_count == 0
    assert assessment.prospective_decision_count == 0


def test_phase3e_rejects_declared_previous_run_without_restoration(tmp_path: Path) -> None:
    observed = datetime(2026, 7, 17, 8, tzinfo=UTC)
    _capture(
        tmp_path,
        payload=RSS_ONE,
        observed=observed,
        maximum_new_semantic_records=1,
    )
    _write_context(tmp_path, restored=False)
    assessment = assess_phase3e_run(tmp_path)
    assert assessment.status == "fail"
    assert assessment.recommended_action == "halt_and_review"
    assert "previous_state_not_restored" in assessment.failure_reasons
