"""Deterministic admission gates for prospective public event sources."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hybrid_trader.data.snapshot import canonical_json_sha256
from hybrid_trader.event_documents import FeedSourceSpec
from hybrid_trader.feed_source import FeedFetchResult, PublicFeedSource

_ALLOWED_ASSET_TAGS = frozenset({"BTC", "MARKET"})
_DEFAULT_REJECTED_WARNINGS = (
    "entry_domain_not_allowed",
    "published_time_beyond_clock_skew",
)


class SourceAdmissionPolicy(BaseModel):
    """Frozen quality limits applied before a source may enter longitudinal capture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum_documents: int = Field(default=1, ge=1, le=1000)
    minimum_published_timestamp_ratio: float = Field(default=0.50, ge=0, le=1)
    maximum_skipped_fraction: float = Field(default=0.25, ge=0, le=1)
    maximum_duplicate_count: int = Field(default=5, ge=0, le=1000)
    maximum_truncated_count: int = Field(default=1000, ge=0, le=100_000)
    rejected_warnings: tuple[str, ...] = _DEFAULT_REJECTED_WARNINGS
    allowed_asset_tags: tuple[str, ...] = ("BTC", "MARKET")

    @field_validator("rejected_warnings")
    @classmethod
    def normalize_warnings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip() for item in value)
        if any(not item for item in normalized):
            raise ValueError("Rejected warning names cannot be empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Rejected warning names cannot contain duplicates")
        return normalized

    @field_validator("allowed_asset_tags")
    @classmethod
    def normalize_assets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip().upper() for item in value)
        if not normalized or any(not item for item in normalized):
            raise ValueError("At least one allowed asset tag is required")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Allowed asset tags cannot contain duplicates")
        unsupported = set(normalized).difference(_ALLOWED_ASSET_TAGS)
        if unsupported:
            raise ValueError(f"Unsupported source-admission assets: {sorted(unsupported)}")
        return normalized


