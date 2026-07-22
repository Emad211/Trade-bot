from __future__ import annotations

import hashlib
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.replication.revocable_retention import (
    ALLOWED_PURPOSE,
    PrivateRevocableArtifactStore,
    RetentionAttestation,
    RetentionPolicy,
    RevocableRetentionError,
)

NOW = datetime(2026, 7, 21, 8, 0, tzinfo=UTC)
SOURCE_KEY_HASH = hashlib.sha256(b"official-redacted-source-object").hexdigest()


def _policy() -> RetentionPolicy:
    return RetentionPolicy(
        policy_id="OKX_PRIVATE_REVOCABLE_RAW_V1",
        license_snapshot_id="OKX_HISTORICAL_DATA_TERMS_2026-07-21_V1",
        allowed_purpose=ALLOWED_PURPOSE,
        maximum_retention_days=30,
    )


def _attestation() -> RetentionAttestation:
    return RetentionAttestation(
        encryption_at_rest=True,
        owner_only_access=True,
        backup_and_sync_excluded=True,
        public_artifact_upload_disabled=True,
    )


def _store(tmp_path: Path) -> PrivateRevocableArtifactStore:
    repository = tmp_path / "repo"
    repository.mkdir()
    return PrivateRevocableArtifactStore(
        tmp_path / "private-owner-store",
        repository_root=repository,
        policy=_policy(),
        attestation=_attestation(),
    )


def test_refuses_storage_inside_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    with pytest.raises(RevocableRetentionError, match="outside the repository"):
        PrivateRevocableArtifactStore(
            repository / "raw",
            repository_root=repository,
            policy=_policy(),
            attestation=_attestation(),
        )


