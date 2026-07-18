from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hybrid_trader.avalai import AvalAIHTTPResponse, AvalAISettings, AvalAIStructuredExtractor
from hybrid_trader.avalai_capture import Phase3CAvalAIConfig, capture_avalai_events
from hybrid_trader.event_capture_models import EventCaptureSpec
from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.event_source_spec import FeedRelevanceSpec
from hybrid_trader.feed_source import FeedFetchResult, parse_feed
from hybrid_trader.phase3h import Phase3HPilotPolicy, assess_phase3h_pilot

RSS_OPTECH = b"""<rss><channel>
<item><title>Bitcoin protocol review alpha</title><link>https://example.com/optech-a</link>
<description>Bitcoin protocol and Lightning development.</description></item>
<item><title>Bitcoin protocol review beta</title><link>https://example.com/optech-b</link>
<description>Bitcoin transaction relay development.</description></item>
</channel></rss>"""
RSS_FED = b"""<rss><channel>
<item><title>Federal Reserve monetary policy statement</title><link>https://example.com/fed</link>
<description>Interest-rate and monetary-policy update.</description></item>
</channel></rss>"""
RSS_SEC = b"""<rss><channel>
<item><title>SEC announces accounting fellowship</title><link>https://example.com/sec</link>
<description>Application dates for an accounting fellowship.</description></item>
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


class AssetAwareTransport:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, url: str, headers, body: bytes, timeout_seconds: float):
        del url, headers, timeout_seconds
        self.calls += 1
        request = json.loads(body)
        document = json.loads(request["input"])
        allowed_assets = document["allowed_asset_tags"]
        asset = allowed_assets[0] if allowed_assets else "MARKET"
        semantic = {
            "asset": asset,
            "event_time_utc": "2026-07-18T12:00:00Z",
            "event_type": "prospective_source_update",
            "direction": "neutral",
            "horizon": "1d_3d",
            "severity": 0.3,
            "novelty": 0.5,
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


def _sources() -> tuple[FeedSourceSpec, ...]:
    return (
        FeedSourceSpec(
            source_id="bitcoin-optech-newsletters",
            feed_url="https://example.com/optech.xml",
            allowed_domains=("example.com",),
            source_quality=0.92,
            asset_tags=("BTC",),
            required=True,
            max_items=2,
        ),
        FeedSourceSpec(
            source_id="federal-reserve-monetary-policy",
            feed_url="https://example.com/fed.xml",
            allowed_domains=("example.com",),
            source_quality=0.98,
            asset_tags=("MARKET",),
            required=True,
            max_items=1,
        ),
        FeedSourceSpec(
            source_id="sec-press-releases",
            feed_url="https://example.com/sec.xml",
            allowed_domains=("example.com",),
            source_quality=0.98,
            asset_tags=("BTC", "MARKET"),
            required=False,
            max_items=1,
            relevance=FeedRelevanceSpec(include_any_terms=("bitcoin", "digital asset")),
        ),
    )


def _payload(source_id: str) -> bytes:
    return {
        "bitcoin-optech-newsletters": RSS_OPTECH,
        "federal-reserve-monetary-policy": RSS_FED,
        "sec-press-releases": RSS_SEC,
    }[source_id]


def _write_context(root: Path) -> None:
    (root / "phase3e_run_context.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "workflow_run_id": "phase3h-test",
                "source_commit_sha": "a" * 40,
                "previous_workflow_run_id": None,
                "previous_artifact_id": None,
                "previous_artifact_digest": None,
                "state_restored": False,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _run_capture(root: Path, *, strategy: str) -> AssetAwareTransport:
    observed = datetime(2026, 7, 18, 12, tzinfo=UTC)
    settings = AvalAISettings(max_retries=0, reasoning_effort=None)
    config = Phase3CAvalAIConfig(
        capture=EventCaptureSpec(
            extractor="avalai_structured",
            sources=_sources(),
            minimum_successful_sources=2,
            semantic_selection_strategy=strategy,
        ),
        avalai=settings,
    )
    transport = AssetAwareTransport()

    def feed_factory(spec: FeedSourceSpec, timeout_seconds: int) -> FakeFeedClient:
        assert timeout_seconds == 30
        return FakeFeedClient(spec, _payload(spec.source_id), observed)

    def extractor_factory() -> AvalAIStructuredExtractor:
        return AvalAIStructuredExtractor(
            settings,
            api_key="unit-test-secret-value",
            transport=transport,
            clock=SequenceClock(observed + timedelta(seconds=1)),
        )

    capture_avalai_events(
        config,
        root,
        feed_factory=feed_factory,
        extractor_factory=extractor_factory,
        maximum_new_semantic_records=2,
    )
    _write_context(root)
    return transport


def _policy() -> Phase3HPilotPolicy:
    return Phase3HPilotPolicy(
        max_new_calls=2,
        max_total_tokens=500,
        minimum_successful_sources=2,
        minimum_new_semantic_sources=2,
        minimum_new_assets=2,
        required_new_sources=(
            "bitcoin-optech-newsletters",
            "federal-reserve-monetary-policy",
        ),
        required_new_assets=("BTC", "MARKET"),
        minimum_relevance_rejections=1,
    )


def test_round_robin_phase3h_pilot_passes_diversity_and_relevance_gates(
    tmp_path: Path,
) -> None:
    transport = _run_capture(tmp_path, strategy="source_round_robin")
    assessment = assess_phase3h_pilot(tmp_path, policy=_policy())

    assert transport.calls == 2
    assert assessment.status == "pass"
    assert assessment.new_semantic_sources == (
        "bitcoin-optech-newsletters",
        "federal-reserve-monetary-policy",
    )
    assert assessment.new_semantic_assets == ("BTC", "MARKET")
    assert assessment.zero_accepted_sources_called == ()
    assert assessment.relevance_rejected_document_count == 1
    assert assessment.prospective_decision_count == 0
    assert assessment.paper_or_live_trading_allowed is False


def test_global_order_phase3h_pilot_fails_required_diversity(tmp_path: Path) -> None:
    transport = _run_capture(tmp_path, strategy="global_order")
    assessment = assess_phase3h_pilot(tmp_path, policy=_policy())

    assert transport.calls == 2
    assert assessment.status == "fail"
    assert assessment.new_semantic_sources == ("bitcoin-optech-newsletters",)
    assert assessment.new_semantic_assets == ("BTC",)
    assert "required_new_sources_missing" in assessment.failure_reasons
    assert "required_new_assets_missing" in assessment.failure_reasons