class SourceAdmissionResult(BaseModel):
    """Machine-readable accepted/rejected verdict for one public feed probe."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    admission_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    feed_url: str
    asset_tags: tuple[str, ...]
    observed_at: datetime
    status: Literal["accepted", "rejected"]
    policy: SourceAdmissionPolicy
    payload_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    payload_bytes: int = Field(default=0, ge=0)
    parsed_documents: int = Field(default=0, ge=0)
    documents_with_published_at: int = Field(default=0, ge=0)
    published_timestamp_ratio: float = Field(default=0, ge=0, le=1)
    duplicate_count: int = Field(default=0, ge=0)
    skipped_count: int = Field(default=0, ge=0)
    truncated_count: int = Field(default=0, ge=0)
    skipped_fraction: float = Field(default=0, ge=0, le=1)
    warning_counts: dict[str, int] = Field(default_factory=dict)
    unique_document_id_count: int = Field(default=0, ge=0)
    unique_canonical_url_count: int = Field(default=0, ge=0)
    failure_reasons: tuple[str, ...] = ()
    error_type: str | None = None
    error_message: str | None = None
    longitudinal_state_modified: bool = False

    @field_validator("observed_at")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Source admission observation time must be timezone-aware")
        return value.astimezone(UTC)

    @field_validator("asset_tags")
    @classmethod
    def normalize_result_assets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(item.strip().upper() for item in value)

    @model_validator(mode="after")
    def validate_verdict(self) -> SourceAdmissionResult:
        expected = "accepted" if not self.failure_reasons else "rejected"
        if self.status != expected:
            raise ValueError("Source admission status disagrees with failure reasons")
        if self.status == "accepted" and (self.error_type or self.error_message):
            raise ValueError("Accepted source cannot contain retrieval error metadata")
        if self.longitudinal_state_modified:
            raise ValueError("Source admission probes cannot modify longitudinal state")
        expected_id = source_admission_id(
            source_id=self.source_id,
            feed_url=self.feed_url,
            asset_tags=self.asset_tags,
            observed_at=self.observed_at,
            policy=self.policy,
            payload_sha256=self.payload_sha256,
            parsed_documents=self.parsed_documents,
            failure_reasons=self.failure_reasons,
        )
        if self.admission_id != expected_id:
            raise ValueError("Source admission ID does not match probe provenance")
        return self


class FeedClient(Protocol):
    def fetch(self, *, retrieved_at: datetime | None = None) -> FeedFetchResult: ...


FeedFactory = Callable[[FeedSourceSpec, int], FeedClient]


def _default_feed_factory(spec: FeedSourceSpec, timeout_seconds: int) -> FeedClient:
    return PublicFeedSource(spec, timeout_seconds=timeout_seconds)


def source_admission_id(
    *,
    source_id: str,
    feed_url: str,
    asset_tags: tuple[str, ...],
    observed_at: datetime,
    policy: SourceAdmissionPolicy,
    payload_sha256: str | None,
    parsed_documents: int,
    failure_reasons: tuple[str, ...],
) -> str:
    return canonical_json_sha256(
        {
            "source_id": source_id,
            "feed_url": feed_url,
            "asset_tags": asset_tags,
            "observed_at": observed_at.astimezone(UTC).isoformat(),
            "policy": policy.model_dump(mode="json"),
            "payload_sha256": payload_sha256,
            "parsed_documents": parsed_documents,
            "failure_reasons": failure_reasons,
        }
    )


def _warning_counts(warnings: tuple[str, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for warning in warnings:
        counts[warning] = counts.get(warning, 0) + 1
    return dict(sorted(counts.items()))


def probe_source(
    spec: FeedSourceSpec,
    *,
    policy: SourceAdmissionPolicy | None = None,
    observed_at: datetime | None = None,
    timeout_seconds: int = 30,
    feed_factory: FeedFactory = _default_feed_factory,
) -> tuple[SourceAdmissionResult, bytes | None]:
    """Probe one public source without appending any document or semantic ledger."""

    declared_policy = policy or SourceAdmissionPolicy()
    observed = observed_at or datetime.now(UTC)
    if observed.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    observed = observed.astimezone(UTC)

    reasons: list[str] = []
    asset_tags = tuple(spec.asset_tags)
    allowed_assets = frozenset(declared_policy.allowed_asset_tags)
    if not asset_tags or not set(asset_tags).issubset(allowed_assets):
        reasons.append("asset_policy_failed")

    result: FeedFetchResult | None = None
    error_type: str | None = None
    error_message: str | None = None
    try:
        result = feed_factory(spec, timeout_seconds).fetch(retrieved_at=observed)
    except Exception as exc:
        reasons.append("retrieval_or_parse_failed")
        error_type = type(exc).__name__
        error_message = "Public feed retrieval or parsing failed"

    payload: bytes | None = None
    payload_sha: str | None = None
    payload_bytes = 0
    parsed_documents = 0
    published_count = 0
    published_ratio = 0.0
    duplicate_count = 0
    skipped_count = 0
    truncated_count = 0
    skipped_fraction = 0.0
    warnings: dict[str, int] = {}
    unique_document_ids = 0
    unique_urls = 0

    if result is not None:
        payload = result.payload
        payload_sha = result.payload_sha256
        payload_bytes = len(payload)
        parsed = result.parse_result
        parsed_documents = len(parsed.documents)
        published_count = sum(
            envelope.document.published_at is not None for envelope in parsed.documents
        )
        published_ratio = published_count / parsed_documents if parsed_documents else 0.0
        duplicate_count = parsed.duplicate_count
        skipped_count = parsed.skipped_count
        truncated_count = parsed.truncated_count
        denominator = parsed_documents + skipped_count + duplicate_count
        skipped_fraction = skipped_count / denominator if denominator else 0.0
        warnings = _warning_counts(parsed.warnings)
        unique_document_ids = len({envelope.document.document_id for envelope in parsed.documents})
        unique_urls = len({envelope.document.canonical_url for envelope in parsed.documents})

        if result.source_id != spec.source_id or result.feed_url != spec.feed_url:
            reasons.append("fetch_identity_mismatch")
        if parsed_documents < declared_policy.minimum_documents:
            reasons.append("insufficient_documents")
        if published_ratio < declared_policy.minimum_published_timestamp_ratio:
            reasons.append("insufficient_published_timestamp_coverage")
        if skipped_fraction > declared_policy.maximum_skipped_fraction:
            reasons.append("skipped_fraction_exceeded")
        if duplicate_count > declared_policy.maximum_duplicate_count:
            reasons.append("duplicate_count_exceeded")
        if truncated_count > declared_policy.maximum_truncated_count:
            reasons.append("truncated_count_exceeded")
        rejected_warnings = set(warnings).intersection(declared_policy.rejected_warnings)
        if rejected_warnings:
            reasons.append("rejected_warning_observed")
        if unique_document_ids != parsed_documents:
            reasons.append("document_id_uniqueness_failed")
        if unique_urls != parsed_documents:
            reasons.append("canonical_url_uniqueness_failed")
        for envelope in parsed.documents:
            document = envelope.document
            if document.source_id != spec.source_id:
                reasons.append("document_source_identity_failed")
                break
            if document.available_at != result.retrieved_at:
                reasons.append("availability_contract_failed")
                break
            if document.retrieved_at != result.retrieved_at:
                reasons.append("retrieval_contract_failed")
                break
            if document.available_at < observed:
                reasons.append("availability_precedes_probe")
                break
            if document.feed_payload_sha256 != payload_sha:
                reasons.append("payload_provenance_failed")
                break

    failure_reasons = tuple(sorted(set(reasons)))
    admission = SourceAdmissionResult(
        admission_id=source_admission_id(
            source_id=spec.source_id,
            feed_url=spec.feed_url,
            asset_tags=asset_tags,
            observed_at=observed,
            policy=declared_policy,
            payload_sha256=payload_sha,
            parsed_documents=parsed_documents,
            failure_reasons=failure_reasons,
        ),
        source_id=spec.source_id,
        feed_url=spec.feed_url,
        asset_tags=asset_tags,
        observed_at=observed,
        status="accepted" if not failure_reasons else "rejected",
        policy=declared_policy,
        payload_sha256=payload_sha,
        payload_bytes=payload_bytes,
        parsed_documents=parsed_documents,
        documents_with_published_at=published_count,
        published_timestamp_ratio=published_ratio,
        duplicate_count=duplicate_count,
        skipped_count=skipped_count,
        truncated_count=truncated_count,
        skipped_fraction=skipped_fraction,
        warning_counts=warnings,
        unique_document_id_count=unique_document_ids,
        unique_canonical_url_count=unique_urls,
        failure_reasons=failure_reasons,
        error_type=error_type,
        error_message=error_message,
    )
    return admission, payload


def write_admission_report(
    result: SourceAdmissionResult,
    directory: str | Path,
) -> Path:
    """Write deterministic, secret-free admission evidence and a checksum."""

    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / f"{result.source_id}.json"
    report_path.write_text(
        json.dumps(result.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(report_path.read_bytes()).hexdigest()
    (root / f"{result.source_id}.sha256").write_text(
        f"{checksum}  {report_path.name}\n",
        encoding="utf-8",
    )
    return report_path
