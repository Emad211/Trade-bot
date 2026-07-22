"""Owner-controlled private retention contract for synchronized OKX sampling batches."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from hybrid_trader.replication.revocable_retention import (
    ActiveLease,
    DeletionReceipt,
    PrivateRevocableArtifactStore,
)

ALLOWED_SOURCE_IDS = (
    "OKX_SPOT_BTC_USDT_TICKER",
    "OKX_SWAP_BTC_USDT_SWAP_TICKER",
    "OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE",
    "OKX_BTC_USDT_INDEX_TICKER",
)
MAX_SOURCE_BYTES = 1_000_000
MAX_BATCH_BYTES = 4_000_000
MAX_SAMPLING_RETENTION_DAYS = 7
MAX_PROVIDER_FUTURE_SKEW_MS = 5_000


class OKXPrivateSamplingError(RuntimeError):
    """Raised when a private synchronized sampling batch violates its contract."""


class SamplingExecutionMode(StrEnum):
    SYNTHETIC_VALIDATION = "SYNTHETIC_VALIDATION"
    OWNER_CONTROLLED_REAL = "OWNER_CONTROLLED_REAL"


@dataclass(frozen=True)
class OwnerSamplingAuthorization:
    """Explicit terms and execution attestations for one sampling operation."""

    terms_reviewed: bool
    personal_noncommercial_use: bool
    reasonable_rate_and_scale: bool
    redistribution_disabled: bool
    owner_controlled_private_storage: bool
    owner_controlled_encryption_keys: bool
    real_execution_owner_confirmed: bool

    def validate(self, *, mode: SamplingExecutionMode) -> None:
        common = {
            "terms_reviewed": self.terms_reviewed,
            "personal_noncommercial_use": self.personal_noncommercial_use,
            "reasonable_rate_and_scale": self.reasonable_rate_and_scale,
            "redistribution_disabled": self.redistribution_disabled,
        }
        missing = [name for name, value in common.items() if value is not True]
        if missing:
            raise OKXPrivateSamplingError(
                "Sampling authorization is incomplete: " + ", ".join(missing)
            )
        if mode == SamplingExecutionMode.OWNER_CONTROLLED_REAL:
            real = {
                "owner_controlled_private_storage": self.owner_controlled_private_storage,
                "owner_controlled_encryption_keys": self.owner_controlled_encryption_keys,
                "real_execution_owner_confirmed": self.real_execution_owner_confirmed,
            }
            missing_real = [name for name, value in real.items() if value is not True]
            if missing_real:
                raise OKXPrivateSamplingError(
                    "Real sampling requires owner-controlled execution attestations: "
                    + ", ".join(missing_real)
                )
        elif self.real_execution_owner_confirmed:
            raise OKXPrivateSamplingError(
                "Synthetic validation cannot claim real owner-side execution"
            )


@dataclass(frozen=True)
class SamplingClock:
    request_started_at: datetime
    response_received_at: datetime
    provider_timestamp_ms: int
    research_available_at: datetime

    def validate(self) -> None:
        request = _aware_utc(self.request_started_at, field="request_started_at")
        response = _aware_utc(self.response_received_at, field="response_received_at")
        available = _aware_utc(self.research_available_at, field="research_available_at")
        if not request <= response <= available:
            raise OKXPrivateSamplingError(
                "Sampling clocks must satisfy request <= response <= research available"
            )
        if self.provider_timestamp_ms < 10**12 or self.provider_timestamp_ms >= 10**14:
            raise OKXPrivateSamplingError("provider_timestamp_ms is not milliseconds")
        response_ms = int(response.timestamp() * 1000)
        if self.provider_timestamp_ms > response_ms + MAX_PROVIDER_FUTURE_SKEW_MS:
            raise OKXPrivateSamplingError(
                "Provider timestamp exceeds the allowed future-skew guard"
            )


@dataclass(frozen=True)
class SafeSamplingSourceLease:
    source_id: str
    artifact_id: str
    raw_sha256: str
    byte_count: int
    source_object_key_sha256: str
    request_started_at: str
    response_received_at: str
    provider_timestamp_ms: int
    provider_timestamp_utc: str
    provider_timestamp_age_ms_at_response: int
    research_available_at: str
    created_at_utc: str
    expires_at_utc: str
    raw_values_publicly_retained: bool


@dataclass(frozen=True)
class SafeSamplingBatchManifest:
    schema_version: str
    contract_id: str
    batch_id: str
    execution_mode: str
    synthetic_validation_only: bool
    real_raw_sampling_executed: bool
    source_count: int
    source_order: tuple[str, ...]
    sources: tuple[SafeSamplingSourceLease, ...]
    total_byte_count: int
    registry_committed_at: str
    requested_retention_days: int
    policy_id: str
    license_snapshot_id: str
    owner_controlled_private_storage_attested: bool
    owner_controlled_encryption_keys_attested: bool
    public_manifest_contains_market_values: bool
    public_raw_artifact_authorized: bool
    redistribution_authorized: bool
    basis_computation_authorized: bool
    funding_pnl_computation_authorized: bool
    returns_computation_authorized: bool
    transaction_cost_estimation_authorized: bool
    empirical_fitting_authorized: bool
    paper_or_live_trading_authorized: bool
    report_2_4_authorized: bool


@dataclass(frozen=True)
class SafeSamplingDeletionRecord:
    source_id: str
    artifact_id: str
    integrity_matched_before_delete: bool
    raw_exists_after_delete: bool
    lease_exists_after_delete: bool
    secure_erase_claimed: bool


@dataclass(frozen=True)
class SafeSamplingBatchDeletionReceipt:
    schema_version: str
    batch_id: str
    delete_reason: str
    deleted_at_utc: str
    source_count: int
    sources: tuple[SafeSamplingDeletionRecord, ...]
    all_raw_deleted: bool
    all_leases_deleted: bool
    secure_erase_claimed: bool


def _aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OKXPrivateSamplingError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _iso_utc(value: datetime) -> str:
    return _aware_utc(value, field="timestamp").isoformat()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _sha256(payload)


def _source_object_key(source_id: str, clock: SamplingClock) -> str:
    return _canonical_sha256(
        {
            "source_id": source_id,
            "request_started_at": _iso_utc(clock.request_started_at),
            "response_received_at": _iso_utc(clock.response_received_at),
            "provider_timestamp_ms": clock.provider_timestamp_ms,
            "research_available_at": _iso_utc(clock.research_available_at),
        }
    )


def _validate_source_sets(
    raw_by_source: Mapping[str, bytes], clocks_by_source: Mapping[str, SamplingClock]
) -> None:
    expected = set(ALLOWED_SOURCE_IDS)
    raw_ids = set(raw_by_source)
    clock_ids = set(clocks_by_source)
    if raw_ids != expected:
        raise OKXPrivateSamplingError(
            f"Raw source set must equal the frozen four-source contract; missing={sorted(expected - raw_ids)}, unknown={sorted(raw_ids - expected)}"
        )
    if clock_ids != expected:
        raise OKXPrivateSamplingError(
            f"Clock source set must equal the frozen four-source contract; missing={sorted(expected - clock_ids)}, unknown={sorted(clock_ids - expected)}"
        )


def _safe_source_record(lease: ActiveLease, clock: SamplingClock) -> SafeSamplingSourceLease:
    response = _aware_utc(clock.response_received_at, field="response_received_at")
    provider = datetime.fromtimestamp(clock.provider_timestamp_ms / 1000, tz=UTC)
    return SafeSamplingSourceLease(
        source_id=lease.source_id,
        artifact_id=lease.artifact_id,
        raw_sha256=lease.raw_sha256,
        byte_count=lease.byte_count,
        source_object_key_sha256=lease.source_object_key_sha256,
        request_started_at=_iso_utc(clock.request_started_at),
        response_received_at=_iso_utc(response),
        provider_timestamp_ms=clock.provider_timestamp_ms,
        provider_timestamp_utc=_iso_utc(provider),
        provider_timestamp_age_ms_at_response=(
            int(response.timestamp() * 1000) - clock.provider_timestamp_ms
        ),
        research_available_at=_iso_utc(clock.research_available_at),
        created_at_utc=lease.created_at_utc,
        expires_at_utc=lease.expires_at_utc,
        raw_values_publicly_retained=False,
    )


def retain_sampling_batch(
    *,
    store: PrivateRevocableArtifactStore,
    raw_by_source: Mapping[str, bytes],
    clocks_by_source: Mapping[str, SamplingClock],
    authorization: OwnerSamplingAuthorization,
    execution_mode: SamplingExecutionMode,
    requested_retention_days: int,
    now: datetime,
) -> SafeSamplingBatchManifest:
    """Atomically retain exactly four source responses under owner-only leases."""

    created_at = _aware_utc(now, field="now")
    authorization.validate(mode=execution_mode)
    _validate_source_sets(raw_by_source, clocks_by_source)
    if not 1 <= requested_retention_days <= MAX_SAMPLING_RETENTION_DAYS:
        raise OKXPrivateSamplingError(
            f"requested_retention_days must be between 1 and {MAX_SAMPLING_RETENTION_DAYS}"
        )
    if requested_retention_days > store.policy.maximum_retention_days:
        raise OKXPrivateSamplingError("requested retention exceeds the store policy")

    total_bytes = 0
    for source_id in ALLOWED_SOURCE_IDS:
        raw = raw_by_source[source_id]
        if not raw:
            raise OKXPrivateSamplingError(f"Raw response is empty for {source_id}")
        if len(raw) > MAX_SOURCE_BYTES:
            raise OKXPrivateSamplingError(
                f"Raw response exceeds the per-source byte guard for {source_id}"
            )
        total_bytes += len(raw)
        clocks_by_source[source_id].validate()
    if total_bytes > MAX_BATCH_BYTES:
        raise OKXPrivateSamplingError("Sampling batch exceeds the total byte guard")
    if any(
        _aware_utc(clock.research_available_at, field="research_available_at") > created_at
        for clock in clocks_by_source.values()
    ):
        raise OKXPrivateSamplingError(
            "registry commit time cannot precede a source research_available_at"
        )

    retained: list[ActiveLease] = []
    try:
        for source_id in ALLOWED_SOURCE_IDS:
            clock = clocks_by_source[source_id]
            retained.append(
                store.retain(
                    raw_by_source[source_id],
                    source_id=source_id,
                    source_object_key_sha256=_source_object_key(source_id, clock),
                    requested_retention_days=requested_retention_days,
                    now=created_at,
                )
            )
    except BaseException as exc:
        rollback_errors: list[str] = []
        for lease in reversed(retained):
            try:
                store.delete(
                    lease.artifact_id,
                    reason="BATCH_ROLLBACK",
                    now=created_at,
                )
            except BaseException as rollback_exc:
                rollback_errors.append(f"{lease.artifact_id}:{type(rollback_exc).__name__}")
        if rollback_errors:
            raise OKXPrivateSamplingError(
                "Sampling batch failed and rollback was incomplete: " + ", ".join(rollback_errors)
            ) from exc
        raise OKXPrivateSamplingError("Sampling batch failed and was rolled back") from exc

    source_records = tuple(
        _safe_source_record(lease, clocks_by_source[lease.source_id]) for lease in retained
    )
    batch_id = f"sha256-{_canonical_sha256([asdict(record) for record in source_records])}"
    manifest = SafeSamplingBatchManifest(
        schema_version="1.0",
        contract_id="OKX_PRIVATE_SYNCHRONIZED_PRICE_SAMPLING_V1",
        batch_id=batch_id,
        execution_mode=execution_mode.value,
        synthetic_validation_only=(execution_mode == SamplingExecutionMode.SYNTHETIC_VALIDATION),
        real_raw_sampling_executed=(execution_mode == SamplingExecutionMode.OWNER_CONTROLLED_REAL),
        source_count=len(source_records),
        source_order=ALLOWED_SOURCE_IDS,
        sources=source_records,
        total_byte_count=total_bytes,
        registry_committed_at=_iso_utc(created_at),
        requested_retention_days=requested_retention_days,
        policy_id=store.policy.policy_id,
        license_snapshot_id=store.policy.license_snapshot_id,
        owner_controlled_private_storage_attested=(authorization.owner_controlled_private_storage),
        owner_controlled_encryption_keys_attested=(authorization.owner_controlled_encryption_keys),
        public_manifest_contains_market_values=False,
        public_raw_artifact_authorized=False,
        redistribution_authorized=False,
        basis_computation_authorized=False,
        funding_pnl_computation_authorized=False,
        returns_computation_authorized=False,
        transaction_cost_estimation_authorized=False,
        empirical_fitting_authorized=False,
        paper_or_live_trading_authorized=False,
        report_2_4_authorized=False,
    )
    assert_sampling_batch_compliant(store=store, manifest=manifest, now=created_at)
    return manifest


def assert_sampling_batch_compliant(
    *,
    store: PrivateRevocableArtifactStore,
    manifest: SafeSamplingBatchManifest,
    now: datetime,
) -> None:
    snapshot = store.assert_compliant(now=now)
    expected_ids = tuple(record.artifact_id for record in manifest.sources)
    if not set(expected_ids).issubset(snapshot.active_artifact_ids):
        raise OKXPrivateSamplingError(
            "Sampling batch artifacts are not all active in the private store"
        )


def delete_sampling_batch(
    *,
    store: PrivateRevocableArtifactStore,
    manifest: SafeSamplingBatchManifest,
    reason: str,
    now: datetime,
) -> SafeSamplingBatchDeletionReceipt:
    deleted_at = _aware_utc(now, field="now")
    if not reason.strip():
        raise OKXPrivateSamplingError("Deletion reason cannot be empty")
    receipts: list[DeletionReceipt] = []
    for source in manifest.sources:
        receipts.append(store.delete(source.artifact_id, reason=reason, now=deleted_at))
    safe_records = tuple(
        SafeSamplingDeletionRecord(
            source_id=receipt.source_id,
            artifact_id=receipt.artifact_id,
            integrity_matched_before_delete=receipt.integrity_matched_before_delete,
            raw_exists_after_delete=receipt.raw_exists_after_delete,
            lease_exists_after_delete=receipt.lease_exists_after_delete,
            secure_erase_claimed=receipt.secure_erase_claimed,
        )
        for receipt in receipts
    )
    result = SafeSamplingBatchDeletionReceipt(
        schema_version="1.0",
        batch_id=manifest.batch_id,
        delete_reason=reason.strip(),
        deleted_at_utc=_iso_utc(deleted_at),
        source_count=len(safe_records),
        sources=safe_records,
        all_raw_deleted=all(not item.raw_exists_after_delete for item in safe_records),
        all_leases_deleted=all(not item.lease_exists_after_delete for item in safe_records),
        secure_erase_claimed=False,
    )
    if not result.all_raw_deleted or not result.all_leases_deleted:
        raise OKXPrivateSamplingError("Sampling batch deletion did not complete")
    return result


def safe_manifest_json(manifest: SafeSamplingBatchManifest) -> str:
    return json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n"
