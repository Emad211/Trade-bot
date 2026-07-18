"""Validated public-feed source contracts for prospective event capture."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.event_url import (
    canonical_hostname,
    canonicalize_url,
    url_is_allowed,
    validate_public_hostname,
)

_WHITESPACE = re.compile(r"\s+")


def _normalize_relevance_term(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return _WHITESPACE.sub(" ", normalized).strip()


class FeedRelevanceSpec(BaseModel):
    """Deterministic title/summary filter applied before semantic inference."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    include_any_terms: tuple[str, ...] = ()
    exclude_any_terms: tuple[str, ...] = ()

    @field_validator("include_any_terms", "exclude_any_terms")
    @classmethod
    def normalize_terms(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_normalize_relevance_term(term) for term in value)
        if any(not term for term in normalized):
            raise ValueError("Relevance terms must be non-empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Relevance terms cannot contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_term_sets(self) -> FeedRelevanceSpec:
        overlap = set(self.include_any_terms).intersection(self.exclude_any_terms)
        if overlap:
            raise ValueError(
                f"Relevance include/exclude terms overlap: {sorted(overlap)}"
            )
        return self


class FeedSourceSpec(BaseModel):
    """Predeclared public feed and trust metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$")
    feed_url: str
    allowed_domains: tuple[str, ...]
    source_quality: float = Field(ge=0, le=1)
    asset_tags: tuple[str, ...] = ()
    required: bool = False
    max_items: int = Field(default=100, ge=1, le=1000)
    maximum_payload_bytes: int = Field(default=5_000_000, ge=1_024, le=50_000_000)
    maximum_clock_skew_seconds: int = Field(default=900, ge=0, le=86_400)
    relevance: FeedRelevanceSpec | None = None

    @field_validator("feed_url")
    @classmethod
    def validate_feed_url(cls, value: str) -> str:
        normalized = canonicalize_url(value)
        if not normalized.startswith("https://"):
            raise ValueError("Feed URLs must use HTTPS")
        return normalized

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        for raw in value:
            domain = canonical_hostname(raw)
            if any(character in domain for character in ("/", ":", "*", "@")):
                raise ValueError(
                    "allowed_domains must contain host names without wildcards or ports"
                )
            validate_public_hostname(domain)
            normalized.append(domain)
        result = tuple(normalized)
        if not result:
            raise ValueError("allowed_domains cannot be empty")
        if len(set(result)) != len(result):
            raise ValueError("allowed_domains cannot contain duplicates")
        return result

    @field_validator("asset_tags")
    @classmethod
    def validate_asset_tags(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(tag.upper().strip() for tag in value)
        if any(not tag for tag in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("asset_tags must be unique non-empty values")
        return normalized

    @model_validator(mode="after")
    def validate_feed_host(self) -> FeedSourceSpec:
        hostname = canonical_hostname(urlsplit(self.feed_url).hostname or "")
        validate_public_hostname(hostname)
        if not url_is_allowed(self.feed_url, self.allowed_domains):
            raise ValueError("feed_url host must be covered by allowed_domains")
        return self
