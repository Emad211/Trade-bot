from __future__ import annotations

import hashlib
import json
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.replication.okx_private_sampling import (
    ALLOWED_SOURCE_IDS,
    MAX_SOURCE_BYTES,
    OKXPrivateSamplingError,
    OwnerSamplingAuthorization,
    SamplingClock,
    SamplingExecutionMode,
    assert_sampling_batch_compliant,
    delete_sampling_batch,
    retain_sampling_batch,
    safe_manifest_json,
)
from hybrid_trader.replication.revocable_retention import (
    ALLOWED_PURPOSE,
    PrivateRevocableArtifactStore,
    RetentionAttestation,
    RetentionPolicy,
    RevocableRetentionError,
)

NOW = datetime(2026, 7, 21, 13, 0, tzinfo=UTC)


def _policy() -> RetentionPolicy:
    return RetentionPolicy(
        policy_id="OKX_LIVE_PRIVATE_SAMPLING_V1",
        license_snapshot_id="OKX_API_AGREEMENT_2026-03-26_REVIEWED_2026-07-21_V1",
        allowed_purpose=ALLOWED_PURPOSE,
        maximum_retention_days=7,
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
    repository.mkdir(parents=True)
    return PrivateRevocableArtifactStore(
        tmp_path / "owner-private-store",
        repository_root=repository,
        policy=_policy(),
        attestation=_attestation(),
    )


def _authorization(*, real: bool = False) -> OwnerSamplingAuthorization:
    return OwnerSamplingAuthorization(
        terms_reviewed=True,
        personal_noncommercial_use=True,
        reasonable_rate_and_scale=True,
        redistribution_disabled=True,
        owner_controlled_private_storage=real,
        owner_controlled_encryption_keys=real,
        real_execution_owner_confirmed=real,
    )


def _raw_by_source() -> dict[str, bytes]:
    return {
        source_id: json.dumps(
            {
                "source": source_id,
                "synthetic_secret_value": f"DO_NOT_PUBLISH_{index}_12345.67",
            },
            sort_keys=True,
        ).encode()
        for index, source_id in enumerate(ALLOWED_SOURCE_IDS)
    }


def _clocks() -> dict[str, SamplingClock]:
    provider_values = [1784638800000, 1784638799000, 1784638801000, 1784638798000]
    return {
        source_id: SamplingClock(
            request_started_at=NOW + timedelta(milliseconds=index * 200),
            response_received_at=NOW + timedelta(milliseconds=index * 200 + 100),
            provider_timestamp_ms=provider_values[index],
            research_available_at=NOW + timedelta(milliseconds=index * 200 + 150),
        )
        for index, source_id in enumerate(ALLOWED_SOURCE_IDS)
    }


def _retain(tmp_path: Path):
    store = _store(tmp_path)
    manifest = retain_sampling_batch(
        store=store,
        raw_by_source=_raw_by_source(),
        clocks_by_source=_clocks(),
        authorization=_authorization(),
        execution_mode=SamplingExecutionMode.SYNTHETIC_VALIDATION,
        requested_retention_days=2,
        now=NOW + timedelta(seconds=2),
    )
    return store, manifest


def test_real_execution_requires_explicit_owner_control() -> None:
    with pytest.raises(OKXPrivateSamplingError, match="owner-controlled execution"):
        _authorization().validate(mode=SamplingExecutionMode.OWNER_CONTROLLED_REAL)
    _authorization(real=True).validate(mode=SamplingExecutionMode.OWNER_CONTROLLED_REAL)
    with pytest.raises(OKXPrivateSamplingError, match="cannot claim real"):
        _authorization(real=True).validate(mode=SamplingExecutionMode.SYNTHETIC_VALIDATION)


def test_requires_exact_four_source_and_clock_sets(tmp_path: Path) -> None:
    store = _store(tmp_path)
    raw = _raw_by_source()
    raw.pop(ALLOWED_SOURCE_IDS[-1])
    with pytest.raises(OKXPrivateSamplingError, match="missing"):
        retain_sampling_batch(
            store=store,
            raw_by_source=raw,
            clocks_by_source=_clocks(),
            authorization=_authorization(),
            execution_mode=SamplingExecutionMode.SYNTHETIC_VALIDATION,
            requested_retention_days=1,
            now=NOW + timedelta(seconds=2),
        )


def test_retains_synthetic_batch_with_owner_only_modes_and_safe_manifest(
    tmp_path: Path,
) -> None:
    store, manifest = _retain(tmp_path)
    assert manifest.source_count == 4
    assert manifest.source_order == ALLOWED_SOURCE_IDS
    assert manifest.synthetic_validation_only is True
    assert manifest.real_raw_sampling_executed is False
    assert manifest.public_manifest_contains_market_values is False
    assert manifest.basis_computation_authorized is False
    assert len({source.artifact_id for source in manifest.sources}) == 4
    assert stat.S_IMODE(store.root.stat().st_mode) == 0o700
    for source in manifest.sources:
        raw_path = store.raw_dir / f"{source.artifact_id}.bin"
        lease_path = store.lease_dir / f"{source.artifact_id}.json"
        assert stat.S_IMODE(raw_path.stat().st_mode) == 0o600
        assert stat.S_IMODE(lease_path.stat().st_mode) == 0o600
        assert source.raw_values_publicly_retained is False
    serialized = safe_manifest_json(manifest)
    assert "DO_NOT_PUBLISH" not in serialized
    assert "synthetic_secret_value" not in serialized
    assert_sampling_batch_compliant(store=store, manifest=manifest, now=NOW + timedelta(hours=1))


def test_nonmonotonic_provider_timestamps_are_preserved(tmp_path: Path) -> None:
    _, manifest = _retain(tmp_path)
    values = [source.provider_timestamp_ms for source in manifest.sources]
    assert values != sorted(values)
    assert manifest.sources[1].provider_timestamp_age_ms_at_response > 0


def test_empty_oversized_and_excessive_retention_are_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    raw = _raw_by_source()
    raw[ALLOWED_SOURCE_IDS[0]] = b""
    with pytest.raises(OKXPrivateSamplingError, match="empty"):
        retain_sampling_batch(
            store=store,
            raw_by_source=raw,
            clocks_by_source=_clocks(),
            authorization=_authorization(),
            execution_mode=SamplingExecutionMode.SYNTHETIC_VALIDATION,
            requested_retention_days=1,
            now=NOW + timedelta(seconds=2),
        )

    raw = _raw_by_source()
    raw[ALLOWED_SOURCE_IDS[0]] = b"x" * (MAX_SOURCE_BYTES + 1)
    with pytest.raises(OKXPrivateSamplingError, match="per-source"):
        retain_sampling_batch(
            store=store,
            raw_by_source=raw,
            clocks_by_source=_clocks(),
            authorization=_authorization(),
            execution_mode=SamplingExecutionMode.SYNTHETIC_VALIDATION,
            requested_retention_days=1,
            now=NOW + timedelta(seconds=2),
        )

    with pytest.raises(OKXPrivateSamplingError, match="between 1 and 7"):
        retain_sampling_batch(
            store=store,
            raw_by_source=_raw_by_source(),
            clocks_by_source=_clocks(),
            authorization=_authorization(),
            execution_mode=SamplingExecutionMode.SYNTHETIC_VALIDATION,
            requested_retention_days=8,
            now=NOW + timedelta(seconds=2),
        )


def test_future_provider_timestamp_guard_fails_closed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    clocks = _clocks()
    source_id = ALLOWED_SOURCE_IDS[0]
    clock = clocks[source_id]
    clocks[source_id] = SamplingClock(
        request_started_at=clock.request_started_at,
        response_received_at=clock.response_received_at,
        provider_timestamp_ms=int(clock.response_received_at.timestamp() * 1000) + 6000,
        research_available_at=clock.research_available_at,
    )
    with pytest.raises(OKXPrivateSamplingError, match="future-skew"):
        retain_sampling_batch(
            store=store,
            raw_by_source=_raw_by_source(),
            clocks_by_source=clocks,
            authorization=_authorization(),
            execution_mode=SamplingExecutionMode.SYNTHETIC_VALIDATION,
            requested_retention_days=1,
            now=NOW + timedelta(seconds=2),
        )


class FailingStore(PrivateRevocableArtifactStore):
    def __init__(self, *args, fail_on: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = 0
        self.fail_on = fail_on

    def retain(self, *args, **kwargs):
        self.calls += 1
        if self.calls == self.fail_on:
            raise RevocableRetentionError("simulated mid-batch failure")
        return super().retain(*args, **kwargs)


def test_mid_batch_failure_rolls_back_all_previous_artifacts(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    store = FailingStore(
        tmp_path / "private",
        repository_root=repository,
        policy=_policy(),
        attestation=_attestation(),
        fail_on=3,
    )
    with pytest.raises(OKXPrivateSamplingError, match="rolled back"):
        retain_sampling_batch(
            store=store,
            raw_by_source=_raw_by_source(),
            clocks_by_source=_clocks(),
            authorization=_authorization(),
            execution_mode=SamplingExecutionMode.SYNTHETIC_VALIDATION,
            requested_retention_days=1,
            now=NOW + timedelta(seconds=2),
        )
    assert not list(store.raw_dir.glob("*.bin"))
    assert not list(store.lease_dir.glob("*.json"))
    assert len(list(store.tombstone_dir.glob("*.json"))) == 2


def test_batch_deletion_removes_all_raw_and_leases_and_keeps_safe_receipts(
    tmp_path: Path,
) -> None:
    store, manifest = _retain(tmp_path)
    receipt = delete_sampling_batch(
        store=store,
        manifest=manifest,
        reason="OWNER_REQUEST",
        now=NOW + timedelta(hours=1),
    )
    assert receipt.source_count == 4
    assert receipt.all_raw_deleted is True
    assert receipt.all_leases_deleted is True
    assert receipt.secure_erase_claimed is False
    assert all(source.integrity_matched_before_delete for source in receipt.sources)
    assert not list(store.raw_dir.glob("*.bin"))
    assert not list(store.lease_dir.glob("*.json"))
    assert len(list(store.tombstone_dir.glob("*.json"))) == 4
    assert store.assert_compliant(now=NOW + timedelta(hours=2)).active_artifact_count == 0


def test_batch_identity_is_deterministic_for_identical_inputs(tmp_path: Path) -> None:
    store_a, manifest_a = _retain(tmp_path / "a")
    store_b, manifest_b = _retain(tmp_path / "b")
    assert manifest_a.batch_id == manifest_b.batch_id
    assert manifest_a.batch_id.startswith("sha256-")
    delete_sampling_batch(
        store=store_a,
        manifest=manifest_a,
        reason="TEST_CLEANUP",
        now=NOW + timedelta(hours=1),
    )
    delete_sampling_batch(
        store=store_b,
        manifest=manifest_b,
        reason="TEST_CLEANUP",
        now=NOW + timedelta(hours=1),
    )


def test_raw_hashes_are_content_addressed_but_values_are_not_public(tmp_path: Path) -> None:
    raw = _raw_by_source()
    _store_instance, manifest = _retain(tmp_path)
    by_source = {source.source_id: source for source in manifest.sources}
    for source_id, raw_bytes in raw.items():
        assert by_source[source_id].raw_sha256 == hashlib.sha256(raw_bytes).hexdigest()
    public = json.loads(safe_manifest_json(manifest))
    assert public["public_raw_artifact_authorized"] is False
    assert public["redistribution_authorized"] is False
    assert public["returns_computation_authorized"] is False
