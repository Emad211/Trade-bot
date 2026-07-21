"""Prospective-only, append-only OKX source and instrument registry contracts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

SHA256_PATTERN = r"^[0-9a-f]{64}$"


class OKXProspectiveRegistryError(RuntimeError):
    """Raised when a prospective observation violates the append-only contract."""


class AvailabilitySemantics(StrEnum):
    """Meaning assigned to the first observed prospective timestamp."""

    FIRST_OBSERVED_NOT_PROVIDER_EFFECTIVE = "FIRST_OBSERVED_NOT_PROVIDER_EFFECTIVE"


class SourceHealthStatus(StrEnum):
    SUCCESS = "SUCCESS"
    HTTP_ERROR = "HTTP_ERROR"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    CONTRACT_ERROR = "CONTRACT_ERROR"


class ObservationClock(BaseModel):
    """Separate request, response, provider, research, and commit clocks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_started_at: datetime
    response_received_at: datetime
    provider_timestamp: datetime | None = None
    research_available_at: datetime
    registry_committed_at: datetime

    @model_validator(mode="after")
    def validate_clock_order(self) -> ObservationClock:
        request = _aware_utc(self.request_started_at, field="request_started_at")
        response = _aware_utc(self.response_received_at, field="response_received_at")
        available = _aware_utc(self.research_available_at, field="research_available_at")
        committed = _aware_utc(self.registry_committed_at, field="registry_committed_at")
        if not request <= response <= available <= committed:
            raise ValueError(
                "observation clocks must satisfy request <= response <= available <= commit"
            )
        if self.provider_timestamp is not None:
            provider = _aware_utc(self.provider_timestamp, field="provider_timestamp")
            if provider > response:
                raise ValueError("provider_timestamp cannot follow response_received_at")
        return self


class SourceHealthObservation(BaseModel):
    """Non-sensitive source-health evidence for one prospective request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: SourceHealthStatus
    http_status: int | None = Field(default=None, ge=100, le=599)
    application_code: str | None = None
    latency_milliseconds: int = Field(ge=0)
    response_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    error_fingerprint_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    raw_error_retained: bool = False

    @model_validator(mode="after")
    def validate_status_contract(self) -> SourceHealthObservation:
        if self.raw_error_retained:
            raise ValueError("raw errors cannot be retained in the prospective registry")
        if self.status == SourceHealthStatus.SUCCESS:
            if self.http_status != 200 or self.response_sha256 is None:
                raise ValueError(
                    "successful health observations require HTTP 200 and a response hash"
                )
            if self.error_fingerprint_sha256 is not None:
                raise ValueError("successful observations cannot carry an error fingerprint")
        else:
            if self.error_fingerprint_sha256 is None:
                raise ValueError("failed observations require an error fingerprint")
        return self


class ProspectiveInstrumentContent(BaseModel):
    """Content-addressed current instrument version without historical promotion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    official_host: str = Field(min_length=1)
    endpoint_path: str = Field(min_length=1)
    response_byte_count: int = Field(gt=0)
    response_sha256: str = Field(pattern=SHA256_PATTERN)
    schema_fields: tuple[str, ...]
    schema_sha256: str = Field(pattern=SHA256_PATTERN)
    selected_fields: dict[str, str]
    provider_time_fields: dict[str, str | None]
    raw_response_retained: bool = False
    historical_effective_from: datetime | None = None
    effective_from_semantics: AvailabilitySemantics = (
        AvailabilitySemantics.FIRST_OBSERVED_NOT_PROVIDER_EFFECTIVE
    )

    @model_validator(mode="after")
    def validate_content_contract(self) -> ProspectiveInstrumentContent:
        if self.raw_response_retained:
            raise ValueError("raw instrument responses cannot be retained")
        if self.historical_effective_from is not None:
            raise ValueError("prospective content cannot define a historical effective_from")
        if not self.schema_fields or tuple(sorted(set(self.schema_fields))) != self.schema_fields:
            raise ValueError("schema_fields must be a non-empty sorted unique tuple")
        if not self.selected_fields:
            raise ValueError("selected_fields cannot be empty")
        if any(not key or value == "" for key, value in self.selected_fields.items()):
            raise ValueError("selected_fields require non-empty keys and values")
        if any(not key for key in self.provider_time_fields):
            raise ValueError("provider_time_fields cannot contain empty keys")
        return self

    @property
    def content_version_id(self) -> str:
        return _content_id("okx-instrument-content-v1", self.model_dump(mode="json"))


