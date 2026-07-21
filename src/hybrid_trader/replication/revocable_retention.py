"""Owner-controlled, revocable raw-artifact retention with mandatory deletion receipts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

ARTIFACT_ID_PATTERN = re.compile(r"^sha256-[0-9a-f]{64}$")
HEX_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MAX_PRIVATE_ARTIFACT_BYTES = 20_000_000
MAX_RETENTION_DAYS = 30
ALLOWED_PURPOSE = "PERSONAL_STRATEGY_RESEARCH_ONLY"


class RevocableRetentionError(RuntimeError):
    """Raised when private raw retention violates the frozen owner-only contract."""


@dataclass(frozen=True)
class RetentionAttestation:
    """Owner attestations that cannot be inferred reliably from a filesystem path."""

    encryption_at_rest: bool
    owner_only_access: bool
    backup_and_sync_excluded: bool
    public_artifact_upload_disabled: bool

    def validate(self) -> None:
        missing = [name for name, value in asdict(self).items() if value is not True]
        if missing:
            raise RevocableRetentionError(
                "Private retention attestations are incomplete: " + ", ".join(missing)
            )


@dataclass(frozen=True)
class RetentionPolicy:
    policy_id: str
    license_snapshot_id: str
    allowed_purpose: str = ALLOWED_PURPOSE
    maximum_retention_days: int = MAX_RETENTION_DAYS

    def validate(self) -> None:
        if not self.policy_id.strip():
            raise RevocableRetentionError("Retention policy_id cannot be empty")
        if not self.license_snapshot_id.strip():
            raise RevocableRetentionError("license_snapshot_id cannot be empty")
        if self.allowed_purpose != ALLOWED_PURPOSE:
            raise RevocableRetentionError(f"Unsupported raw-data purpose: {self.allowed_purpose!r}")
        if not 1 <= self.maximum_retention_days <= MAX_RETENTION_DAYS:
            raise RevocableRetentionError("maximum_retention_days must be between 1 and 30")


@dataclass(frozen=True)
class ActiveLease:
    schema_version: str
    artifact_id: str
    source_id: str
    source_object_key_sha256: str
    raw_filename: str
    raw_sha256: str
    byte_count: int
    created_at_utc: str
    expires_at_utc: str
    policy_id: str
    license_snapshot_id: str
    allowed_purpose: str
    maximum_retention_days: int
    requested_retention_days: int
    encryption_at_rest_attested: bool
    owner_only_access_attested: bool
    backup_and_sync_excluded_attested: bool
    public_artifact_upload_disabled_attested: bool
    redistribution_authorized: bool
    revocable: bool
    deletion_required_on_expiry_or_revocation: bool
    secure_erase_guaranteed: bool


@dataclass(frozen=True)
class DeletionReceipt:
    schema_version: str
    artifact_id: str
    source_id: str
    expected_sha256: str
    observed_sha256_before_delete: str
    expected_byte_count: int
    observed_byte_count_before_delete: int
    integrity_matched_before_delete: bool
    delete_reason: str
    deleted_at_utc: str
    raw_existed_before_delete: bool
    lease_existed_before_delete: bool
    raw_exists_after_delete: bool
    lease_exists_after_delete: bool
    secure_erase_claimed: bool
    policy_id: str
    license_snapshot_id: str


@dataclass(frozen=True)
class ComplianceSnapshot:
    active_artifact_count: int
    active_artifact_ids: tuple[str, ...]
    overdue_artifact_ids: tuple[str, ...]
    orphan_raw_artifact_ids: tuple[str, ...]
    orphan_lease_artifact_ids: tuple[str, ...]
    invalid_permission_paths: tuple[str, ...]

    @property
    def compliant(self) -> bool:
        return not (
            self.overdue_artifact_ids
            or self.orphan_raw_artifact_ids
            or self.orphan_lease_artifact_ids
            or self.invalid_permission_paths
        )


def _require_aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise RevocableRetentionError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _iso_utc(value: datetime) -> str:
    return _require_aware_utc(value, field="timestamp").isoformat()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_artifact_id(value: str) -> str:
    if ARTIFACT_ID_PATTERN.fullmatch(value) is None:
        raise RevocableRetentionError(f"Invalid artifact_id: {value!r}")
    return value


def _validate_source_object_hash(value: str) -> str:
    if HEX_SHA256_PATTERN.fullmatch(value) is None:
        raise RevocableRetentionError("source_object_key_sha256 must be a lowercase SHA-256 digest")
    return value


def _is_within(child: Path, parent: Path) -> bool:
    return child == parent or child.is_relative_to(parent)


def _atomic_write(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RevocableRetentionError(f"Cannot read retention record {path.name!r}") from exc
    if not isinstance(value, dict):
        raise RevocableRetentionError(f"Retention record {path.name!r} is not an object")
    return cast(dict[str, Any], value)


class PrivateRevocableArtifactStore:
    """Content-addressed private storage with bounded leases and fail-closed deletion."""

    def __init__(
        self,
        root: str | Path,
        *,
        repository_root: str | Path,
        policy: RetentionPolicy,
        attestation: RetentionAttestation,
    ) -> None:
        policy.validate()
        attestation.validate()
        resolved_root = Path(root).expanduser().resolve(strict=False)
        resolved_repository = Path(repository_root).expanduser().resolve(strict=False)
        if _is_within(resolved_root, resolved_repository):
            raise RevocableRetentionError("Private raw storage must be outside the repository tree")
        if resolved_root.exists() and resolved_root.is_symlink():
            raise RevocableRetentionError("Private raw storage root cannot be a symlink")

        self.root = resolved_root
        self.repository_root = resolved_repository
        self.policy = policy
        self.attestation = attestation
        self.raw_dir = self.root / "raw"
        self.lease_dir = self.root / "leases"
        self.tombstone_dir = self.root / "tombstones"
        for directory in (
            self.root,
            self.raw_dir,
            self.lease_dir,
            self.tombstone_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            if directory.is_symlink():
                raise RevocableRetentionError(
                    f"Retention directory cannot be a symlink: {directory}"
                )
            os.chmod(directory, 0o700)

    def _raw_path(self, artifact_id: str) -> Path:
        return self.raw_dir / f"{_validate_artifact_id(artifact_id)}.bin"

    def _lease_path(self, artifact_id: str) -> Path:
        return self.lease_dir / f"{_validate_artifact_id(artifact_id)}.json"

    def _tombstone_path(self, artifact_id: str) -> Path:
        return self.tombstone_dir / f"{_validate_artifact_id(artifact_id)}.json"

    def retain(
        self,
        raw_bytes: bytes,
        *,
        source_id: str,
        source_object_key_sha256: str,
        requested_retention_days: int,
        now: datetime,
    ) -> ActiveLease:
        """Persist one owner-only raw artifact under a bounded revocable lease."""

        created_at = _require_aware_utc(now, field="now")
        if not source_id.strip():
            raise RevocableRetentionError("source_id cannot be empty")
        _validate_source_object_hash(source_object_key_sha256)
        if not raw_bytes:
            raise RevocableRetentionError("Cannot retain an empty raw artifact")
        if len(raw_bytes) > MAX_PRIVATE_ARTIFACT_BYTES:
            raise RevocableRetentionError(
                f"Raw artifact exceeds the {MAX_PRIVATE_ARTIFACT_BYTES}-byte pilot guard"
            )
        if not 1 <= requested_retention_days <= self.policy.maximum_retention_days:
            raise RevocableRetentionError(
                "requested_retention_days exceeds the frozen retention policy"
            )

        digest = _sha256(raw_bytes)
        artifact_id = f"sha256-{digest}"
        raw_path = self._raw_path(artifact_id)
        lease_path = self._lease_path(artifact_id)
        tombstone_path = self._tombstone_path(artifact_id)
        if raw_path.exists() or lease_path.exists() or tombstone_path.exists():
            raise RevocableRetentionError(
                f"Artifact identity already exists or was previously deleted: {artifact_id}"
            )

        expires_at = created_at + timedelta(days=requested_retention_days)
        lease = ActiveLease(
            schema_version="1.0",
            artifact_id=artifact_id,
            source_id=source_id,
            source_object_key_sha256=source_object_key_sha256,
            raw_filename=raw_path.name,
            raw_sha256=digest,
            byte_count=len(raw_bytes),
            created_at_utc=_iso_utc(created_at),
            expires_at_utc=_iso_utc(expires_at),
            policy_id=self.policy.policy_id,
            license_snapshot_id=self.policy.license_snapshot_id,
            allowed_purpose=self.policy.allowed_purpose,
            maximum_retention_days=self.policy.maximum_retention_days,
            requested_retention_days=requested_retention_days,
            encryption_at_rest_attested=self.attestation.encryption_at_rest,
            owner_only_access_attested=self.attestation.owner_only_access,
            backup_and_sync_excluded_attested=self.attestation.backup_and_sync_excluded,
            public_artifact_upload_disabled_attested=(
                self.attestation.public_artifact_upload_disabled
            ),
            redistribution_authorized=False,
            revocable=True,
            deletion_required_on_expiry_or_revocation=True,
            secure_erase_guaranteed=False,
        )

        _atomic_write(raw_path, raw_bytes, mode=0o600)
        try:
            _atomic_write(lease_path, _json_bytes(asdict(lease)), mode=0o600)
        except BaseException:
            raw_path.unlink(missing_ok=True)
            raise
        self._validate_active_artifact(lease)
        return lease

    def _validate_active_artifact(self, lease: ActiveLease) -> None:
        raw_path = self._raw_path(lease.artifact_id)
        lease_path = self._lease_path(lease.artifact_id)
        if raw_path.is_symlink() or lease_path.is_symlink():
            raise RevocableRetentionError("Retention records cannot be symlinks")
        if not raw_path.is_file() or not lease_path.is_file():
            raise RevocableRetentionError("Active raw artifact and lease must both exist")
        raw_stat = raw_path.stat()
        if raw_stat.st_nlink != 1:
            raise RevocableRetentionError("Private raw artifact cannot have hard links")
        if stat.S_IMODE(raw_stat.st_mode) != 0o600:
            raise RevocableRetentionError("Private raw artifact mode must be 0600")
        if stat.S_IMODE(lease_path.stat().st_mode) != 0o600:
            raise RevocableRetentionError("Private lease mode must be 0600")
        raw = raw_path.read_bytes()
        if len(raw) != lease.byte_count or _sha256(raw) != lease.raw_sha256:
            raise RevocableRetentionError("Private raw artifact integrity check failed")

    def read_lease(self, artifact_id: str) -> ActiveLease:
        record = _load_json_object(self._lease_path(artifact_id))
        try:
            return ActiveLease(**record)
        except TypeError as exc:
            raise RevocableRetentionError("Active lease schema is invalid") from exc

    def delete(
        self,
        artifact_id: str,
        *,
        reason: str,
        now: datetime,
    ) -> DeletionReceipt:
        """Delete raw bytes even when integrity changed, then retain a safe tombstone."""

        deleted_at = _require_aware_utc(now, field="now")
        if not reason.strip():
            raise RevocableRetentionError("Deletion reason cannot be empty")
        raw_path = self._raw_path(artifact_id)
        lease_path = self._lease_path(artifact_id)
        tombstone_path = self._tombstone_path(artifact_id)
        if tombstone_path.exists() and not raw_path.exists() and not lease_path.exists():
            record = _load_json_object(tombstone_path)
            try:
                return DeletionReceipt(**record)
            except TypeError as exc:
                raise RevocableRetentionError("Deletion receipt schema is invalid") from exc

        lease_existed = lease_path.is_file()
        raw_existed = raw_path.is_file()
        if not lease_existed and not raw_existed:
            raise RevocableRetentionError(f"Unknown artifact_id: {artifact_id}")

        expected_sha256 = ""
        expected_byte_count = 0
        source_id = "UNKNOWN"
        policy_id = self.policy.policy_id
        license_snapshot_id = self.policy.license_snapshot_id
        if lease_existed:
            lease_record = _load_json_object(lease_path)
            expected_sha256 = str(lease_record.get("raw_sha256", ""))
            expected_byte_count = int(lease_record.get("byte_count", 0))
            source_id = str(lease_record.get("source_id", "UNKNOWN"))
            policy_id = str(lease_record.get("policy_id", policy_id))
            license_snapshot_id = str(lease_record.get("license_snapshot_id", license_snapshot_id))

        observed_sha256 = ""
        observed_byte_count = 0
        if raw_existed:
            observed = raw_path.read_bytes()
            observed_sha256 = _sha256(observed)
            observed_byte_count = len(observed)

        raw_path.unlink(missing_ok=True)
        lease_path.unlink(missing_ok=True)
        for directory in (self.raw_dir, self.lease_dir):
            descriptor = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

        receipt = DeletionReceipt(
            schema_version="1.0",
            artifact_id=artifact_id,
            source_id=source_id,
            expected_sha256=expected_sha256,
            observed_sha256_before_delete=observed_sha256,
            expected_byte_count=expected_byte_count,
            observed_byte_count_before_delete=observed_byte_count,
            integrity_matched_before_delete=(
                raw_existed
                and expected_sha256 == observed_sha256
                and expected_byte_count == observed_byte_count
            ),
            delete_reason=reason.strip(),
            deleted_at_utc=_iso_utc(deleted_at),
            raw_existed_before_delete=raw_existed,
            lease_existed_before_delete=lease_existed,
            raw_exists_after_delete=raw_path.exists(),
            lease_exists_after_delete=lease_path.exists(),
            secure_erase_claimed=False,
            policy_id=policy_id,
            license_snapshot_id=license_snapshot_id,
        )
        if receipt.raw_exists_after_delete or receipt.lease_exists_after_delete:
            raise RevocableRetentionError("Raw artifact deletion did not complete")
        _atomic_write(tombstone_path, _json_bytes(asdict(receipt)), mode=0o600)
        return receipt

    def purge_due(
        self, *, now: datetime, reason: str = "LEASE_EXPIRED"
    ) -> tuple[DeletionReceipt, ...]:
        """Delete every lease whose expiry is at or before the supplied clock."""

        current = _require_aware_utc(now, field="now")
        receipts: list[DeletionReceipt] = []
        for lease_path in sorted(self.lease_dir.glob("sha256-*.json")):
            record = _load_json_object(lease_path)
            artifact_id = str(record.get("artifact_id", ""))
            expires_text = str(record.get("expires_at_utc", ""))
            try:
                expires_at = datetime.fromisoformat(expires_text).astimezone(UTC)
            except (ValueError, TypeError) as exc:
                raise RevocableRetentionError(f"Invalid lease expiry for {artifact_id!r}") from exc
            if expires_at <= current:
                receipts.append(
                    self.delete(
                        artifact_id,
                        reason=reason,
                        now=current,
                    )
                )
        return tuple(receipts)

    def compliance_snapshot(self, *, now: datetime) -> ComplianceSnapshot:
        current = _require_aware_utc(now, field="now")
        raw_ids = {path.stem for path in self.raw_dir.glob("sha256-*.bin")}
        lease_ids = {path.stem for path in self.lease_dir.glob("sha256-*.json")}
        active_ids = sorted(raw_ids & lease_ids)
        overdue: list[str] = []
        invalid_permissions: list[str] = []

        for artifact_id in active_ids:
            lease = self.read_lease(artifact_id)
            expires_at = datetime.fromisoformat(lease.expires_at_utc).astimezone(UTC)
            if expires_at <= current:
                overdue.append(artifact_id)
            for path in (self._raw_path(artifact_id), self._lease_path(artifact_id)):
                if stat.S_IMODE(path.stat().st_mode) != 0o600:
                    invalid_permissions.append(str(path.relative_to(self.root)))

        for directory in (self.root, self.raw_dir, self.lease_dir, self.tombstone_dir):
            if stat.S_IMODE(directory.stat().st_mode) != 0o700:
                invalid_permissions.append(str(directory.relative_to(self.root.parent)))

        return ComplianceSnapshot(
            active_artifact_count=len(active_ids),
            active_artifact_ids=tuple(active_ids),
            overdue_artifact_ids=tuple(sorted(overdue)),
            orphan_raw_artifact_ids=tuple(sorted(raw_ids - lease_ids)),
            orphan_lease_artifact_ids=tuple(sorted(lease_ids - raw_ids)),
            invalid_permission_paths=tuple(sorted(set(invalid_permissions))),
        )

    def assert_compliant(self, *, now: datetime) -> ComplianceSnapshot:
        snapshot = self.compliance_snapshot(now=now)
        if not snapshot.compliant:
            raise RevocableRetentionError(
                "Private retention store is non-compliant: "
                + json.dumps(asdict(snapshot), sort_keys=True)
            )
        return snapshot
