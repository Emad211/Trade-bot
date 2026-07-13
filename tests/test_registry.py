from datetime import UTC, datetime
from pathlib import Path

import pytest

from hybrid_trader.registry import (
    ExperimentRecord,
    append_registry_record,
    verify_registry,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def test_registry_retains_null_and_failed_results(tmp_path: Path) -> None:
    path = tmp_path / "registry.jsonl"
    first = ExperimentRecord(
        recorded_at=datetime(2026, 7, 13, 12, tzinfo=UTC),
        status="null",
        plan_sha256=SHA_A,
        experiment_id=SHA_B,
        dataset_sha256=(SHA_C,),
        artifact_sha256={},
        summary={"candidate": False},
        notes="No incremental value",
    )
    first_sha = append_registry_record(path, first)
    second = ExperimentRecord(
        recorded_at=datetime(2026, 7, 13, 13, tzinfo=UTC),
        status="failed",
        plan_sha256=SHA_A,
        dataset_sha256=(SHA_C,),
        artifact_sha256={},
        summary={"stage": "download"},
        previous_record_sha256=first_sha,
    )
    append_registry_record(path, second)
    head, record, count = verify_registry(path)
    assert head is not None
    assert count == 2
    assert record is not None and record.status == "failed"

    raw = path.read_text()
    path.write_text(raw.replace("No incremental value", "selected result"))
    with pytest.raises(ValueError, match=r"Invalid registry|hash chain"):
        verify_registry(path)


def test_completed_registry_record_requires_experiment_id() -> None:
    with pytest.raises(ValueError, match="require experiment_id"):
        ExperimentRecord(
            recorded_at=datetime.now(UTC),
            status="completed",
            plan_sha256=SHA_A,
            dataset_sha256=(SHA_C,),
            artifact_sha256={},
            summary={},
        )


def test_blocked_registry_record_allows_no_dataset(tmp_path: Path) -> None:
    path = tmp_path / "registry.jsonl"
    record = ExperimentRecord(
        recorded_at=datetime(2026, 7, 13, 14, tzinfo=UTC),
        status="blocked",
        plan_sha256=SHA_A,
        dataset_sha256=(),
        artifact_sha256={"blocked.json": SHA_B},
        summary={"stage": "collection"},
        notes="Public endpoint unavailable",
    )
    digest = append_registry_record(path, record)
    head, restored, count = verify_registry(path)
    assert head == digest
    assert count == 1
    assert restored is not None
    assert restored.status == "blocked"
    assert restored.dataset_sha256 == ()


def test_null_registry_record_still_requires_dataset() -> None:
    with pytest.raises(ValueError, match="at least one dataset"):
        ExperimentRecord(
            recorded_at=datetime.now(UTC),
            status="null",
            plan_sha256=SHA_A,
            experiment_id=SHA_B,
            dataset_sha256=(),
            artifact_sha256={},
            summary={},
        )
