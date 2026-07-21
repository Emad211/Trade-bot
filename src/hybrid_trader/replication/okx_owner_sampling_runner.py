"""Disabled-by-default owner-side runner for one private OKX sampling batch."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from hybrid_trader.replication.okx_price_linkage_probe import (
    SOURCE_CONTRACTS,
    TimedHTTPResponse,
    build_url,
    fetch_public_response,
    validate_source_response,
)
from hybrid_trader.replication.okx_private_sampling import (
    OwnerSamplingAuthorization,
    SafeSamplingBatchDeletionReceipt,
    SafeSamplingBatchManifest,
    SafeSamplingSourceLease,
    SamplingClock,
    SamplingExecutionMode,
    delete_sampling_batch,
    retain_sampling_batch,
    safe_manifest_json,
)
from hybrid_trader.replication.revocable_retention import (
    ALLOWED_PURPOSE,
    PrivateRevocableArtifactStore,
    RetentionAttestation,
    RetentionPolicy,
)

REAL_CONFIRMATION_PHRASE = "I_CONFIRM_OWNER_CONTROLLED_PRIVATE_OKX_RAW_SAMPLING"
SYNTHETIC_CONFIRMATION_PHRASE = "I_CONFIRM_SYNTHETIC_INJECTED_RESPONSES_ONLY"
DELETE_CONFIRMATION_PHRASE = "I_CONFIRM_DELETE_OWNER_CONTROLLED_OKX_RAW_BATCH"
DEFAULT_POLICY_ID = "OKX_LIVE_PRIVATE_SAMPLING_V1"
DEFAULT_LICENSE_SNAPSHOT_ID = "OKX_API_AGREEMENT_2026-03-26_REVIEWED_2026-07-21_V1"


class OwnerRunnerMode(StrEnum):
    SYNTHETIC_INJECTED = "SYNTHETIC_INJECTED"
    OWNER_REAL_NETWORK = "OWNER_REAL_NETWORK"


class OKXOwnerSamplingRunnerError(RuntimeError):
    """Raised when owner-side activation, storage, or output controls fail."""


@dataclass(frozen=True)
class OwnerRunnerAttestations:
    terms_reviewed: bool
    personal_noncommercial_use: bool
    reasonable_rate_and_scale: bool
    redistribution_disabled: bool
    encryption_at_rest: bool
    owner_only_access: bool
    backup_and_sync_excluded: bool
    public_artifact_upload_disabled: bool
    owner_controlled_private_storage: bool
    owner_controlled_encryption_keys: bool
    real_execution_owner_confirmed: bool


@dataclass(frozen=True)
class OwnerSamplingRunnerConfig:
    mode: OwnerRunnerMode
    private_root: Path
    repository_root: Path
    safe_manifest_output: Path
    requested_retention_days: int
    confirmation_phrase: str
    enable_real_network_fetch: bool
    attestations: OwnerRunnerAttestations
    policy_id: str = DEFAULT_POLICY_ID
    license_snapshot_id: str = DEFAULT_LICENSE_SNAPSHOT_ID

    def validate(self) -> None:
        if not self.policy_id.strip() or not self.license_snapshot_id.strip():
            raise OKXOwnerSamplingRunnerError("Policy and license snapshot IDs are required")
        if not 1 <= self.requested_retention_days <= 7:
            raise OKXOwnerSamplingRunnerError("requested_retention_days must be between 1 and 7")
        if self.safe_manifest_output.suffix.casefold() != ".json":
            raise OKXOwnerSamplingRunnerError("safe_manifest_output must be a JSON file")
        if self.safe_manifest_output.exists():
            raise OKXOwnerSamplingRunnerError("safe_manifest_output already exists")

        common = {
            "terms_reviewed": self.attestations.terms_reviewed,
            "personal_noncommercial_use": self.attestations.personal_noncommercial_use,
            "reasonable_rate_and_scale": self.attestations.reasonable_rate_and_scale,
            "redistribution_disabled": self.attestations.redistribution_disabled,
            "encryption_at_rest": self.attestations.encryption_at_rest,
            "owner_only_access": self.attestations.owner_only_access,
            "backup_and_sync_excluded": self.attestations.backup_and_sync_excluded,
            "public_artifact_upload_disabled": (
                self.attestations.public_artifact_upload_disabled
            ),
        }
        missing = [name for name, value in common.items() if value is not True]
        if missing:
            raise OKXOwnerSamplingRunnerError(
                "Owner runner attestations are incomplete: " + ", ".join(missing)
            )

        if self.mode == OwnerRunnerMode.OWNER_REAL_NETWORK:
            if self.confirmation_phrase != REAL_CONFIRMATION_PHRASE:
                raise OKXOwnerSamplingRunnerError("Exact real-execution confirmation is required")
            if not self.enable_real_network_fetch:
                raise OKXOwnerSamplingRunnerError("Real network fetch is disabled")
            real = {
                "owner_controlled_private_storage": (
                    self.attestations.owner_controlled_private_storage
                ),
                "owner_controlled_encryption_keys": (
                    self.attestations.owner_controlled_encryption_keys
                ),
                "real_execution_owner_confirmed": (
                    self.attestations.real_execution_owner_confirmed
                ),
            }
            missing_real = [name for name, value in real.items() if value is not True]
            if missing_real:
                raise OKXOwnerSamplingRunnerError(
                    "Real owner-side execution attestations are incomplete: "
                    + ", ".join(missing_real)
                )
        else:
            if self.confirmation_phrase != SYNTHETIC_CONFIRMATION_PHRASE:
                raise OKXOwnerSamplingRunnerError(
                    "Exact synthetic-execution confirmation is required"
                )
            if self.enable_real_network_fetch:
                raise OKXOwnerSamplingRunnerError(
                    "Synthetic mode cannot enable real network fetch"
                )
            if self.attestations.real_execution_owner_confirmed:
                raise OKXOwnerSamplingRunnerError(
                    "Synthetic mode cannot claim real owner execution"
                )

        private_root = self.private_root.expanduser().resolve(strict=False)
        repository_root = self.repository_root.expanduser().resolve(strict=False)
        safe_output = self.safe_manifest_output.expanduser().resolve(strict=False)
        if safe_output == private_root or safe_output.is_relative_to(private_root):
            raise OKXOwnerSamplingRunnerError(
                "Safe manifest must be outside the private raw storage tree"
            )
        if private_root == repository_root or private_root.is_relative_to(repository_root):
            raise OKXOwnerSamplingRunnerError(
                "Private raw storage must be outside the repository tree"
            )


@dataclass(frozen=True)
class OwnerSamplingRunResult:
    mode: str
    real_okx_request_performed: bool
    real_raw_sampling_executed: bool
    batch_id: str
    source_count: int
    safe_manifest_output: str
    safe_manifest_byte_count: int
    safe_manifest_sha256: str
    private_artifact_count: int


@dataclass(frozen=True)
class OwnerSamplingDeletionConfig:
    private_root: Path
    repository_root: Path
    safe_manifest_path: Path
    safe_deletion_receipt_output: Path
    confirmation_phrase: str
    reason: str
    attestations: OwnerRunnerAttestations

    def validate(self) -> None:
        if self.confirmation_phrase != DELETE_CONFIRMATION_PHRASE:
            raise OKXOwnerSamplingRunnerError("Exact deletion confirmation is required")
        if not self.reason.strip():
            raise OKXOwnerSamplingRunnerError("Deletion reason cannot be empty")
        if not self.safe_manifest_path.is_file():
            raise OKXOwnerSamplingRunnerError("Safe manifest does not exist")
        if self.safe_deletion_receipt_output.suffix.casefold() != ".json":
            raise OKXOwnerSamplingRunnerError(
                "safe_deletion_receipt_output must be a JSON file"
            )
        if self.safe_deletion_receipt_output.exists():
            raise OKXOwnerSamplingRunnerError(
                "safe_deletion_receipt_output already exists"
            )
        required = {
            "owner_only_access": self.attestations.owner_only_access,
            "public_artifact_upload_disabled": (
                self.attestations.public_artifact_upload_disabled
            ),
        }
        missing = [name for name, value in required.items() if value is not True]
        if missing:
            raise OKXOwnerSamplingRunnerError(
                "Deletion attestations are incomplete: " + ", ".join(missing)
            )


def _atomic_write(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _store_from_config(config: OwnerSamplingRunnerConfig) -> PrivateRevocableArtifactStore:
    return PrivateRevocableArtifactStore(
        config.private_root,
        repository_root=config.repository_root,
        policy=RetentionPolicy(
            policy_id=config.policy_id,
            license_snapshot_id=config.license_snapshot_id,
            allowed_purpose=ALLOWED_PURPOSE,
            maximum_retention_days=7,
        ),
        attestation=RetentionAttestation(
            encryption_at_rest=config.attestations.encryption_at_rest,
            owner_only_access=config.attestations.owner_only_access,
            backup_and_sync_excluded=config.attestations.backup_and_sync_excluded,
            public_artifact_upload_disabled=(
                config.attestations.public_artifact_upload_disabled
            ),
        ),
    )


def _authorization_from_config(
    config: OwnerSamplingRunnerConfig,
) -> OwnerSamplingAuthorization:
    real = config.mode == OwnerRunnerMode.OWNER_REAL_NETWORK
    return OwnerSamplingAuthorization(
        terms_reviewed=config.attestations.terms_reviewed,
        personal_noncommercial_use=config.attestations.personal_noncommercial_use,
        reasonable_rate_and_scale=config.attestations.reasonable_rate_and_scale,
        redistribution_disabled=config.attestations.redistribution_disabled,
        owner_controlled_private_storage=(
            config.attestations.owner_controlled_private_storage if real else False
        ),
        owner_controlled_encryption_keys=(
            config.attestations.owner_controlled_encryption_keys if real else False
        ),
        real_execution_owner_confirmed=(
            config.attestations.real_execution_owner_confirmed if real else False
        ),
    )


def _run_sampling_batch(
    config: OwnerSamplingRunnerConfig,
    *,
    fetcher: Callable[[str], TimedHTTPResponse],
) -> OwnerSamplingRunResult:
    config.validate()
    raw_by_source: dict[str, bytes] = {}
    clocks_by_source: dict[str, SamplingClock] = {}
    research_times: list[datetime] = []

    for contract in SOURCE_CONTRACTS:
        url = build_url(contract)
        timed = fetcher(url)
        research_available_at = datetime.now(UTC)
        observation = validate_source_response(
            contract=contract,
            response=timed.response,
            request_url=url,
            request_started_at=timed.request_started_at,
            response_received_at=timed.response_received_at,
            research_available_at=research_available_at,
        )
        raw_by_source[contract.source_id] = timed.response.body
        clocks_by_source[contract.source_id] = SamplingClock(
            request_started_at=timed.request_started_at,
            response_received_at=timed.response_received_at,
            provider_timestamp_ms=observation.provider_timestamp_ms,
            research_available_at=research_available_at,
        )
        research_times.append(research_available_at)

    committed_at = max(datetime.now(UTC), max(research_times))
    store = _store_from_config(config)
    execution_mode = (
        SamplingExecutionMode.OWNER_CONTROLLED_REAL
        if config.mode == OwnerRunnerMode.OWNER_REAL_NETWORK
        else SamplingExecutionMode.SYNTHETIC_VALIDATION
    )
    manifest = retain_sampling_batch(
        store=store,
        raw_by_source=raw_by_source,
        clocks_by_source=clocks_by_source,
        authorization=_authorization_from_config(config),
        execution_mode=execution_mode,
        requested_retention_days=config.requested_retention_days,
        now=committed_at,
    )
    safe_bytes = safe_manifest_json(manifest).encode("utf-8")
    try:
        _atomic_write(config.safe_manifest_output, safe_bytes, mode=0o600)
    except BaseException as exc:
        try:
            delete_sampling_batch(
                store=store,
                manifest=manifest,
                reason="SAFE_MANIFEST_WRITE_FAILURE",
                now=datetime.now(UTC),
            )
        except BaseException as rollback_exc:
            raise OKXOwnerSamplingRunnerError(
                "Safe manifest write failed and private-batch rollback was incomplete"
            ) from rollback_exc
        raise OKXOwnerSamplingRunnerError(
            "Safe manifest write failed; retained batch was rolled back"
        ) from exc

    compliance = store.assert_compliant(now=committed_at)
    return OwnerSamplingRunResult(
        mode=config.mode.value,
        real_okx_request_performed=(config.mode == OwnerRunnerMode.OWNER_REAL_NETWORK),
        real_raw_sampling_executed=(config.mode == OwnerRunnerMode.OWNER_REAL_NETWORK),
        batch_id=manifest.batch_id,
        source_count=manifest.source_count,
        safe_manifest_output=str(config.safe_manifest_output),
        safe_manifest_byte_count=len(safe_bytes),
        safe_manifest_sha256=_sha256(safe_bytes),
        private_artifact_count=compliance.active_artifact_count,
    )


def execute_real_owner_sampling(config: OwnerSamplingRunnerConfig) -> OwnerSamplingRunResult:
    """Perform one real public-data fetch and owner-controlled private retain operation."""

    if config.mode != OwnerRunnerMode.OWNER_REAL_NETWORK:
        raise OKXOwnerSamplingRunnerError("Real executor requires OWNER_REAL_NETWORK mode")
    return _run_sampling_batch(config, fetcher=fetch_public_response)


def execute_synthetic_owner_sampling_for_validation(
    config: OwnerSamplingRunnerConfig,
    *,
    fetcher: Callable[[str], TimedHTTPResponse],
) -> OwnerSamplingRunResult:
    """Run injected synthetic responses; never call this as evidence of real execution."""

    if config.mode != OwnerRunnerMode.SYNTHETIC_INJECTED:
        raise OKXOwnerSamplingRunnerError(
            "Synthetic validator requires SYNTHETIC_INJECTED mode"
        )
    if fetcher is fetch_public_response:
        raise OKXOwnerSamplingRunnerError(
            "Synthetic validation cannot use the official network fetcher"
        )
    return _run_sampling_batch(config, fetcher=fetcher)


def load_safe_sampling_manifest(path: Path) -> SafeSamplingBatchManifest:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OKXOwnerSamplingRunnerError("Cannot read safe sampling manifest") from exc
    if not isinstance(value, dict):
        raise OKXOwnerSamplingRunnerError("Safe sampling manifest is not an object")
    try:
        sources = tuple(SafeSamplingSourceLease(**source) for source in value["sources"])
        return SafeSamplingBatchManifest(**{**value, "sources": sources})
    except (KeyError, TypeError) as exc:
        raise OKXOwnerSamplingRunnerError("Safe sampling manifest schema is invalid") from exc


def delete_owner_sampling_batch(
    config: OwnerSamplingDeletionConfig,
) -> SafeSamplingBatchDeletionReceipt:
    config.validate()
    manifest = load_safe_sampling_manifest(config.safe_manifest_path)
    store = PrivateRevocableArtifactStore(
        config.private_root,
        repository_root=config.repository_root,
        policy=RetentionPolicy(
            policy_id=manifest.policy_id,
            license_snapshot_id=manifest.license_snapshot_id,
            allowed_purpose=ALLOWED_PURPOSE,
            maximum_retention_days=7,
        ),
        attestation=RetentionAttestation(
            encryption_at_rest=config.attestations.encryption_at_rest,
            owner_only_access=config.attestations.owner_only_access,
            backup_and_sync_excluded=config.attestations.backup_and_sync_excluded,
            public_artifact_upload_disabled=(
                config.attestations.public_artifact_upload_disabled
            ),
        ),
    )
    receipt = delete_sampling_batch(
        store=store,
        manifest=manifest,
        reason=config.reason,
        now=datetime.now(UTC),
    )
    _atomic_write(
        config.safe_deletion_receipt_output,
        (json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n").encode("utf-8"),
        mode=0o600,
    )
    return receipt


def _sha256(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value).hexdigest()
