from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hybrid_trader.avalai import AvalAIHTTPResponse, AvalAISettings, AvalAIStructuredExtractor
from hybrid_trader.avalai_capture import Phase3CAvalAIConfig, capture_avalai_events
from hybrid_trader.event_capture_models import EventCaptureSpec
from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.feed_source import FeedFetchResult, parse_feed
from hybrid_trader.phase3i_health import (
    Phase3ISourceHealthPolicy,
    assess_phase3i_source_health,
)

RSS_ALPHA_TWO = b"""<rss><channel>
<item><title>Alpha one</title><link>https://example.com/alpha-1</link><description>Alpha protocol update.</description></item>
<item><title>Alpha two</title><link>https://example.com/alpha-2</link><description>Alpha protocol review.</description></item>
</channel></rss>"""
RSS_BETA_TWO = b"""<rss><channel>
<item><title>Beta one</title><link>https://example.com/beta-1</link><description>Market policy update.</description></item>
<item><title>Beta two</title><link>https://example.com/beta-2</link><description>Market outlook update.</description></item>
</channel></rss>"""
RSS_DRIFT_ONE = b"""<rss><channel>
<item><title>Drift one</title><link>https://example.com/drift-1</link><description>First source policy.</description></item>
</channel></rss>"""
RSS_DRIFT_TWO = b"""<rss><channel>
<item><title>Drift two</title><link>https://example.com/drift-2</link><description>Second source policy.</description></item>
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
        document = json.loads(json.loads(body)["input"])
        asset = document["allowed_asset_tags"][0]
        semantic = {
            "asset": asset,
            "event_time_utc": "2026-07-18T12:00:00Z",
            "event_type": "source_health_test",
            "direction": "neutral",
            "horizon": "1d_3d",
            "severity": 0.2,
            "novelty": 0.4,
            "confidence": 0.6,
        }
        response = {
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
            body=json.dumps(response).encode(),
        )


def _source(source_id: str, asset: str, quality: float, max_items: int) -> FeedSourceSpec:
    return FeedSourceSpec(
        source_id=source_id,
        feed_url=f"https://example.com/{source_id}.xml",
        allowed_domains=("example.com",),
        source_quality=quality,
        asset_tags=(asset,),
        required=True,
        max_items=max_items,
    )


def _capture(
    root: Path,
    *,
    sources: tuple[FeedSourceSpec, ...],
    payloads: dict[str, bytes],
    observed: datetime,
    maximum_records: int,
) -> AssetAwareTransport:
    settings = AvalAISettings(max_retries=0, reasoning_effort=None)
    config = Phase3CAvalAIConfig(
        capture=EventCaptureSpec(
            extractor="avalai_structured",
            sources=sources,
            minimum_successful_sources=1,
            semantic_selection_strategy="source_round_robin",
        ),
        avalai=settings,
    )
    transport = AssetAwareTransport()

    def feed_factory(spec: FeedSourceSpec, timeout_seconds: int) -> FakeFeedClient:
        assert timeout_seconds == 30
        return FakeFeedClient(spec, payloads[spec.source_id], observed)

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
        maximum_new_semantic_records=maximum_records,
    )
    return transport


def test_phase3i_health_reconciles_source_diversity_and_pending_backlog(
    tmp_path: Path,
) -> None:
    observed = datetime(2026, 7, 18, 12, tzinfo=UTC)
    alpha = _source("alpha-source", "BTC", 0.9, 2)
    beta = _source("beta-source", "MARKET", 0.8, 2)
    transport = _capture(
        tmp_path,
        sources=(alpha, beta),
        payloads={
            "alpha-source": RSS_ALPHA_TWO,
            "beta-source": RSS_BETA_TWO,
        },
        observed=observed,
        maximum_records=2,
    )
    assessment = assess_phase3i_source_health(
        tmp_path,
        assessed_at=observed + timedelta(minutes=5),
        policy=Phase3ISourceHealthPolicy(
            minimum_document_sources=2,
            minimum_semantic_sources=2,
            minimum_semantic_assets=2,
        ),
    )

    assert transport.calls == 2
    assert assessment.status == "pass"
    assert assessment.total_document_count == 4
    assert assessment.total_semantic_record_count == 2
    assert assessment.total_pending_semantic_document_count == 2
    assert assessment.document_source_count == 2
    assert assessment.semantic_source_count == 2
    assert assessment.semantic_assets == ("BTC", "MARKET")
    assert assessment.metadata_drift_sources == ()
    assert assessment.zero_accepted_sources_called == ()
    assert all(record.pending_semantic_document_count == 1 for record in assessment.source_records)


def test_phase3i_health_detects_metadata_drift_across_new_documents(tmp_path: Path) -> None:
    first_time = datetime(2026, 7, 18, 12, tzinfo=UTC)
    first_source = _source("drift-source", "BTC", 0.9, 1)
    second_source = _source("drift-source", "BTC", 0.7, 1)
    _capture(
        tmp_path,
        sources=(first_source,),
        payloads={"drift-source": RSS_DRIFT_ONE},
        observed=first_time,
        maximum_records=1,
    )
    _capture(
        tmp_path,
        sources=(second_source,),
        payloads={"drift-source": RSS_DRIFT_TWO},
        observed=first_time + timedelta(hours=1),
        maximum_records=1,
    )
    assessment = assess_phase3i_source_health(
        tmp_path,
        assessed_at=first_time + timedelta(hours=2),
        policy=Phase3ISourceHealthPolicy(
            minimum_document_sources=1,
            minimum_semantic_sources=1,
            minimum_semantic_assets=1,
        ),
    )

    assert assessment.status == "fail"
    assert assessment.metadata_drift_sources == ("drift-source",)
    assert "source_metadata_drift_detected" in assessment.failure_reasons
    assert assessment.source_records[0].source_metadata_variant_count == 2