def test_refuses_incomplete_owner_attestations(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    incomplete = RetentionAttestation(
        encryption_at_rest=False,
        owner_only_access=True,
        backup_and_sync_excluded=True,
        public_artifact_upload_disabled=True,
    )

    with pytest.raises(RevocableRetentionError, match="encryption_at_rest"):
        PrivateRevocableArtifactStore(
            tmp_path / "private",
            repository_root=repository,
            policy=_policy(),
            attestation=incomplete,
        )


def test_retains_content_addressed_artifact_with_owner_only_modes(tmp_path: Path) -> None:
    store = _store(tmp_path)
    raw = b"bounded-private-raw-artifact"

    lease = store.retain(
        raw,
        source_id="OKX_FUNDING_BTC_USDT_SWAP_2022_03",
        source_object_key_sha256=SOURCE_KEY_HASH,
        requested_retention_days=14,
        now=NOW,
    )

    raw_path = store.raw_dir / f"{lease.artifact_id}.bin"
    lease_path = store.lease_dir / f"{lease.artifact_id}.json"
    assert lease.raw_sha256 == hashlib.sha256(raw).hexdigest()
    assert lease.byte_count == len(raw)
    assert lease.expires_at_utc == (NOW + timedelta(days=14)).isoformat()
    assert lease.redistribution_authorized is False
    assert lease.revocable is True
    assert lease.secure_erase_guaranteed is False
    assert raw_path.read_bytes() == raw
    assert stat.S_IMODE(raw_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(lease_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.root.stat().st_mode) == 0o700
    snapshot = store.assert_compliant(now=NOW + timedelta(days=1))
    assert snapshot.active_artifact_ids == (lease.artifact_id,)


def test_refuses_duplicate_or_previously_deleted_artifact_identity(tmp_path: Path) -> None:
    store = _store(tmp_path)
    raw = b"same-content"
    lease = store.retain(
        raw,
        source_id="OKX_TEST",
        source_object_key_sha256=SOURCE_KEY_HASH,
        requested_retention_days=1,
        now=NOW,
    )

    with pytest.raises(RevocableRetentionError, match="already exists"):
        store.retain(
            raw,
            source_id="OKX_TEST",
            source_object_key_sha256=SOURCE_KEY_HASH,
            requested_retention_days=1,
            now=NOW,
        )

    store.delete(lease.artifact_id, reason="OWNER_REQUEST", now=NOW)
    with pytest.raises(RevocableRetentionError, match="previously deleted"):
        store.retain(
            raw,
            source_id="OKX_TEST",
            source_object_key_sha256=SOURCE_KEY_HASH,
            requested_retention_days=1,
            now=NOW,
        )


def test_delete_removes_raw_and_lease_and_keeps_safe_tombstone(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lease = store.retain(
        b"delete-me",
        source_id="OKX_TEST",
        source_object_key_sha256=SOURCE_KEY_HASH,
        requested_retention_days=7,
        now=NOW,
    )

    receipt = store.delete(
        lease.artifact_id,
        reason="LICENSE_REVOKED",
        now=NOW + timedelta(hours=1),
    )

    assert receipt.integrity_matched_before_delete is True
    assert receipt.raw_exists_after_delete is False
    assert receipt.lease_exists_after_delete is False
    assert receipt.secure_erase_claimed is False
    assert not (store.raw_dir / f"{lease.artifact_id}.bin").exists()
    assert not (store.lease_dir / f"{lease.artifact_id}.json").exists()
    tombstone = store.tombstone_dir / f"{lease.artifact_id}.json"
    assert tombstone.is_file()
    assert stat.S_IMODE(tombstone.stat().st_mode) == 0o600
    assert (
        store.delete(
            lease.artifact_id,
            reason="DUPLICATE_DELETE_REQUEST",
            now=NOW + timedelta(hours=2),
        )
        == receipt
    )


def test_integrity_mismatch_never_blocks_required_deletion(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lease = store.retain(
        b"original",
        source_id="OKX_TEST",
        source_object_key_sha256=SOURCE_KEY_HASH,
        requested_retention_days=7,
        now=NOW,
    )
    raw_path = store.raw_dir / f"{lease.artifact_id}.bin"
    raw_path.write_bytes(b"tampered")
    raw_path.chmod(0o600)

    receipt = store.delete(
        lease.artifact_id,
        reason="INTEGRITY_FAILURE_DELETE_ANYWAY",
        now=NOW + timedelta(hours=1),
    )

    assert receipt.integrity_matched_before_delete is False
    assert receipt.observed_sha256_before_delete == hashlib.sha256(b"tampered").hexdigest()
    assert receipt.raw_exists_after_delete is False
    assert receipt.lease_exists_after_delete is False


def test_purge_due_deletes_only_expired_leases(tmp_path: Path) -> None:
    store = _store(tmp_path)
    expired = store.retain(
        b"expires-first",
        source_id="OKX_TEST_A",
        source_object_key_sha256=SOURCE_KEY_HASH,
        requested_retention_days=1,
        now=NOW,
    )
    active = store.retain(
        b"expires-later",
        source_id="OKX_TEST_B",
        source_object_key_sha256=hashlib.sha256(b"second-source").hexdigest(),
        requested_retention_days=10,
        now=NOW,
    )

    receipts = store.purge_due(now=NOW + timedelta(days=2))

    assert tuple(receipt.artifact_id for receipt in receipts) == (expired.artifact_id,)
    assert not (store.raw_dir / f"{expired.artifact_id}.bin").exists()
    assert (store.raw_dir / f"{active.artifact_id}.bin").is_file()
    snapshot = store.assert_compliant(now=NOW + timedelta(days=2))
    assert snapshot.active_artifact_ids == (active.artifact_id,)


def test_compliance_fails_closed_on_overdue_or_orphaned_records(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lease = store.retain(
        b"overdue",
        source_id="OKX_TEST",
        source_object_key_sha256=SOURCE_KEY_HASH,
        requested_retention_days=1,
        now=NOW,
    )

    overdue = store.compliance_snapshot(now=NOW + timedelta(days=2))
    assert overdue.overdue_artifact_ids == (lease.artifact_id,)
    with pytest.raises(RevocableRetentionError, match="non-compliant"):
        store.assert_compliant(now=NOW + timedelta(days=2))

    lease_path = store.lease_dir / f"{lease.artifact_id}.json"
    lease_path.unlink()
    orphaned = store.compliance_snapshot(now=NOW)
    assert orphaned.orphan_raw_artifact_ids == (lease.artifact_id,)
