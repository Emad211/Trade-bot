from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.feed_source import FeedFetchResult, parse_feed
from hybrid_trader.source_admission import (
    SourceAdmissionPolicy,
    SourceAdmissionResult,
    probe_source,
    write_admission_report,
)

VALID_RSS = b"""<rss><channel>
<item>
<title>Policy update</title>
<link>https://example.com/releases/1</link>
<pubDate>Fri, 17 Jul 2026 10:00:00 GMT</pubDate>
<description>Official public update.</description>
</item>
<item>
<title>Second update</title>
<link>https://example.com/releases/2</link>
<pubDate>Fri, 17 Jul 2026 09:00:00 GMT</pubDate>
<description>Another official update.</description>
</item>
</channel></rss>"""

OUTSIDE_DOMAIN_RSS = b"""<rss><channel>
<item>
<title>Untrusted link</title>
<link>https://evil.example/releases/1</link>
<pubDate>Fri, 17 Jul 2026 10:00:00 GMT</pubDate>
</item>
</channel></rss>"""

FUTURE_RSS = b"""<rss><channel>
<item>
<title>Future dated item</title>
<link>https://example.com/releases/future</link>
<pubDate>Sat, 18 Jul 2026 10:00:00 GMT</pubDate>
</item>
</channel></rss>"""


def _source(*, asset_tags: tuple[str, ...] = ("BTC",)) -> FeedSourceSpec:
    return FeedSourceSpec(
        source_id="official-source",
        feed_url="https://example.com/feed.xml",
        allowed_domains=("example.com",),
        source_quality=0.9,
        asset_tags=asset_tags,
        required=False,
        max_items=50,
    )


class FakeClient:
    def __init__(
        self,
        spec: FeedSourceSpec,
        payload: bytes | Exception,
    ) -> None:
        self.spec = spec
        self.payload = payload

    def fetch(self, *, retrieved_at: datetime | None = None) -> FeedFetchResult:
        if isinstance(self.payload, Exception):
            raise self.payload
        if retrieved_at is None:
            raise AssertionError("Admission tests require a fixed observation time")
        parsed = parse_feed(self.payload, self.spec, retrieved_at=retrieved_at)
        return FeedFetchResult(
            source_id=self.spec.source_id,
            feed_url=self.spec.feed_url,
            retrieved_at=retrieved_at,
            payload=self.payload,
            payload_sha256=hashlib.sha256(self.payload).hexdigest(),
            parse_result=parsed,
        )


def _factory(payload: bytes | Exception):
    def factory(spec: FeedSourceSpec, timeout_seconds: int) -> FakeClient:
        assert timeout_seconds == 30
        return FakeClient(spec, payload)

    return factory


def _observed() -> datetime:
    return datetime(2026, 7, 17, 12, tzinfo=UTC)


def test_valid_public_feed_is_accepted_without_state_mutation(tmp_path: Path) -> None:
    result, payload = probe_source(
        _source(),
        observed_at=_observed(),
        feed_factory=_factory(VALID_RSS),
    )
    assert result.status == "accepted"
    assert result.failure_reasons == ()
    assert result.parsed_documents == 2
    assert result.documents_with_published_at == 2
    assert result.published_timestamp_ratio == 1.0
    assert result.unique_document_id_count == 2
    assert result.unique_canonical_url_count == 2
    assert result.longitudinal_state_modified is False
    assert payload == VALID_RSS
    assert not (tmp_path / "state").exists()

    report_path = write_admission_report(result, tmp_path / "reports")
    stored = SourceAdmissionResult.model_validate_json(report_path.read_text())
    assert stored == result
    checksum_line = (tmp_path / "reports" / "official-source.sha256").read_text().strip()
    expected = hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert checksum_line == f"{expected}  official-source.json"


def test_outside_domain_and_high_skip_ratio_are_rejected() -> None:
    result, _ = probe_source(
        _source(),
        observed_at=_observed(),
        feed_factory=_factory(OUTSIDE_DOMAIN_RSS),
    )
    assert result.status == "rejected"
    assert "insufficient_documents" in result.failure_reasons
    assert "skipped_fraction_exceeded" in result.failure_reasons
    assert "rejected_warning_observed" in result.failure_reasons
    assert result.warning_counts["entry_domain_not_allowed"] == 1


def test_future_publication_and_unsupported_asset_fail_closed() -> None:
    result, _ = probe_source(
        _source(asset_tags=("ETH",)),
        observed_at=_observed(),
        feed_factory=_factory(FUTURE_RSS),
    )
    assert result.status == "rejected"
    assert "asset_policy_failed" in result.failure_reasons
    assert "rejected_warning_observed" in result.failure_reasons
    assert "insufficient_published_timestamp_coverage" in result.failure_reasons
    assert result.warning_counts["published_time_beyond_clock_skew"] == 1


def test_retrieval_failure_is_audited_and_secret_free() -> None:
    secret = "not-for-persistence"
    result, payload = probe_source(
        _source(),
        observed_at=_observed(),
        feed_factory=_factory(RuntimeError(f"offline {secret}")),
    )
    assert result.status == "rejected"
    assert result.failure_reasons == ("retrieval_or_parse_failed",)
    assert result.error_type == "RuntimeError"
    assert result.error_message == f"offline {secret}"
    assert payload is None
    serialized = result.model_dump_json()
    assert "authorization" not in serialized.lower()


def test_strict_policy_rejects_low_timestamp_coverage() -> None:
    rss = VALID_RSS.replace(
        b"<pubDate>Fri, 17 Jul 2026 09:00:00 GMT</pubDate>",
        b"",
    )
    result, _ = probe_source(
        _source(),
        policy=SourceAdmissionPolicy(minimum_published_timestamp_ratio=0.75),
        observed_at=_observed(),
        feed_factory=_factory(rss),
    )
    assert result.status == "rejected"
    assert result.documents_with_published_at == 1
    assert result.published_timestamp_ratio == 0.5
    assert "insufficient_published_timestamp_coverage" in result.failure_reasons


def test_observation_time_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        probe_source(
            _source(),
            observed_at=datetime(2026, 7, 17, 12),
            feed_factory=_factory(VALID_RSS),
        )


def test_admission_id_changes_with_probe_time() -> None:
    first, _ = probe_source(
        _source(),
        observed_at=_observed(),
        feed_factory=_factory(VALID_RSS),
    )
    second, _ = probe_source(
        _source(),
        observed_at=_observed() + timedelta(hours=1),
        feed_factory=_factory(VALID_RSS),
    )
    assert first.admission_id != second.admission_id
    assert json.loads(first.model_dump_json())["status"] == "accepted"
