from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest
from hybrid_trader.replication.artifacts import sha256_file
from hybrid_trader.replication.provenance import ArtifactProvenance, SourceAccessStatus
from hybrid_trader.replication.runner import run_aqr_vintage_audit
from hybrid_trader.replication.verdicts import ReplicationStatus


def _write_factor(path: Path, values: list[float]) -> None:
    pd.DataFrame({"date": [202001, 202002, 202003], "tsmom": values}).to_csv(
        path, index=False
    )


def _immutable_provenance(path: Path, source_id: str) -> ArtifactProvenance:
    return ArtifactProvenance(
        source_id=source_id,
        official_locator=f"https://official.example/{path.name}",
        access_status=SourceAccessStatus.IMMUTABLE_INGESTED,
        sha256=sha256_file(path),
        byte_count=path.stat().st_size,
        retrieved_at=datetime(2026, 7, 18, tzinfo=UTC),
        license_snapshot_id="license-v1",
        immutable_storage_key=f"raw/{source_id}/{path.name}",
    )


def test_local_files_cannot_receive_artifact_pass(tmp_path: Path) -> None:
    original = tmp_path / "original.csv"
    maintained = tmp_path / "maintained.csv"
    output = tmp_path / "verdict.json"
    _write_factor(original, [1.0, -2.0, 3.0])
    _write_factor(maintained, [1.0, -1.0, 3.0])

    verdict = run_aqr_vintage_audit(
        original_path=original,
        maintained_path=maintained,
        output_path=output,
        return_scale="percent",
    )

    assert verdict.status == ReplicationStatus.IMPLEMENTATION_READY
    assert verdict.source_artifact_ids == []
    assert verdict.exactness_class == "UNVERIFIED_LOCAL_FACTOR_AUDIT"


def test_immutable_official_files_receive_artifact_audit_pass(tmp_path: Path) -> None:
    original = tmp_path / "original.csv"
    maintained = tmp_path / "maintained.csv"
    output = tmp_path / "verdict.json"
    _write_factor(original, [1.0, -2.0, 3.0])
    _write_factor(maintained, [1.0, -1.0, 3.0])

    verdict = run_aqr_vintage_audit(
        original_path=original,
        maintained_path=maintained,
        output_path=output,
        return_scale="percent",
        original_provenance=_immutable_provenance(original, "AQR_ORIGINAL"),
        maintained_provenance=_immutable_provenance(maintained, "AQR_MAINTAINED"),
    )

    assert verdict.status == ReplicationStatus.ARTIFACT_AUDIT_PASS
    assert len(verdict.source_artifact_ids) == 2
    assert verdict.metrics["maintained_factor_metrics"]["tsmom"]["count"] == 3


def test_mismatched_checksum_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "factor.csv"
    _write_factor(source, [1.0, 2.0, 3.0])
    provenance = ArtifactProvenance(
        source_id="AQR",
        official_locator="https://official.example/factor.csv",
        access_status=SourceAccessStatus.RAW_ARTIFACT_ACQUIRED,
        sha256="0" * 64,
        byte_count=source.stat().st_size,
        retrieved_at=datetime(2026, 7, 18, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        provenance.verify_local_file(source)


def test_immutable_status_requires_license_and_storage() -> None:
    with pytest.raises(ValueError, match="license_snapshot_id"):
        ArtifactProvenance(
            source_id="AQR",
            official_locator="https://official.example/factor.csv",
            access_status=SourceAccessStatus.IMMUTABLE_INGESTED,
            sha256="1" * 64,
            byte_count=10,
            retrieved_at=datetime(2026, 7, 18, tzinfo=UTC),
        )
