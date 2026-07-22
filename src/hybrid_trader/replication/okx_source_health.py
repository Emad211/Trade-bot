"""Fail-closed OKX source-health, sequence, staleness, and sampling-abort contracts."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
DEPRECATED_CHECKSUM_CHANNELS = frozenset({"books", "books-l2-tbt", "books50-l2-tbt"})
RATE_LIMIT_CODE = "50011"
SERVICE_UPGRADE_CODE = "64008"


class SourceHealthError(RuntimeError):
    """Raised when a health policy or batch contract is invalid."""


class SourceHealthState(StrEnum):
    HEALTHY = "HEALTHY"
    HEARTBEAT_NO_BOOK_CHANGE = "HEARTBEAT_NO_BOOK_CHANGE"
    STALE_PROVIDER_TIME = "STALE_PROVIDER_TIME"
    FUTURE_PROVIDER_TIME = "FUTURE_PROVIDER_TIME"
    RESEARCH_DELAY_EXCEEDED = "RESEARCH_DELAY_EXCEEDED"
    CLOCK_INVALID = "CLOCK_INVALID"
    RATE_LIMITED = "RATE_LIMITED"
    HTTP_ERROR = "HTTP_ERROR"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    CONNECTION_SILENT = "CONNECTION_SILENT"
    SERVICE_UPGRADE_DRAIN = "SERVICE_UPGRADE_DRAIN"
    SEQUENCE_GAP = "SEQUENCE_GAP"
    SEQUENCE_REGRESSION = "SEQUENCE_REGRESSION"
    SCHEMA_CHANGED = "SCHEMA_CHANGED"
    IDENTITY_CHANGED = "IDENTITY_CHANGED"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    PARTIAL_SOURCE_SET = "PARTIAL_SOURCE_SET"
    DUPLICATE_SOURCE = "DUPLICATE_SOURCE"
    CROSS_SOURCE_SKEW_EXCEEDED = "CROSS_SOURCE_SKEW_EXCEEDED"
    POLICY_VERSION_MISMATCH = "POLICY_VERSION_MISMATCH"
    QUARANTINED = "QUARANTINED"


class BatchDecision(StrEnum):
    ADMIT_PRIVATE_BATCH = "ADMIT_PRIVATE_BATCH"
    REJECT_BATCH = "REJECT_BATCH"
    QUARANTINE_INCIDENT = "QUARANTINE_INCIDENT"


class BookAction(StrEnum):
    SNAPSHOT = "snapshot"
    UPDATE = "update"
    NOTICE = "notice"


def _require_aware(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SourceHealthError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_sha(value: str, *, field: str) -> str:
    if HEX_SHA256.fullmatch(value) is None:
        raise SourceHealthError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _whole_milliseconds(delta: timedelta) -> int:
    """Return exact whole milliseconds without floating-point boundary drift."""
    return delta // timedelta(milliseconds=1)


@dataclass(frozen=True)
class SourceHealthPolicy:
    policy_id: str
    maximum_provider_age_ms: int
    maximum_future_clock_skew_ms: int
    maximum_response_to_research_delay_ms: int
    maximum_websocket_silence_seconds: float
    maximum_cross_source_provider_time_skew_ms: int
    required_source_ids: tuple[str, ...]
    expected_schema_sha256: Mapping[str, str]
    expected_identity_sha256: Mapping[str, str]
    checksum_deprecation_effective_at: datetime
    sequence_validation_mode: str
    rate_limit_backoff_policy_id: str

    def validate(self) -> None:
        if not self.policy_id.strip():
            raise SourceHealthError("policy_id cannot be empty")
        if not self.rate_limit_backoff_policy_id.strip():
            raise SourceHealthError("rate_limit_backoff_policy_id cannot be empty")
        for field, threshold_value in (
            ("maximum_provider_age_ms", self.maximum_provider_age_ms),
            ("maximum_future_clock_skew_ms", self.maximum_future_clock_skew_ms),
            (
                "maximum_response_to_research_delay_ms",
                self.maximum_response_to_research_delay_ms,
            ),
            (
                "maximum_cross_source_provider_time_skew_ms",
                self.maximum_cross_source_provider_time_skew_ms,
            ),
        ):
            if threshold_value < 0:
                raise SourceHealthError(f"{field} must be non-negative")
        if not 0 < self.maximum_websocket_silence_seconds < 30:
            raise SourceHealthError(
                "maximum_websocket_silence_seconds must be explicit and below 30"
            )
        if not self.required_source_ids:
            raise SourceHealthError("required_source_ids cannot be empty")
        if len(set(self.required_source_ids)) != len(self.required_source_ids):
            raise SourceHealthError("required_source_ids must be unique")
        if tuple(sorted(self.required_source_ids)) != self.required_source_ids:
            raise SourceHealthError("required_source_ids must be sorted")
        required = set(self.required_source_ids)
        if set(self.expected_schema_sha256) != required:
            raise SourceHealthError("schema fingerprints must match required sources")
        if set(self.expected_identity_sha256) != required:
            raise SourceHealthError("identity fingerprints must match required sources")
        for source_id, schema_fingerprint in self.expected_schema_sha256.items():
            _validate_sha(schema_fingerprint, field=f"schema fingerprint for {source_id}")
        for source_id, identity_fingerprint in self.expected_identity_sha256.items():
            _validate_sha(identity_fingerprint, field=f"identity fingerprint for {source_id}")
        _require_aware(
            self.checksum_deprecation_effective_at,
            field="checksum_deprecation_effective_at",
        )
        if self.sequence_validation_mode != "SEQ_ID_PREV_SEQ_ID":
            raise SourceHealthError("unsupported sequence validation mode")

    @property
    def policy_fingerprint_sha256(self) -> str:
        self.validate()
        payload = {
            "policy_id": self.policy_id,
            "maximum_provider_age_ms": self.maximum_provider_age_ms,
            "maximum_future_clock_skew_ms": self.maximum_future_clock_skew_ms,
            "maximum_response_to_research_delay_ms": (self.maximum_response_to_research_delay_ms),
            "maximum_websocket_silence_seconds": self.maximum_websocket_silence_seconds,
            "maximum_cross_source_provider_time_skew_ms": (
                self.maximum_cross_source_provider_time_skew_ms
            ),
            "required_source_ids": self.required_source_ids,
            "expected_schema_sha256": dict(sorted(self.expected_schema_sha256.items())),
            "expected_identity_sha256": dict(sorted(self.expected_identity_sha256.items())),
            "checksum_deprecation_effective_at": self.checksum_deprecation_effective_at.astimezone(
                UTC
            ).isoformat(),
            "sequence_validation_mode": self.sequence_validation_mode,
            "rate_limit_backoff_policy_id": self.rate_limit_backoff_policy_id,
        }
        return _canonical_sha256(payload)


@dataclass(frozen=True)
class RestObservation:
    source_id: str
    request_started_at: datetime
    response_received_at: datetime
    provider_timestamp: datetime
    research_available_at: datetime
    http_status: int
    provider_code: str
    row_count: int
    response_sha256: str
    schema_sha256: str
    identity_sha256: str
    transport_error_fingerprint_sha256: str | None = None

    def validate_fingerprints(self) -> None:
        _validate_sha(self.response_sha256, field="response_sha256")
        _validate_sha(self.schema_sha256, field="schema_sha256")
        _validate_sha(self.identity_sha256, field="identity_sha256")
        if self.transport_error_fingerprint_sha256 is not None:
            _validate_sha(
                self.transport_error_fingerprint_sha256,
                field="transport_error_fingerprint_sha256",
            )


@dataclass(frozen=True)
class RestHealthResult:
    source_id: str
    state: SourceHealthState
    admitted: bool
    quarantine_required: bool
    provider_timestamp: datetime
    research_available_at: datetime
    provider_age_ms: int
    future_skew_ms: int
    research_delay_ms: int
    policy_id: str
    policy_fingerprint_sha256: str
    response_sha256: str
    schema_sha256: str
    identity_sha256: str
    raw_response_retained: bool = False
    market_values_retained: bool = False
    carry_forward_used: bool = False
    interpolation_used: bool = False


@dataclass(frozen=True)
class BookMessage:
    channel: str
    instrument_id: str
    action: BookAction
    seq_id: int
    prev_seq_id: int
    asks_count: int
    bids_count: int
    provider_timestamp: datetime
    received_at: datetime
    checksum: int | None = None
    notice_code: str | None = None


@dataclass(frozen=True)
class BookHealthResult:
    state: SourceHealthState
    admitted_as_new_book_data: bool
    stream_live: bool
    reconnect_required: bool
    next_sequence_id: int | None
    checksum_deprecated: bool
    checksum_used_for_integrity: bool
    sequence_authoritative: bool
    raw_book_retained: bool = False
    market_values_retained: bool = False


@dataclass(frozen=True)
class BatchAdmissionResult:
    decision: BatchDecision
    state: SourceHealthState
    policy_id: str
    source_ids: tuple[str, ...]
    cross_source_provider_time_skew_ms: int | None
    provider_timestamps_monotonic_in_input_order: bool | None
    carry_forward_used: bool = False
    interpolation_used: bool = False
    rejected_data_retained: bool = False
    numerical_calculation_authorized: bool = False


@dataclass(frozen=True)
class IncidentRecord:
    incident_id: str
    source_id: str
    state: SourceHealthState
    policy_id: str
    policy_fingerprint_sha256: str
    observed_at: datetime
    response_sha256: str | None
    schema_sha256: str | None
    identity_sha256: str | None
    error_fingerprint_sha256: str | None
    raw_payload_retained: bool = False
    market_values_retained: bool = False
    price_null_created: bool = False
    carry_forward_used: bool = False
    interpolation_used: bool = False


def evaluate_rest_observation(
    observation: RestObservation,
    *,
    policy: SourceHealthPolicy,
) -> RestHealthResult:
    policy.validate()
    observation.validate_fingerprints()
    policy_fingerprint = policy.policy_fingerprint_sha256

    request = _require_aware(observation.request_started_at, field="request_started_at")
    response = _require_aware(observation.response_received_at, field="response_received_at")
    provider = _require_aware(observation.provider_timestamp, field="provider_timestamp")
    research = _require_aware(observation.research_available_at, field="research_available_at")

    provider_age_ms = _whole_milliseconds(response - provider)
    future_skew_ms = max(0, -provider_age_ms)
    research_delay_ms = _whole_milliseconds(research - response)

    state = SourceHealthState.HEALTHY
    quarantine = False
    if observation.transport_error_fingerprint_sha256 is not None:
        state = SourceHealthState.TRANSPORT_ERROR
    elif not request <= response <= research:
        state = SourceHealthState.CLOCK_INVALID
    elif observation.http_status != 200:
        state = SourceHealthState.HTTP_ERROR
    elif observation.provider_code == RATE_LIMIT_CODE:
        state = SourceHealthState.RATE_LIMITED
    elif observation.provider_code != "0":
        state = SourceHealthState.PROVIDER_ERROR
    elif observation.row_count <= 0:
        state = SourceHealthState.EMPTY_RESPONSE
    elif observation.source_id not in policy.required_source_ids:
        state = SourceHealthState.IDENTITY_CHANGED
        quarantine = True
    elif observation.schema_sha256 != policy.expected_schema_sha256[observation.source_id]:
        state = SourceHealthState.SCHEMA_CHANGED
        quarantine = True
    elif observation.identity_sha256 != policy.expected_identity_sha256[observation.source_id]:
        state = SourceHealthState.IDENTITY_CHANGED
        quarantine = True
    elif future_skew_ms > policy.maximum_future_clock_skew_ms:
        state = SourceHealthState.FUTURE_PROVIDER_TIME
    elif provider_age_ms > policy.maximum_provider_age_ms:
        state = SourceHealthState.STALE_PROVIDER_TIME
    elif research_delay_ms > policy.maximum_response_to_research_delay_ms:
        state = SourceHealthState.RESEARCH_DELAY_EXCEEDED

    return RestHealthResult(
        source_id=observation.source_id,
        state=state,
        admitted=state is SourceHealthState.HEALTHY,
        quarantine_required=quarantine,
        provider_timestamp=provider,
        research_available_at=research,
        provider_age_ms=provider_age_ms,
        future_skew_ms=future_skew_ms,
        research_delay_ms=research_delay_ms,
        policy_id=policy.policy_id,
        policy_fingerprint_sha256=policy_fingerprint,
        response_sha256=observation.response_sha256,
        schema_sha256=observation.schema_sha256,
        identity_sha256=observation.identity_sha256,
    )


def evaluate_book_message(
    message: BookMessage,
    *,
    previous_sequence_id: int | None,
    policy: SourceHealthPolicy,
) -> BookHealthResult:
    policy.validate()
    provider_time = _require_aware(message.provider_timestamp, field="provider_timestamp")
    _require_aware(message.received_at, field="received_at")

    if message.notice_code == SERVICE_UPGRADE_CODE or message.action is BookAction.NOTICE:
        return BookHealthResult(
            state=SourceHealthState.SERVICE_UPGRADE_DRAIN,
            admitted_as_new_book_data=False,
            stream_live=False,
            reconnect_required=True,
            next_sequence_id=previous_sequence_id,
            checksum_deprecated=False,
            checksum_used_for_integrity=False,
            sequence_authoritative=True,
        )

    checksum_deprecated = (
        message.channel in DEPRECATED_CHECKSUM_CHANNELS
        and provider_time >= policy.checksum_deprecation_effective_at.astimezone(UTC)
    )
    if message.channel in DEPRECATED_CHECKSUM_CHANNELS and not checksum_deprecated:
        return BookHealthResult(
            state=SourceHealthState.POLICY_VERSION_MISMATCH,
            admitted_as_new_book_data=False,
            stream_live=False,
            reconnect_required=True,
            next_sequence_id=previous_sequence_id,
            checksum_deprecated=False,
            checksum_used_for_integrity=False,
            sequence_authoritative=True,
        )

    if message.action is BookAction.SNAPSHOT:
        state = (
            SourceHealthState.HEALTHY
            if message.prev_seq_id == -1 and message.seq_id >= 0
            else SourceHealthState.SEQUENCE_GAP
        )
        return BookHealthResult(
            state=state,
            admitted_as_new_book_data=state is SourceHealthState.HEALTHY,
            stream_live=state is SourceHealthState.HEALTHY,
            reconnect_required=state is not SourceHealthState.HEALTHY,
            next_sequence_id=message.seq_id if state is SourceHealthState.HEALTHY else None,
            checksum_deprecated=checksum_deprecated,
            checksum_used_for_integrity=False,
            sequence_authoritative=True,
        )

    if previous_sequence_id is None:
        state = SourceHealthState.SEQUENCE_GAP
    elif (
        message.asks_count == 0
        and message.bids_count == 0
        and message.seq_id == previous_sequence_id
        and message.prev_seq_id == previous_sequence_id
    ):
        state = SourceHealthState.HEARTBEAT_NO_BOOK_CHANGE
    elif message.seq_id < previous_sequence_id:
        state = SourceHealthState.SEQUENCE_REGRESSION
    elif message.prev_seq_id != previous_sequence_id:
        state = SourceHealthState.SEQUENCE_GAP
    elif message.seq_id <= previous_sequence_id:
        state = SourceHealthState.SEQUENCE_REGRESSION
    else:
        state = SourceHealthState.HEALTHY

    return BookHealthResult(
        state=state,
        admitted_as_new_book_data=state is SourceHealthState.HEALTHY,
        stream_live=state
        in {SourceHealthState.HEALTHY, SourceHealthState.HEARTBEAT_NO_BOOK_CHANGE},
        reconnect_required=state
        not in {SourceHealthState.HEALTHY, SourceHealthState.HEARTBEAT_NO_BOOK_CHANGE},
        next_sequence_id=(
            message.seq_id
            if state in {SourceHealthState.HEALTHY, SourceHealthState.HEARTBEAT_NO_BOOK_CHANGE}
            else previous_sequence_id
        ),
        checksum_deprecated=checksum_deprecated,
        checksum_used_for_integrity=False,
        sequence_authoritative=True,
    )


def evaluate_websocket_silence(
    *,
    last_message_at: datetime,
    observed_at: datetime,
    policy: SourceHealthPolicy,
) -> BookHealthResult:
    policy.validate()
    last = _require_aware(last_message_at, field="last_message_at")
    now = _require_aware(observed_at, field="observed_at")
    if now < last:
        state = SourceHealthState.CLOCK_INVALID
    elif (now - last).total_seconds() > policy.maximum_websocket_silence_seconds:
        state = SourceHealthState.CONNECTION_SILENT
    else:
        state = SourceHealthState.HEALTHY
    return BookHealthResult(
        state=state,
        admitted_as_new_book_data=False,
        stream_live=state is SourceHealthState.HEALTHY,
        reconnect_required=state is not SourceHealthState.HEALTHY,
        next_sequence_id=None,
        checksum_deprecated=True,
        checksum_used_for_integrity=False,
        sequence_authoritative=True,
    )


def admit_sampling_batch(
    observations: Sequence[RestHealthResult],
    *,
    policy: SourceHealthPolicy,
) -> BatchAdmissionResult:
    policy.validate()
    source_ids = tuple(result.source_id for result in observations)
    counts = Counter(source_ids)
    if any(count > 1 for count in counts.values()):
        return BatchAdmissionResult(
            decision=BatchDecision.REJECT_BATCH,
            state=SourceHealthState.DUPLICATE_SOURCE,
            policy_id=policy.policy_id,
            source_ids=source_ids,
            cross_source_provider_time_skew_ms=None,
            provider_timestamps_monotonic_in_input_order=None,
        )
    if set(source_ids) != set(policy.required_source_ids):
        return BatchAdmissionResult(
            decision=BatchDecision.REJECT_BATCH,
            state=SourceHealthState.PARTIAL_SOURCE_SET,
            policy_id=policy.policy_id,
            source_ids=source_ids,
            cross_source_provider_time_skew_ms=None,
            provider_timestamps_monotonic_in_input_order=None,
        )
    for result in observations:
        if result.quarantine_required:
            return BatchAdmissionResult(
                decision=BatchDecision.QUARANTINE_INCIDENT,
                state=SourceHealthState.QUARANTINED,
                policy_id=policy.policy_id,
                source_ids=source_ids,
                cross_source_provider_time_skew_ms=None,
                provider_timestamps_monotonic_in_input_order=None,
            )
        if not result.admitted:
            return BatchAdmissionResult(
                decision=BatchDecision.REJECT_BATCH,
                state=result.state,
                policy_id=policy.policy_id,
                source_ids=source_ids,
                cross_source_provider_time_skew_ms=None,
                provider_timestamps_monotonic_in_input_order=None,
            )

    provider_values = [int(item.provider_timestamp.timestamp() * 1000) for item in observations]
    spread = max(provider_values) - min(provider_values)
    monotonic = provider_values == sorted(provider_values)
    if spread > policy.maximum_cross_source_provider_time_skew_ms:
        return BatchAdmissionResult(
            decision=BatchDecision.REJECT_BATCH,
            state=SourceHealthState.CROSS_SOURCE_SKEW_EXCEEDED,
            policy_id=policy.policy_id,
            source_ids=source_ids,
            cross_source_provider_time_skew_ms=spread,
            provider_timestamps_monotonic_in_input_order=monotonic,
        )
    return BatchAdmissionResult(
        decision=BatchDecision.ADMIT_PRIVATE_BATCH,
        state=SourceHealthState.HEALTHY,
        policy_id=policy.policy_id,
        source_ids=source_ids,
        cross_source_provider_time_skew_ms=spread,
        provider_timestamps_monotonic_in_input_order=monotonic,
    )


def build_incident_record(
    *,
    source_id: str,
    state: SourceHealthState,
    policy: SourceHealthPolicy,
    observed_at: datetime,
    response_sha256: str | None = None,
    schema_sha256: str | None = None,
    identity_sha256: str | None = None,
    error_fingerprint_sha256: str | None = None,
) -> IncidentRecord:
    policy.validate()
    observed = _require_aware(observed_at, field="observed_at")
    for field, value in (
        ("response_sha256", response_sha256),
        ("schema_sha256", schema_sha256),
        ("identity_sha256", identity_sha256),
        ("error_fingerprint_sha256", error_fingerprint_sha256),
    ):
        if value is not None:
            _validate_sha(value, field=field)
    incident_payload = {
        "source_id": source_id,
        "state": state.value,
        "policy_id": policy.policy_id,
        "observed_at": observed.isoformat(),
        "response_sha256": response_sha256,
        "schema_sha256": schema_sha256,
        "identity_sha256": identity_sha256,
        "error_fingerprint_sha256": error_fingerprint_sha256,
    }
    return IncidentRecord(
        incident_id=_canonical_sha256(incident_payload),
        source_id=source_id,
        state=state,
        policy_id=policy.policy_id,
        policy_fingerprint_sha256=policy.policy_fingerprint_sha256,
        observed_at=observed,
        response_sha256=response_sha256,
        schema_sha256=schema_sha256,
        identity_sha256=identity_sha256,
        error_fingerprint_sha256=error_fingerprint_sha256,
    )


def safe_incident_json(record: IncidentRecord) -> str:
    return json.dumps(asdict(record), default=str, indent=2, sort_keys=True) + "\n"
