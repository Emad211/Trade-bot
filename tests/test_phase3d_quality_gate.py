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
from hybrid_trader.phase3d import Phase3DPolicy, assess_phase3d_pilot

RSS = b"""<rss><channel>
<item><title>Bitcoin Core release</title><link>https://example.com/releases/1</link>
<pubDate>Thu, 16 Jul 2026 11:55:00 GMT</pubDate>
<description>Routine protocol maintenance release</description></item>
</channel></rss>"""


class IncrementingClock:
    def __init__(self, start: datetime) -> None:
        self.start = start
        self.calls = 0

    def __call__(self) -> datetime:
        value = self.start + timedelta(milliseconds=self.calls)
        self.calls += 1
        return value


class FakeFeedClient:
    def __init__(self, spec: FeedSourceSpec, observed: datetime) -> None:
        self.spec = spec
        self.observed = observed

    def fetch(self, *, retrieved_at: datetime | None = None) -> FeedFetchResult:
        del retrieved_at
        parsed = parse_feed(RSS, self.spec, retrieved_at=self.observed)
        return FeedFetchResult(
            source_id=self.spec.source_id,
            feed_url=self.spec.feed_url,
            retrieved_at=self.observed,
            payload=RSS,
            payload_sha256=hashlib.sha256(RSS).hexdigest(),
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
            "event_time_utc": "2026-07-16T11:55:00Z",
            "event_type": "software_maintenance_release",
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
        max_items=1,
    )
    return Phase3CAvalAIConfig(
        capture=EventCaptureSpec(
            extractor="avalai_structured",
            sources=(source,),
            minimum_successful_sources=1,
        ),
        avalai=AvalAISettings(max_retries=0, reasoning_effort=None),
    )


def _feed_factory(observed: datetime):
    def factory(spec: FeedSourceSpec, timeout_seconds: int) -> FakeFeedClient:
        assert timeout_seconds == 30
        return FakeFeedClient(spec, observed)

    return factory


def _extractor_factory(
    config: Phase3CAvalAIConfig,
    transport: FakeTransport,
    start: datetime,
):
    def factory() -> AvalAIStructuredExtractor:
        return AvalAIStructuredExtractor(
            config.avalai,
            api_key="unit-test-secret-value",
            transport=transport,
            clock=IncrementingClock(start),
        )

    return factory


def _two_pass_capture(root: Path) -> None:
    config = _config()
    first_time = datetime(2026, 7, 16, 12, tzinfo=UTC)
    first_transport = FakeTransport()
    capture_avalai_events(
        config,
        root,
        feed_factory=_feed_factory(first_time),
        extractor_factory=_extractor_factory(
            config,
            first_transport,
            first_time + timedelta(seconds=1),
        ),
    )
    assert first_transport.calls == 1

    second_time = first_time + timedelta(hours=1)
    second_transport = FakeTransport()
    capture_avalai_events(
        config,
        root,
        feed_factory=_feed_factory(second_time),
        extractor_factory=_extractor_factory(
            config,
            second_transport,
            second_time + timedelta(seconds=1),
        ),
    )
    assert second_transport.calls == 0


def test_phase3d_gate_passes_bounded_deduplicated_capture(tmp_path: Path) -> None:
    _two_pass_capture(tmp_path)
    assessment = assess_phase3d_pilot(
        tmp_path,
        policy=Phase3DPolicy(
            max_new_calls=1,
            max_total_tokens=500,
            minimum_successful_sources=1,
        ),
    )
    assert assessment.status == "pass"
    assert assessment.call_count == 1
    assert assessment.semantic_record_count == 1
    assert assessment.repeat_capture_zero_new_calls is True
    assert assessment.total_tokens == 130
    assert assessment.direction_counts == {"neutral": 1}
    assert assessment.prospective_decision_count == 0
    assert assessment.credential_pattern_detected is False


def test_phase3d_gate_fails_closed_when_token_budget_is_exceeded(tmp_path: Path) -> None:
    _two_pass_capture(tmp_path)
    assessment = assess_phase3d_pilot(
        tmp_path,
        policy=Phase3DPolicy(
            max_new_calls=1,
            max_total_tokens=100,
            minimum_successful_sources=1,
        ),
    )
    assert assessment.status == "fail"
    assert assessment.recommended_action == "retain_research_only"
    assert "token_budget_exceeded" in assessment.failure_reasons
