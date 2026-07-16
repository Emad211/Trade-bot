"""Credential-free RSS/Atom retrieval with prospective availability semantics."""

from __future__ import annotations

import hashlib
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

from hybrid_trader.event_documents import (
    DocumentEnvelope,
    FeedSourceSpec,
    ProspectiveDocument,
    canonicalize_url,
    document_identity_payload,
    make_document_id,
    url_is_allowed,
)

Downloader = Callable[[str, int, int], bytes]


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _strip_markup(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1].lower()


def _child_text(element: ET.Element, names: tuple[str, ...]) -> str | None:
    wanted = set(names)
    for child in element:
        if _local_name(child.tag) in wanted and child.text:
            value = child.text.strip()
            if value:
                return value
    return None


def _entry_link(element: ET.Element, *, feed_url: str) -> str | None:
    for child in element:
        if _local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        relation = child.attrib.get("rel", "alternate")
        if href and relation in {"alternate", ""}:
            return urljoin(feed_url, href)
        if child.text and child.text.strip():
            return urljoin(feed_url, child.text.strip())
    identifier = _child_text(element, ("id", "guid"))
    if identifier and identifier.startswith(("https://", "http://")):
        return identifier
    return None


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _default_downloader(url: str, timeout_seconds: int, maximum_bytes: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml",
            "User-Agent": "HybridTraderProspectiveEvents/1.0 (+https://github.com/Emad211/Trade-bot)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        declared_length = response.headers.get("Content-Length")
        if declared_length is not None and int(declared_length) > maximum_bytes:
            raise ValueError("Feed payload exceeds the configured maximum size")
        payload = response.read(maximum_bytes + 1)
    if len(payload) > maximum_bytes:
        raise ValueError("Feed payload exceeds the configured maximum size")
    return payload


@dataclass(frozen=True)
class FeedParseResult:
    documents: tuple[DocumentEnvelope, ...]
    duplicate_count: int
    skipped_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class FeedFetchResult:
    source_id: str
    feed_url: str
    retrieved_at: datetime
    payload: bytes
    payload_sha256: str
    parse_result: FeedParseResult


def parse_feed(
    payload: bytes,
    spec: FeedSourceSpec,
    *,
    retrieved_at: datetime,
) -> FeedParseResult:
    """Parse RSS/Atom bytes without assigning availability before retrieval."""

    if retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    retrieved = retrieved_at.astimezone(UTC)
    if len(payload) > spec.maximum_payload_bytes:
        raise ValueError("Feed payload exceeds the configured maximum size")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML feed for {spec.source_id}") from exc

    payload_sha = hashlib.sha256(payload).hexdigest()
    item_names = {"item", "entry"}
    entries = [element for element in root.iter() if _local_name(element.tag) in item_names]
    documents: list[DocumentEnvelope] = []
    seen_ids: set[str] = set()
    duplicate_count = 0
    skipped_count = 0
    warnings: list[str] = []
    clock_skew = timedelta(seconds=spec.maximum_clock_skew_seconds)

    for entry in entries[: spec.max_items]:
        title = _strip_markup(_child_text(entry, ("title",)) or "")
        raw_link = _entry_link(entry, feed_url=spec.feed_url)
        if not title or not raw_link:
            skipped_count += 1
            warnings.append("entry_missing_title_or_link")
            continue
        try:
            canonical_url = canonicalize_url(raw_link)
        except ValueError:
            skipped_count += 1
            warnings.append("entry_invalid_url")
            continue
        if not url_is_allowed(canonical_url, spec.allowed_domains):
            skipped_count += 1
            warnings.append("entry_domain_not_allowed")
            continue

        summary_raw = _child_text(entry, ("summary", "description", "content", "encoded")) or ""
        summary = _strip_markup(summary_raw)
        text = title if not summary else f"{title}\n\n{summary}"
        encoded = text.encode("utf-8")
        content_sha = hashlib.sha256(encoded).hexdigest()
        published_at = _parse_timestamp(
            _child_text(entry, ("published", "updated", "pubdate", "date"))
        )
        if published_at is not None and published_at > retrieved + clock_skew:
            warnings.append("published_time_beyond_clock_skew")
            published_at = None

        identity_payload = document_identity_payload(
            source_id=spec.source_id,
            canonical_url=canonical_url,
            title=title[:500],
            published_at=published_at,
            content_sha256=content_sha,
        )
        document_id = make_document_id(**identity_payload)
        if document_id in seen_ids:
            duplicate_count += 1
            continue
        seen_ids.add(document_id)
        document = ProspectiveDocument(
            document_id=document_id,
            source_id=spec.source_id,
            canonical_url=canonical_url,
            title=title[:500],
            published_at=published_at,
            retrieved_at=retrieved,
            available_at=retrieved,
            source_quality=spec.source_quality,
            asset_tags=spec.asset_tags,
            content_sha256=content_sha,
            content_length=len(encoded),
            feed_payload_sha256=payload_sha,
        )
        documents.append(DocumentEnvelope(document=document, text=text))

    return FeedParseResult(
        documents=tuple(documents),
        duplicate_count=duplicate_count,
        skipped_count=skipped_count,
        warnings=tuple(sorted(warnings)),
    )


class PublicFeedSource:
    def __init__(self, spec: FeedSourceSpec, *, timeout_seconds: int = 30) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.spec = spec
        self.timeout_seconds = timeout_seconds

    def fetch(
        self,
        *,
        retrieved_at: datetime | None = None,
        downloader: Downloader = _default_downloader,
    ) -> FeedFetchResult:
        observed_at = (retrieved_at or datetime.now(UTC)).astimezone(UTC)
        payload = downloader(
            self.spec.feed_url,
            self.timeout_seconds,
            self.spec.maximum_payload_bytes,
        )
        parsed = parse_feed(payload, self.spec, retrieved_at=observed_at)
        return FeedFetchResult(
            source_id=self.spec.source_id,
            feed_url=self.spec.feed_url,
            retrieved_at=observed_at,
            payload=payload,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            parse_result=parsed,
        )
