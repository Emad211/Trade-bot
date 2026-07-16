from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from hybrid_trader.event_documents import (
    FeedSourceSpec,
    ProspectiveDocument,
    canonicalize_url,
    document_identity_payload,
    make_document_id,
    url_is_allowed,
)
from hybrid_trader.feed_source import PublicFeedSource, parse_feed


def _source_spec(**updates: object) -> FeedSourceSpec:
    payload: dict[str, object] = {
        "source_id": "official-feed",
        "feed_url": "https://example.com/feed.xml",
        "allowed_domains": ("example.com",),
        "source_quality": 0.9,
        "asset_tags": ("BTC",),
        "max_items": 10,
    }
    payload.update(updates)
    return FeedSourceSpec.model_validate(payload)


def test_event_urls_are_canonical_and_feed_hosts_are_constrained() -> None:
    value = canonicalize_url(
        "HTTPS://Example.COM:443/releases/?utm_source=x&b=2&a=1#fragment"
    )
    assert value == "https://example.com/releases?a=1&b=2"
    assert url_is_allowed(value, ("example.com",))
    assert url_is_allowed("https://sub.example.com/a", ("example.com",))
    assert not url_is_allowed("https://notexample.com/a", ("example.com",))
    with pytest.raises(ValueError, match="User information"):
        canonicalize_url("https://user:secret@example.com/feed")
    with pytest.raises(ValidationError, match="localhost"):
        FeedSourceSpec(
            source_id="unsafe-source",
            feed_url="https://localhost/feed.xml",
            allowed_domains=("localhost",),
            source_quality=0.5,
        )
    with pytest.raises(ValidationError, match="allowed_domains"):
        FeedSourceSpec(
            source_id="wrong-domain",
            feed_url="https://example.com/feed.xml",
            allowed_domains=("other.example",),
            source_quality=0.5,
        )


def test_document_id_is_self_verifying() -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    title = "Release 2.0"
    encoded = title.encode()
    content_hash = hashlib.sha256(encoded).hexdigest()
    payload = document_identity_payload(
        source_id="source-one",
        canonical_url="https://example.com/release/2",
        title=title,
        published_at=observed,
        content_sha256=content_hash,
    )
    document = ProspectiveDocument(
        document_id=make_document_id(**payload),
        source_id="source-one",
        canonical_url="https://example.com/release/2",
        title=title,
        published_at=observed,
        retrieved_at=observed,
        available_at=observed,
        source_quality=0.9,
        asset_tags=("btc",),
        content_sha256=content_hash,
        content_length=len(encoded),
        feed_payload_sha256="a" * 64,
    )
    assert document.asset_tags == ("BTC",)
    with pytest.raises(ValidationError, match="document_id"):
        ProspectiveDocument.model_validate({**document.model_dump(), "document_id": "0" * 64})
    with pytest.raises(ValidationError, match="retrieval time"):
        ProspectiveDocument.model_validate(
            {**document.model_dump(), "available_at": observed.replace(hour=11)}
        )


def test_rss_parsing_uses_retrieval_time_and_deduplicates() -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    payload = b"""<?xml version='1.0'?>
    <rss><channel>
      <item><title>Release 1.0</title><link>https://example.com/r/1?utm_source=x</link>
        <pubDate>Thu, 16 Jul 2026 09:00:00 GMT</pubDate>
        <description><![CDATA[<b>Upgrade</b><script>ignore()</script> details]]></description>
      </item>
      <item><title>Release 1.0</title><link>https://example.com/r/1</link>
        <pubDate>Thu, 16 Jul 2026 09:00:00 GMT</pubDate>
        <description><![CDATA[<b>Upgrade</b><script>ignore()</script> details]]></description>
      </item>
    </channel></rss>"""
    result = parse_feed(payload, _source_spec(), retrieved_at=observed)
    assert len(result.documents) == 1
    assert result.duplicate_count == 1
    envelope = result.documents[0]
    assert envelope.document.available_at == observed
    assert envelope.document.canonical_url == "https://example.com/r/1"
    assert "ignore" not in envelope.text
    assert "Upgrade details" in envelope.text


def test_atom_parsing_handles_nested_content_future_time_and_domain_filter() -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    future = (observed + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    payload = f"""<feed xmlns='http://www.w3.org/2005/Atom'>
      <entry><title>Future release</title><link href='/release/2'/>
        <updated>{future}</updated><content type='html'><div>Nested <b>content</b></div></content>
      </entry>
      <entry><title>Offsite</title><link href='https://evil.example/item'/></entry>
    </feed>""".encode()
    result = parse_feed(
        payload,
        _source_spec(maximum_clock_skew_seconds=30),
        retrieved_at=observed,
    )
    assert len(result.documents) == 1
    assert result.documents[0].document.published_at is None
    assert result.documents[0].text.endswith("Nested content")
    assert result.skipped_count == 1
    assert "entry_domain_not_allowed" in result.warnings
    assert "published_time_beyond_clock_skew" in result.warnings


def test_public_feed_source_accepts_an_injected_downloader() -> None:
    observed = datetime(2026, 7, 16, 10, tzinfo=UTC)
    payload = b"<rss><channel><item><title>A</title><link>https://example.com/a</link></item></channel></rss>"
    calls: list[tuple[str, int, int]] = []

    def downloader(url: str, timeout: int, maximum: int) -> bytes:
        calls.append((url, timeout, maximum))
        return payload

    result = PublicFeedSource(_source_spec(), timeout_seconds=7).fetch(
        retrieved_at=observed,
        downloader=downloader,
    )
    assert result.retrieved_at == observed
    assert calls == [("https://example.com/feed.xml", 7, 5_000_000)]