class ProspectiveFundingSourceContent(BaseModel):
    """Safe funding-source profile without rate values or ordered row retention."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    official_host: str = Field(min_length=1)
    endpoint_path: str = Field(min_length=1)
    request_fingerprint_sha256: str = Field(pattern=SHA256_PATTERN)
    response_byte_count: int = Field(gt=0)
    response_sha256: str = Field(pattern=SHA256_PATTERN)
    schema_fields: tuple[str, ...]
    schema_sha256: str = Field(pattern=SHA256_PATTERN)
    row_count: int = Field(gt=0)
    unique_provider_timestamps: int = Field(gt=0)
    minimum_provider_timestamp_ms: int = Field(gt=0)
    maximum_provider_timestamp_ms: int = Field(gt=0)
    interval_seconds_counts: tuple[tuple[int, int], ...]
    raw_response_retained: bool = False
    funding_rate_values_retained: bool = False
    ordered_timestamp_series_retained: bool = False

    @model_validator(mode="after")
    def validate_safe_profile(self) -> ProspectiveFundingSourceContent:
        if (
            self.raw_response_retained
            or self.funding_rate_values_retained
            or self.ordered_timestamp_series_retained
        ):
            raise ValueError("prospective public evidence must not retain raw funding data")
        if self.unique_provider_timestamps > self.row_count:
            raise ValueError("unique_provider_timestamps cannot exceed row_count")
        if self.minimum_provider_timestamp_ms > self.maximum_provider_timestamp_ms:
            raise ValueError("minimum provider timestamp cannot exceed maximum")
        if not self.schema_fields or tuple(sorted(set(self.schema_fields))) != self.schema_fields:
            raise ValueError("schema_fields must be a non-empty sorted unique tuple")
        if tuple(sorted(set(self.interval_seconds_counts))) != self.interval_seconds_counts:
            raise ValueError("interval_seconds_counts must be sorted and unique")
        if any(interval <= 0 or count <= 0 for interval, count in self.interval_seconds_counts):
            raise ValueError("interval counts require positive intervals and counts")
        return self

    @property
    def content_version_id(self) -> str:
        return _content_id("okx-funding-source-content-v1", self.model_dump(mode="json"))


class ProspectiveRegistryObservation(BaseModel):
    """One immutable observation of a content-addressed source version."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_clock: ObservationClock
    content_kind: str = Field(pattern=r"^(INSTRUMENT|FUNDING_SOURCE)$")
    content_version_id: str = Field(pattern=SHA256_PATTERN)
    previous_observation_id: str | None = Field(default=None, pattern=SHA256_PATTERN)
    changed_fields: tuple[str, ...] = ()
    source_health: SourceHealthObservation
    historical_backfill: bool = False
    historical_effective_time_inferred: bool = False
    basis_computation_authorized: bool = False
    funding_pnl_computation_authorized: bool = False
    returns_computation_authorized: bool = False
    empirical_fitting_authorized: bool = False
    paper_or_live_trading_authorized: bool = False

    @model_validator(mode="after")
    def validate_observation_contract(self) -> ProspectiveRegistryObservation:
        if self.historical_backfill or self.historical_effective_time_inferred:
            raise ValueError("prospective registry observations cannot backfill history")
        if tuple(sorted(set(self.changed_fields))) != self.changed_fields:
            raise ValueError("changed_fields must be sorted and unique")
        if any(
            (
                self.basis_computation_authorized,
                self.funding_pnl_computation_authorized,
                self.returns_computation_authorized,
                self.empirical_fitting_authorized,
                self.paper_or_live_trading_authorized,
            )
        ):
            raise ValueError("the prospective registry cannot authorize economic testing")
        return self

    @property
    def observation_id(self) -> str:
        return _content_id("okx-prospective-observation-v1", self.model_dump(mode="json"))


class AppendResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observations: tuple[ProspectiveRegistryObservation, ...]
    appended_observation_id: str
    content_version_changed: bool


def diff_selected_fields(
    previous: Mapping[str, str],
    current: Mapping[str, str],
) -> tuple[str, ...]:
    """Return sorted field names whose presence or value changed."""

    keys = set(previous) | set(current)
    return tuple(sorted(key for key in keys if previous.get(key) != current.get(key)))


def diff_safe_values(
    previous: Any,
    current: Any,
    *,
    prefix: str = "",
) -> tuple[str, ...]:
    """Return stable dotted paths for safe metadata changes."""

    path = prefix or "$"
    if isinstance(previous, Mapping) and isinstance(current, Mapping):
        changes: list[str] = []
        for key in sorted(set(previous) | set(current), key=str):
            child = f"{prefix}.{key}" if prefix else str(key)
            if key not in previous or key not in current:
                changes.append(child)
            else:
                changes.extend(diff_safe_values(previous[key], current[key], prefix=child))
        return tuple(changes)
    if (
        isinstance(previous, Sequence)
        and not isinstance(previous, (str, bytes, bytearray))
        and isinstance(current, Sequence)
        and not isinstance(current, (str, bytes, bytearray))
    ):
        return () if list(previous) == list(current) else (path,)
    return () if previous == current else (path,)


def tail_by_content_kind(
    observations: Sequence[ProspectiveRegistryObservation],
    *,
    content_kind: str,
) -> ProspectiveRegistryObservation:
    """Return the last observation in one source stream."""

    matches = [item for item in observations if item.content_kind == content_kind]
    if not matches:
        raise OKXProspectiveRegistryError(f"registry has no observations for {content_kind!r}")
    return matches[-1]


def append_observation(
    existing: Sequence[ProspectiveRegistryObservation],
    observation: ProspectiveRegistryObservation,
) -> AppendResult:
    """Append one observation without overwriting, reordering, or duplicating."""

    observation_id = observation.observation_id
    if any(item.observation_id == observation_id for item in existing):
        raise OKXProspectiveRegistryError("observation identity already exists")
    if any(item.content_kind != observation.content_kind for item in existing):
        raise OKXProspectiveRegistryError(
            "append_observation accepts exactly one content-kind stream"
        )
    if existing:
        previous = existing[-1]
        previous_time = previous.observation_clock.registry_committed_at.astimezone(UTC)
        current_time = observation.observation_clock.registry_committed_at.astimezone(UTC)
        if current_time <= previous_time:
            raise OKXProspectiveRegistryError("registry_committed_at must increase monotonically")
        if observation.previous_observation_id != previous.observation_id:
            raise OKXProspectiveRegistryError(
                "previous_observation_id must reference the registry tail"
            )
        changed = previous.content_version_id != observation.content_version_id
        if changed and not observation.changed_fields:
            raise OKXProspectiveRegistryError(
                "content version changes require a non-empty field diff"
            )
        if not changed and observation.changed_fields:
            raise OKXProspectiveRegistryError("unchanged content cannot declare changed fields")
    else:
        if observation.previous_observation_id is not None:
            raise OKXProspectiveRegistryError(
                "the first observation cannot reference a predecessor"
            )
        changed = True
    return AppendResult(
        observations=(*tuple(existing), observation),
        appended_observation_id=observation_id,
        content_version_changed=changed,
    )


def _aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _content_id(namespace: str, value: Any) -> str:
    canonical = json.dumps(
        {"namespace": namespace, "value": value},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
