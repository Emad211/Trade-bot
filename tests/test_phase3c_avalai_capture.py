from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.avalai import AvalAIHTTPResponse, AvalAISettings, AvalAIStructuredExtractor
from hybrid_trader.avalai_capture import (
    Phase3CAvalAIConfig,
    capture_avalai_events,
    verify_phase3c_avalai_root,
)
from hybrid_trader.event_capture_models import EventCaptureFailure, EventCaptureSpec
from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.feed_source import FeedFetchResult, parse_feed

RSS = b"""<rss><channel>
<item><title>Bitcoin Core release</title><link>https://example.com/releases/1</link>
<pubDate>Thu, 16 Jul 2026 11:55:00 GMT</pubDate>
<description>Protocol security fix</description></item>
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
    def __init__(self, *, status_code: int = 200) -> None:
        self.status_code = status_code
        self.calls = 0

    def __call__(self, url: str, headers, body: bytes, timeout_seconds: float):
        del url, headers, body, timeout_seconds
        self.calls += 1
        if self.status_code == 200:
            semantic = {
                "asset": "BTC",
                "event_time_utc": "2026-07-16T11:55:00Z",
                "event_type": "protocol_security_fix",
                "direction": "neutral",
                "horizon": "1d_3d",
                "severity": 0.7,
                "novelty": 0.6,
                "confidence": 0.5,
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
        else:
            payload = {
                "error": {
                    "code": "invalid_api_key",
                    "message": "invalid credential",
                }
            }
        return AvalAIHTTPResponse(
            status_code=self.status_code,
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
    )
    return Phase3CAvalAIConfig(
        capture=EventCaptureSpec(
            extractor="avalai_structured",
            sources=(source,),
        ),
        avalai=AvalAISettings(
            model="gpt-5-mini-2025-08-07",
            model_revision="gpt-5-mini-2025-08-07",
            max_retries=0,
            reasoning_effort=None,
        ),
    )


def _feed_factory(observed: datetime):
    def factory(spec: FeedSourceSpec, timeout_seconds: int) -> FakeFeedClient:
        assert timeout_seconds == 30
        return FakeFeedClient(spec, observed)

    return factory


def _extractor_factory(config: Phase3CAvalAIConfig, transport: FakeTransport, start: datetime):
    def factory() -> AvalAIStructuredExtractor:
        return AvalAIStructuredExtractor(
            config.avalai,
            api_key="unit-test-secret",
            transport=transport,
            clock=IncrementingClock(start),
        )

    return factory


def test_repeated_avalai_capture_is_deduplicated_and_secret_free(tmp_path: Path) -> None:
    config = _config()
    first_time = datetime(2026, 7, 16, 12, tzinfo=UTC)
    first_transport = FakeTransport()
    first = capture_avalai_events(
        config,
        tmp_path,
        feed_factory=_feed_factory(first_time),
        extractor_factory=_extractor_factory(
            config,
            first_transport,
            first_time + timedelta(seconds=1),
        ),
    )
    assert first.capture.status == "success"
    assert first.provider.new_call_count == 1
    assert first.provider.successful_call_count == 1
    assert first_transport.calls == 1

    second_time = first_time + timedelta(hours=1)
    second_transport = FakeTransport()
    second = capture_avalai_events(
        config,
        tmp_path,
        feed_factory=_feed_factory(second_time),
        extractor_factory=_extractor_factory(
            config,
            second_transport,
            second_time + timedelta(seconds=1),
        ),
    )
    assert second.capture.new_document_count == 0
    assert second.capture.new_semantic_record_count == 0
    assert second.provider.new_call_count == 0
    assert second_transport.calls == 0

    verification = verify_phase3c_avalai_root(tmp_path)
    assert verification["provider_run_count"] == 2
    assert verification["call_count"] == 1
    assert verification["semantic_record_count"] == 1
    assert verification["prospective_decision_count"] == 0
    assert not (tmp_path / "state" / "prospective_decisions.jsonl").read_text().strip()
    state_bytes = b"".join(
        path.read_bytes() for path in (tmp_path / "state").rglob("*") if path.is_file()
    )
    assert b"unit-test-secret" not in state_bytes
    assert b"Authorization" not in state_bytes


def test_failed_provider_call_is_audited_without_semantic_or_decision(tmp_path: Path) -> None:
    config = _config()
    observed = datetime(2026, 7, 16, 12, tzinfo=UTC)
    transport = FakeTransport(status_code=401)
    with pytest.raises(EventCaptureFailure):
        capture_avalai_events(
            config,
            tmp_path,
            feed_factory=_feed_factory(observed),
            extractor_factory=_extractor_factory(
                config,
                transport,
                observed + timedelta(seconds=1),
            ),
        )
    verification = verify_phase3c_avalai_root(tmp_path)
    assert verification["call_count"] == 1
    assert verification["successful_call_count"] == 0
    assert verification["failed_call_count"] == 1
    assert verification["semantic_record_count"] == 0
    assert verification["prospective_decision_count"] == 0
