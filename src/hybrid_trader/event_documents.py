"""Compatibility facade for prospective event document contracts."""

from __future__ import annotations

from typing import Any

from hybrid_trader.event_identity import (
    document_identity_payload,
)
from hybrid_trader.event_identity import (
    make_document_id as _make_document_id,
)
from hybrid_trader.event_source_spec import FeedSourceSpec
from hybrid_trader.event_url import canonicalize_url, url_is_allowed
from hybrid_trader.prospective_document import DocumentEnvelope, ProspectiveDocument

__all__ = [
    "DocumentEnvelope",
    "FeedSourceSpec",
    "ProspectiveDocument",
    "canonicalize_url",
    "document_identity_payload",
    "make_document_id",
    "url_is_allowed",
]


def make_document_id(**payload: Any) -> str:
    """Preserve the original keyword-call API for existing feed adapters."""

    normalized = {str(key): None if value is None else str(value) for key, value in payload.items()}
    return _make_document_id(normalized)
